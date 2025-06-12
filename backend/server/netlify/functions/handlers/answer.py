# backend/server/netlify/functions/handlers/answer.py

from openai import OpenAI
from fastapi import HTTPException
from backend.server.netlify.functions.schemas.schemas import AnswerResponse, QueryResponse
from backend.server.netlify.utils.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def answer_handler(qr: QueryResponse) -> AnswerResponse:
    if not qr.matches:
        return AnswerResponse(answer="Nu am găsit pasaje relevante.")

    snippets = []
    for m in qr.matches:
        # Extract directly from metadata
        url = m.metadata.get("url", "")
        idx = m.metadata.get("chunk_index", None)
        text = m.metadata.get("text", "")

        # Clean up and truncate if desired
        snippet_text = text.replace("\n", " ").strip()
        # e.g. snippet_text = (snippet_text[:200] + "…") if len(snippet_text) > 200 else snippet_text

        snippets.append(f"* (score {m.score:.3f}) “{snippet_text}” — {url}")

    # System/user messages for the LLM
    system_msg = {
        "role": "system",
        "content": (
            "You are an intelligent assistant specialized in Romanian road legislation. "
            "Use ONLY the provided snippets to answer the question, synthesize the information, "
            "and respond in Romanian. If the user’s question is straightforward, answer simply."
        )
    }
    user_msg = {
        "role": "user",
        "content": (
            f"Query: {qr.prompt}\n\n"
            "Here are the retrieved snippets:\n" +
            "\n".join(snippets) +
            "\n\nPlease provide a concise, Romanian-language answer based solely on these."
        )
    }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_msg, user_msg],
            temperature=0.2,
            max_tokens=600
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    answer = resp.choices[0].message.content.strip()
    return AnswerResponse(answer=answer)
