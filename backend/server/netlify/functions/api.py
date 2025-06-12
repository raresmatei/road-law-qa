from mangum import Mangum
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.server.netlify.functions.handlers.admin_ingest import IngestResponse, ingest_legislation_admin
from backend.server.netlify.functions.handlers.chat import chat_handler
from backend.server.netlify.functions.handlers.conversation import get_conversation_handler, list_conversations_handler
from backend.server.netlify.functions.handlers.list_ingested_urls import UrlsResponse, list_ingested_urls_handler

from .handlers.auth    import register_handler
from .handlers.login   import login_handler
from .db.db            import get_db
from ..utils.auth import get_current_admin_user, get_current_user
from .schemas.schemas import ChatRequest, ChatResponse, ConversationHistory, ConversationSummary, IngestRequest, QueryRequest, QueryResponse, AnswerResponse, RegisterRequest, RegisterResponse, LoginRequest, LoginResponse

app = FastAPI(title="Road Legislation QA")

# bearer_scheme = HTTPBearer(
#     scheme_name="Bearer",
#     description="Please paste your token as: Bearer <your_jwt>"
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/admin/ingest_legislation",
    response_model=IngestResponse,
    summary="[ADMIN] Scrape & ingest legislation from a URL",
)
async def ingest_legislation(
    req: IngestRequest,
    user_id: str = Depends(get_current_admin_user),
):
    return await ingest_legislation_admin(req, user_id)

@app.get(
    "/admin/ingested_urls",
    response_model=UrlsResponse,
    summary="[ADMIN] List already-ingested legislation URLs",
)
async def ingested_urls(
    user_id: str = Depends(get_current_admin_user),
):
    return list_ingested_urls_handler(user_id)

@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: Session            = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await chat_handler(req, db, user_id)

@app.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    return register_handler(req, db)

@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, conn=Depends(get_db)):
    try:
        return login_handler(req, conn)
    finally:
        conn.close()
        
@app.get(
    "/conversations",
    response_model=list[ConversationSummary],
    summary="List past conversations for current user"
)
async def list_conversations(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    return await list_conversations_handler(db, user_id)

@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistory,
    summary="Get a single conversation’s full history"
)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    return await get_conversation_handler(conversation_id, db, user_id)

handler = Mangum(app)
