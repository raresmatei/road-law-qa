# src/python_be/server/handlers/chat.py

from typing import List
from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from openai import OpenAI

from backend.server.netlify.functions.db.db import get_db
from backend.server.netlify.functions.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    QueryResponse,
    AnswerResponse,
)
from backend.server.netlify.utils.auth import get_current_user
from ...utils.settings import settings
from ..models.models import Conversation, Message
from .query import query_handler, QueryRequest
from .answer import answer_handler

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def is_road_legislation_question(text: str) -> bool:
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
    # Treat any “LEG…” prefix as LEGISLATION, “CHA…” as CHAT.
    if verdict.startswith("LEG"):
        return True
    if verdict.startswith("CHA"):
        return False

    # If the output is completely unexpected, default to CHAT
    return False


def rewrite_followup_question(
    history: List[dict],
    current_question: str
) -> str:
    """
    Given the last few turns of conversation plus the new (possibly incomplete)
    question, call OpenAI to rewrite it as a standalone, fully-formed question.
    """
    # Build messages for the rewriter
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
    # Append the last N turns from history (up to 4)
    rewriter_messages.extend(history[-4:])
    # Finally, ask the model to rewrite the current question
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
    rewritten = resp.choices[0].message.content.strip()
    return rewritten


async def chat_handler(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> ChatResponse:
    """
    1) If no conversation_id provided, create a new Conversation row.
    2) Insert the new user message (role="user") into the Message table.
    3) Fetch the entire message history for this conversation.
    4) If this is a follow-up question (i.e., more than 1 user turn exists),
       rewrite it into a standalone prompt; else use req.message directly.
    5) Classify (LEGISLATION vs. CHAT):
         • If LEGISLATION → call RAG: query_handler + answer_handler.
         • Otherwise → run a generic OpenAI chat completion on full history.
    6) Insert and commit the assistant’s reply, return ChatResponse.
    """

    # 1) Create a new Conversation if no ID was passed
    conv_id = req.conversation_id
    if conv_id is None:
        new_conv = Conversation(created_at=datetime.utcnow(), user_id=user_id)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = new_conv.id

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

    # Build a list of {"role": ..., "content": ...} for OpenAI
    openai_history: List[dict] = [
        {"role": msg.role, "content": msg.content} for msg in all_messages
    ]

    # 4) If there is at least one prior user-assistant exchange, rewrite the new prompt
    #    so that “follow-up” questions like “but on national roads” become complete.
    user_turns = [m for m in openai_history if m["role"] == "user"]
    if len(user_turns) >= 2:
        # Use the last few turns (assistant + user) as context
        # We’ll take the last 4 messages overall:
        context_for_rewriter = openai_history[-4:]
        rewritten_query = rewrite_followup_question(context_for_rewriter, req.message)
    else:
        rewritten_query = req.message.strip()

    # 5) Classify the (possibly rewritten) query
    if is_road_legislation_question(rewritten_query):
        # → RAG pipeline:
        qr = QueryRequest(query=rewritten_query)
        query_resp: QueryResponse = await query_handler(qr)        # synchronous call
        print('query_resp: ', query_resp)
        answer_resp: AnswerResponse = await answer_handler(query_resp)
        print('answer_resp: ', answer_resp)
        assistant_text = answer_resp.answer
    else:
        # → Generic chat: pass the full history to OpenAI
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

    return ChatResponse(
        conversation_id=conv_id,
        reply=assistant_text,
    )
