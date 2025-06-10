# src/python_be/server/netlify/functions/handlers/conversation.py

from fastapi import HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models.models import Conversation, Message, User
from ..schemas.schemas import ConversationSummary, ConversationHistory, MessageItem

async def list_conversations_handler(
    db: Session,
    user_id: str
) -> List[ConversationSummary]:
    """
    Return a list of { conversation_id, created_at, summary } for this user.
    """
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    stmt = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at.desc())
    convos = db.execute(stmt).scalars().all()

    return [
        ConversationSummary(
            conversation_id=c.id,
            created_at=c.created_at,
            summary=c.summary or ""
        )
        for c in convos
    ]


async def get_conversation_handler(
    conversation_id: int,
    db: Session,
    user_id: str
) -> ConversationHistory:
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    convo = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
        .first()
    )
    if not convo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    stmt_msgs = select(Message).where(Message.conversation_id == convo.id).order_by(Message.created_at)
    db_messages = db.execute(stmt_msgs).scalars().all()

    history_items = [
        MessageItem(
            role=m.role,
            content=m.content,
            created_at=m.created_at
        )
        for m in db_messages
    ]

    return ConversationHistory(
        conversation_id=convo.id,
        messages=history_items
    )
