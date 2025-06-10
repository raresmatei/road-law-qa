# src/python_be/server/netlify/functions/utils/summarizer.py

from openai import OpenAI
from typing import List

from backend.server.netlify.functions.schemas.schemas import MessageItem
from backend.server.netlify.utils.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_conversation_summary(messages: List[MessageItem]) -> str:
    """
    Given the full list of MessageItem, ask OpenAI to produce
    a very short summary (3-5 words) in Romanian.
    """
    # Take the last 20 messages to avoid token bloat
    recent = messages[-20:]
    transcript_lines = []
    for m in recent:
        role = "User" if m.role == "user" else "Assistant"
        # Escape triple quotes
        content = m.content.replace('"""', '\\"""')
        transcript_lines.append(f"{role}: {content}")
    transcript = "\n".join(transcript_lines)

    # Prompt for a very short, title-like summary
    prompt = f"""
Rezumă în doar 3-5 cuvinte principale esența acestei conversații (în limba română):
{transcript}
Returnează strict acele 3-5 cuvinte, fără text suplimentar.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ești un asistent care creează titluri scurte."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=10,  # only a few tokens needed
    )

    summary = response.choices[0].message.content.strip()
    # If the model returns a full sentence, we can truncate to the first line
    # or first 5 words. For safety, split on newline and take first line:
    summary_line = summary.split("\n")[0]
    # Optionally, limit to 5 words:
    words = summary_line.split()
    return " ".join(words[:5])
