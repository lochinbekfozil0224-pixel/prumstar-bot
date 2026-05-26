"""
Mini App uchun ochiq API (har biri initData bilan himoyalangan).
"""
import json
from fastapi import APIRouter, Depends, Body
from sqlalchemy import select, desc

import config
from auth import get_current_user
from db import (
    SessionLocal, User, PremiumPlan, Gift, Order, is_admin, get_setting,
)

router = APIRouter(prefix="/api")


def media_obj(s_val):
    if not s_val:
        return {}
    try:
        return json.loads(s_val)
    except Exception:
        return {}


async def upsert_user(s, u: dict) -> User:
    user = await s.get(User, u["id"])
    name = " ".join(x for x in [u.get("first_name"), u.get("last_name")] if x)
    if not user:
        user = User(id=u["id"], username=u.get("username"), full_name=name,
                    photo_url=u.get("photo_url"), lang=(u.get("language_code") or "uz")[:2])
        if user.lang not in ("uz", "ru", "en", "kk", "uz_cyrl"):
            user.lang = "uz"
        s.add(user)
    else:
        user.username = u.get("username")
        user.full_name = name
        if u.get("photo_url"):
            user.photo_url = u.get("photo_url")
    return user


@router.get("/config")
async def get_config(u: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        user = await upsert_user(s, u)
        await s.commit()
        per_star = float(await get_setting(s, "per_star", "224"))
        plans = (await s.execute(select(PremiumPlan).where(PremiumPlan.active == True).order_by(PremiumPlan.sort))).scalars().all()
        media = {k: media_obj(await get_setting(s, f"media_{k}")) for k in ("stars", "premium", "gifts", "ref")}
        admin = await is_admin(s, u["id"])
        return {
            "per_star": per_star,
            "premium": [{"id": p.id, "months": p.months, "price": p.price,
                         "discount": p.discount, "admin_only": p.admin_only} for p in plans],
            "media": media,
            "channel": config.CHANNEL_USERNAME.lstrip("@"),
            "help": config.HELP_USERNAME.lstrip("@"),
            "bot_username": config.BOT_USERNAME,
            "is_admin": admin,
            "lang": user.lang,
        }


@router.get("/gifts")
async def get_gifts(u: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        gifts = (await s.execute(select(Gift).where(Gift.active == True).order_by(Gift.sort, Gift.id))).scalars().all()
        return [{"id": g.id, "name": g.name, "emoji": g.emoji, "price": g.price,
                 "rare": g.rare, "media": {"src": g.media_url, "type": g.media_type} if g.media_url else {}}
                for g in gifts]


@router.get("/me")
async def get_me(u: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        user = await upsert_user(s, u)
        await s.commit()
        return {"id": user.id, "username": user.username, "name": user.full_name,
                "photo": user.photo_url, "balance": user.balance, "lang": user.lang}


@router.post("/lang")
async def set_lang(lang: str = Body(..., embed=True), u: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        user = await s.get(User, u["id"])
        if user:
            user.lang = lang
            await s.commit()
    return {"ok": True}


@router.get("/history")
async def get_history(u: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        rows = (await s.execute(select(Order).where(Order.user_id == u["id"]).order_by(desc(Order.created_at)).limit(50))).scalars().all()
        return [{"id": o.id, "kind": o.kind, "title": o.title, "amount": o.amount,
                 "status": o.status, "date": o.created_at.strftime("%d %b %Y, %H:%M") if o.created_at else ""}
                for o in rows]


@router.get("/rating")
async def get_rating(period: str = "all", u: dict = Depends(get_current_user)):
    col = {"all": User.stars_earned, "month": User.stars_month, "week": User.stars_week}.get(period, User.stars_earned)
    async with SessionLocal() as s:
        rows = (await s.execute(select(User).where(col > 0).order_by(desc(col)).limit(50))).scalars().all()
        out = []
        for i, r in enumerate(rows):
            stars = {"all": r.stars_earned, "month": r.stars_month, "week": r.stars_week}.get(period, r.stars_earned)
            out.append({"rank": i + 1, "name": r.full_name or (r.username or "User"),
                        "stars": stars, "uzs": r.spent_uzs})
        return out


@router.get("/referral")
async def get_referral(u: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        user = await s.get(User, u["id"])
        friends = (await s.execute(select(User).where(User.referred_by == u["id"]).limit(50))).scalars().all()
        return {
            "available": user.ref_stars if user else 0,
            "count": user.ref_count if user else 0,
            "link": f"https://t.me/{config.BOT_USERNAME}?start=ref_{u['id']}",
            "friends": [{"name": f.full_name or (f.username or "User"), "username": f.username} for f in friends],
        }
