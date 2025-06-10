# src/python_be/server/models/models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    def __repr__(self):
        return f"<User id={self.id!r} username={self.username!r}>"

class Conversation(Base):
    __tablename__ = "conversations"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, index=True)            # from your auth system
    created_at= Column(DateTime, default=datetime.utcnow)
    summary    = Column(Text, nullable=True, default="")

    messages  = relationship("Message", back_populates="conversation", cascade="all, delete")

class Message(Base):
    __tablename__   = "messages"
    id              = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role            = Column(String, nullable=False)   # "user" or "assistant"
    content         = Column(Text, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    conversation    = relationship("Conversation", back_populates="messages")