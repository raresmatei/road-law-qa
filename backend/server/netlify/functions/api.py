from mangum import Mangum
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.server.netlify.functions.handlers.chat import chat_handler
from backend.server.netlify.functions.handlers.conversation import get_conversation_handler, list_conversations_handler 

from .handlers.query   import query_handler
from .handlers.answer  import answer_handler
from .handlers.auth    import register_handler
from .handlers.login   import login_handler
from .db.db            import get_db
from ..utils.auth import get_current_user
from .schemas.schemas import ChatRequest, ChatResponse, ConversationHistory, ConversationSummary, QueryRequest, QueryResponse, AnswerResponse, RegisterRequest, RegisterResponse, LoginRequest, LoginResponse

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
    "/query",
    response_model=QueryResponse,
    summary="Semantic query (protected)",
)
async def query_request(
    query: QueryRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Only logged-in users (valid JWT Bearer token) can reach this.
    `user_id` is available if you ever need it inside your handler.
    """
    return await query_handler(query)

@app.post(
    "/answer",
    response_model=AnswerResponse,
    summary="Generate chat-style answer (protected)",
)
async def answer_from_matches(
    qr: QueryResponse,
    user_id: str = Depends(get_current_user),
):
    return await answer_handler(qr)

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
