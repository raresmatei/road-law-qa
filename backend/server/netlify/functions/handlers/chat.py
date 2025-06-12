# src/python_be/server/handlers/chat.py

from typing import List
from datetime import datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from openai import OpenAI

from backend.server.netlify.functions.db.db import get_db
from backend.server.netlify.functions.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    QueryResponse,
    AnswerResponse,
    MessageItem,
)
from backend.server.netlify.utils.auth import get_current_user
from backend.server.netlify.utils.summarizer import generate_conversation_summary
from ...utils.settings import settings
from ..models.models import Conversation, Message, User
from .query import query_handler, QueryRequest
from .answer import answer_handler

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def is_road_legislation_question(text: str) -> bool:
    print('in fct is_road_legislation_question....')
    """
    Ask a lightweight OpenAI classifier whether `text` is about road legislation.
    Returns True if the LLM says “LEGISLATION”, False if “CHAT”.
    """
    prompt = (
        "You are a classifier. Decide whether the following user message\n"
        "should be routed to a “road-legislation QA” pipeline or treated as a general chat.\n"
        "IMPORTANT: respond with exactly ONE of these two UPPERCASE words and nothing else: "
        "\"LEGISLATION\" or \"CHAT\". Do not abbreviate.\n\n"
        "User message:\n"
        f"\"\"\"\n{text.strip()}\n\"\"\"\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a simple classifier."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=1,
    )
    verdict = resp.choices[0].message.content.strip().upper()
    if verdict.startswith("LEG"):
        return True
    if verdict.startswith("CHA"):
        return False
    return False  # default to CHAT if unexpected


def rewrite_followup_question(
    history: List[dict],
    current_question: str
) -> str:
    """
    Given the last few turns of conversation plus the new (possibly incomplete)
    question, call OpenAI to rewrite it as a standalone, fully-formed question.
    """
    rewriter_messages = [
        {
            "role": "system",
            "content": (
                "You are a question rewriting assistant. "
                "Given a short follow-up user query and the preceding conversation, "
                "output a single, clear, standalone question in Romanian."
            ),
        }
    ]
    # Append up to the last 4 turns
    rewriter_messages.extend(history[-4:])
    # Ask model to rewrite current question
    rewriter_messages.append(
        {
            "role": "user",
            "content": (
                f"Rewrite the following user query so that it is complete and self-contained:\n"
                f"\"{current_question.strip()}\""
            ),
        }
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=rewriter_messages,
        temperature=0.0,
        max_tokens=64,
    )
    return resp.choices[0].message.content.strip()


async def chat_handler(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> ChatResponse:
    """
    1) If no conversation_id provided, create a new Conversation row.
    2) Insert the new user message (role="user") into the Message table.
    3) Fetch the entire message history for this conversation.
    4) If this is a follow-up question (>=2 user turns exist), rewrite it.
    5) Classify (LEGISLATION vs. CHAT):
         • If LEGISLATION → call RAG: query_handler + answer_handler.
         • Otherwise → run a generic OpenAI chat completion on full history.
    6) Insert assistant’s reply.
    7) Generate a short summary of the updated conversation and store it in Conversation.summary.
    8) Return ChatResponse.
    """

    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    # 1) Create a new Conversation if no ID was passed
    conv_id = req.conversation_id
    if conv_id is None:
        new_conv = Conversation(created_at=datetime.utcnow(), user_id=user.id, summary="")
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = new_conv.id
    else:
        convo = db.query(Conversation).filter(
            Conversation.id == conv_id,
            Conversation.user_id == user.id,
        ).first()
        if convo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    # 2) Insert the new user message into the DB
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=req.message.strip(),
        created_at=datetime.utcnow(),
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3) Fetch the full history (ordered by Message.id ascending)
    stmt = select(Message).where(Message.conversation_id == conv_id).order_by(Message.id)
    all_messages = db.execute(stmt).scalars().all()

    openai_history: List[dict] = [
        {"role": msg.role, "content": msg.content} for msg in all_messages
    ]

    # 4) Rewrite follow-up if needed
    user_turns = [m for m in openai_history if m["role"] == "user"]
    if len(user_turns) >= 2:
        context_for_rewriter = openai_history[-4:]
        rewritten_query = rewrite_followup_question(context_for_rewriter, req.message)
    else:
        rewritten_query = req.message.strip()

    # 5) Classify and generate assistant reply
    if is_road_legislation_question(rewritten_query):
        print('road-legislation-question......')
        qr = QueryRequest(query=rewritten_query)
        query_resp: QueryResponse = await query_handler(qr)
        answer_resp: AnswerResponse = await answer_handler(query_resp)
        assistant_text = answer_resp.answer
    else:
        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_history,
            temperature=0.7,
            max_tokens=256,
        )
        assistant_text = chat_completion.choices[0].message.content.strip()

    # 6) Persist the assistant’s reply
    assistant_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=assistant_text,
        created_at=datetime.utcnow(),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    # 7) Generate and store conversation summary
    stmt2 = select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at)
    updated_messages = db.execute(stmt2).scalars().all()

    history_items: List[MessageItem] = [
        MessageItem(role=m.role, content=m.content, created_at=m.created_at)
        for m in updated_messages
    ]
    summary_text = await generate_conversation_summary(history_items)

    convo_obj = db.query(Conversation).filter(Conversation.id == conv_id).first()
    convo_obj.summary = summary_text
    db.commit()

    # 8) Return response
    return ChatResponse(
        conversation_id=conv_id,
        reply=assistant_text,
    )
