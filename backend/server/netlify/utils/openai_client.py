# src/python_be/server/openai_client.py

import os
from openai import OpenAI
from openai import RateLimitError, OpenAIError
from .settings import settings

# Initialize the async client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY)

async def embed_text(text: str) -> list[float]:
    """
    Returns the embedding vector for the given text.
    """
    try:
        resp = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=[text]
        )
        # resp.data is a list of Embedding objects; grab the first one's .embedding field
        return resp.data[0].embedding
    except RateLimitError as e:
        # bubble up or wrap in your own exception
        raise
    except OpenAIError as e:
        # catch other OpenAI API errors
        raise

async def chat_completion(messages: list[dict]) -> str:
    """
    Sends a chat-completion request and returns the assistant's reply.
    messages should be a list of {"role": ..., "content": ...} dicts.
    """
    try:
        resp = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages
        )
        # resp.choices is a list of ChatChoice; each has a .message
        return resp.choices[0].message.content
    except RateLimitError as e:
        raise
    except OpenAIError as e:
        raise
