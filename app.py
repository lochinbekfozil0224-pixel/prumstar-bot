"""
PRUM STAR — FastAPI web service (Railway).
Bitta joyda: Telegram bot (webhook) + Mini App API + Admin API + media fayllar.
Ishga tushirish: uvicorn app:app --host 0.0.0.0 --port $PORT
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aiogram.types import Update

import config
from db import init_db, seed_defaults
from bot import bot, dp
import api
import admin_api

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("prumstar")

WEBHOOK_PATH = f"/webhook/{config.BOT_TOKEN}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_defaults()
    os.makedirs(config.MEDIA_DIR, exist_ok=True)
    if config.PUBLIC_URL:
        try:
            await bot.set_webhook(config.PUBLIC_URL + WEBHOOK_PATH, drop_pending_updates=True)
            log.info("Webhook o'rnatildi: %s%s", config.PUBLIC_URL, WEBHOOK_PATH)
        except Exception as e:
            log.error("Webhook xatosi: %s", e)
    else:
        log.warning("PUBLIC_URL yo'q — bot webhook o'rnatilmadi. Railway domenini PUBLIC_URL ga yozing.")
    yield
    try:
        await bot.delete_webhook()
        await bot.session.close()
    except Exception:
        pass


app = FastAPI(lifespan=lifespan, title="PRUM STAR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Mini App Vercel'da, initData bilan himoyalangan
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(admin_api.router)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"app": "PRUM STAR", "ok": True}


# media fayllarni xizmat qilish (rasmlar/animatsiyalar)
os.makedirs(config.MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")
