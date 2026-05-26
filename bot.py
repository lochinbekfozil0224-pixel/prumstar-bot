"""
Bot — handlerlar va dispatcher. Webhook orqali app.py ishlatadi (polling yo'q).
"""
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery

import config
import texts as T
from db import SessionLocal, User
from helpers import is_subscribed, subscribe_kb, open_app_kb, fill

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def get_or_create_user(m: Message, referred_by=None) -> User:
    async with SessionLocal() as s:
        user = await s.get(User, m.from_user.id)
        if not user:
            lang = (m.from_user.language_code or "uz")[:2]
            if lang not in ("uz", "ru", "en"):
                lang = "uz"
            user = User(id=m.from_user.id, username=m.from_user.username,
                        full_name=m.from_user.full_name, lang=lang)
            if referred_by and referred_by != m.from_user.id:
                user.referred_by = referred_by
                ref = await s.get(User, referred_by)
                if ref:
                    ref.ref_count = (ref.ref_count or 0) + 1
            s.add(user)
        else:
            user.username = m.from_user.username
            user.full_name = m.from_user.full_name
        await s.commit()
        await s.refresh(user)
        return user


async def show_welcome(m: Message, lang: str):
    await m.answer(fill(T.t(T.WELCOME, lang)), reply_markup=open_app_kb(fill(T.t(T.OPEN_APP_BTN, lang))))


async def show_subscribe(m: Message, lang: str):
    kb = subscribe_kb(lang, T.t(T.SUBSCRIBE_BTN, lang), T.t(T.CHECK_BTN, lang))
    await m.answer(fill(T.t(T.SUBSCRIBE, lang)), reply_markup=kb)


@dp.message(CommandStart())
async def cmd_start(m: Message, command: CommandObject):
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        try:
            referred_by = int(command.args[4:])
        except ValueError:
            referred_by = None
    user = await get_or_create_user(m, referred_by)
    if await is_subscribed(bot, m.from_user.id):
        async with SessionLocal() as s:
            u = await s.get(User, m.from_user.id)
            u.is_subscribed = True
            await s.commit()
        await show_welcome(m, user.lang)
    else:
        await show_subscribe(m, user.lang)


@dp.callback_query(F.data == "check_sub")
async def cb_check(c: CallbackQuery):
    async with SessionLocal() as s:
        user = await s.get(User, c.from_user.id)
        lang = user.lang if user else "uz"
    if await is_subscribed(bot, c.from_user.id):
        async with SessionLocal() as s:
            u = await s.get(User, c.from_user.id)
            if u:
                u.is_subscribed = True
                await s.commit()
        await c.message.delete()
        await show_welcome(c.message, lang)
    else:
        await c.answer(T.t(T.NOT_SUBSCRIBED_YET, lang), show_alert=True)
