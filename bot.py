import os
import random
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
APP_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
if APP_URL and not APP_URL.startswith("http"):
    APP_URL = f"https://{APP_URL}"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_COLLECTIONS = {}

GIFTS_POOL = [
    {"name": "Pudgy Dog", "icon": "🐕", "rarity": "Легендарный"},
    {"name": "Heart Locket", "icon": "💖", "rarity": "Легендарный"},
    {"name": "Durov's Cap", "icon": "🧢", "rarity": "Редкий"},
    {"name": "Rose", "icon": "🌹", "rarity": "Редкий"},
    {"name": "Plush Pepe", "icon": "🐸", "rarity": "Обычный"},
    {"name": "Snowman", "icon": "☃️", "rarity": "Обычный"},
]

class CaseRequest(BaseModel):
    init_data: str

@app.get("/")
async def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "Файл интерфейса index.html не найден на сервере"}

@app.post("/api/open-case")
async def api_open_case(payload: CaseRequest):
    user_id = 999999  
    weights = [5, 10, 20, 25, 20, 20]
    reward = random.choices(GIFTS_POOL, weights=weights, k=1)[0]
    
    if user_id not in USER_COLLECTIONS:
        USER_COLLECTIONS[user_id] = []
    
    USER_COLLECTIONS[user_id].append(reward)
    return reward

@app.get("/api/collection")
async def api_get_collection(init_data: str = ""):
    user_id = 999999
    return USER_COLLECTIONS.get(user_id, [])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Добро пожаловать в проект Darikum.\n"
        "Нажми на кнопку ниже, чтобы запустить приложение и открыть свой первый кейс!",
    )

@app.on_event("startup")
async def on_startup():
    if not BOT_TOKEN:
        logger.error("Переменная окружения BOT_TOKEN отсутствует!")
        return

    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    
    await telegram_app.initialize()
    await telegram_app.start()
    if telegram_app.updater:
        await telegram_app.updater.start_polling()
        
    logger.info("Бот Darikum и веб-сервер успешно запущены!")
