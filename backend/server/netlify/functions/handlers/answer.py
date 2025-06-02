from openai import OpenAI

from backend.server.netlify.functions.schemas.schemas import AnswerResponse, QueryResponse
from ...utils.settings import settings
import json
import os

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def answer_handler(qr: QueryResponse) -> AnswerResponse:
    if not qr.matches:
        return {"answer": "Nu am găsit pasaje relevante."}

    # Build snippet list
    snippets = []
    for m in qr.matches:
        url = m.metadata.get("url", "")
        idx = m.metadata.get("chunk_index")
        name = m.metadata.get("name")
        snippet_text = f"(vezi {url} chunk {idx})"
        
        try:
            with open(f"./backend/scrape_api/output/{name}.json", encoding="utf-8") as f:
                chunks = json.load(f)
            for c in chunks:
                if c.get("chunk_index") == idx:
                    print('idx: ', idx)
                    snippet_text = c.get("text", snippet_text)
                    print('snippet_text: ', snippet_text)
                    break
        except FileNotFoundError:
            print('file not found')
            pass

        # truncate
        # print('snipet text: ', snippet_text)
        s = snippet_text.replace("\n", " ").strip()
        # if len(s) > 200:
        #     s = s[:200].rstrip() + "…"
        snippets.append(f"* (score {m.score:.3f}) “{s}” — {url}")
                
    # compose messages
    system = {
        "role": "system",
        "content": (
            "as an intelligentint assistant," 
            "answer only using the received information in the previous message" 
            "answer in romanian and synthetise the retrieved informatoion, give explanations if needed" 
            "if question is starightforward, answer simply to it, without giving too many options to confuse the user"
            "for example if the user asks a general question like what is the speed limt, offer more options depinding on type of road and so on"
        )
    }
    user = {
        "role": "user",
        "content": (
            f"Here's the user query: ${qr.prompt} and the retrieved information from RAG:\n"
            + "\n".join(snippets)
            # + "\n\nTe rog dă-mi o sinteză a ceea ce spun aceste legi pe subiect, iar daca intrebarea este una simpla de exemple limite de viteza/tonaj raspnude simplu si al obiect"
        ),
    }

    # call the new client
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[user, system],
        temperature=0.2,
        max_tokens=600
    )

    return AnswerResponse(answer =  resp.choices[0].message.content)