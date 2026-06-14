"""
conda activate service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import io
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tts_router, user_router, align_router
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI(title="TTS 服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tts_router)
app.include_router(user_router)
app.include_router(align_router)

@app.get("/")
async def root():
    return {"message": "TTS 服务运行中", "status": "ok"}