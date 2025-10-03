from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import users, chat_rooms, messages, attachments

load_dotenv()

app = FastAPI(title="Chat API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(users.router)
app.include_router(chat_rooms.router)
app.include_router(messages.router)
app.include_router(attachments.router)

@app.get("/")
async def root():
    return {"message": "Chat API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
