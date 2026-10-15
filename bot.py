import os
import random
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

app = FastAPI()

# Разрешаем CORS для связи с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище коллекций пользователей в оперативной памяти
USER_COLLECTIONS = {}

# Список доступных наград
GIFTS_POOL = [
    {"name": "Pudgy Dog", "icon": "🐕", "rarity": "Легендарный", "base_stars": 500, "base_ton": 12.5},
    {"name": "Heart Locket", "icon": "💖", "rarity": "Легендарный", "base_stars": 350, "base_ton": 6.8},
    {"name": "Durov's Cap", "icon": "🧢", "rarity": "Редкий", "base_stars": 250, "base_ton": 4.5},
    {"name": "Rose", "icon": "🌹", "rarity": "Редкий", "base_stars": 150, "base_ton": 3.1},
    {"name": "Snowman", "icon": "☃️", "rarity": "Редкий", "base_stars": 80, "base_ton": 1.8},
    {"name": "Plush Pepe", "icon": "🐸", "rarity": "Обычный", "base_stars": 100, "base_ton": 1.2},
]

class CaseRequest(BaseModel):
    init_data: str

def get_dynamic_price(base_price: float) -> float:
    """Симулирует автоматическое отслеживание рыночной цены с колебаниями курса в 5%."""
    fluctuation = random.uniform(-0.05, 0.05)
    return round(base_price * (1 + fluctuation), 2)

def apply_anti_profit_tax(price_ton: float) -> float:
    """Урезает выплату для отправителя на 40%, чтобы никто не уходил в плюс."""
    tax_rate = 0.40 
    return round(price_ton * (1 - tax_rate), 2)

@app.get("/")
async def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "Файл index.html отсутствует"}

@app.post("/api/open-case")
async def api_open_case(payload: CaseRequest):
    user_id = 999999  
    
    # КРАЙНЕ МАЛЕНЬКИЙ ШАНС ВЫБИТЬ (Легендарные: ~1.5%, Редкие: ~8.5%, Обычные: ~90%)
    drop_weights = [0.0075, 0.0075, 0.0283, 0.0283, 0.0284, 0.90]
    
    reward_item = random.choices(GIFTS_POOL, weights=drop_weights, k=1)[0].copy()
    
    current_market_ton = get_dynamic_price(reward_item["base_ton"])
    sender_final_value = apply_anti_profit_tax(current_market_ton)
    
    reward_item["ton"] = f"{current_market_ton} TON"
    reward_item["star_count"] = reward_item["base_stars"]
    reward_item["sender_payout"] = f"{sender_final_value} TON"
    
    if user_id not in USER_COLLECTIONS:
        USER_COLLECTIONS[user_id] = []
        
    USER_COLLECTIONS[user_id].append(reward_item)
    return reward_item

@app.get("/api/collection")
async def api_get_collection(init_data: str = ""):
    user_id = 999999
    collection = USER_COLLECTIONS.get(user_id, [])
    
    for item in collection:
        item["ton"] = f"{get_dynamic_price(item['base_ton'])} TON"
    
    return collection

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в проект Darikum!\n"
        "Нажмите на кнопку ниже, чтобы запустить приложение.",
    )

@app.on_event("startup")
async def on_startup():
    if not BOT_TOKEN:
        logger.error("Переменная BOT_TOKEN не найдена.")
        return

    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    
    await telegram_app.initialize()
    await telegram_app.start()
    if telegram_app.updater:
        await telegram_app.updater.start_polling()
        
    logger.info("Сервер Darikum запущен!")
