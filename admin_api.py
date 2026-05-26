"""
Admin panel API — faqat adminlar (super admin 8135915671 + qo'shilganlar).
Rasm/animatsiya yuklash, narx, gift, admin boshqarish.
"""
import os
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body

import config
from auth import get_current_user
from db import (
    SessionLocal, User, Admin, PremiumPlan, Gift, is_admin, set_setting, get_setting,
)
from sqlalchemy import select

router = APIRouter(prefix="/api/admin")


async def require_admin(u: dict = Depends(get_current_user)) -> dict:
    async with SessionLocal() as s:
        if not await is_admin(s, u["id"]):
            raise HTTPException(403, "Siz admin emassiz")
    return u


def detect_type(filename: str) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext == "json":
        return "lottie"
    if ext in ("mp4", "webm", "mov"):
        return "mp4"
    return "img"  # gif/png/jpg/webp


async def save_file(file: UploadFile) -> tuple[str, str]:
    """Faylni MEDIA_DIR ga saqlaydi, (url, type) qaytaradi."""
    os.makedirs(config.MEDIA_DIR, exist_ok=True)
    ext = (file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin").lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(config.MEDIA_DIR, name)
    data = await file.read()
    with open(path, "wb") as f:
        f.write(data)
    url = f"{config.PUBLIC_URL}/media/{name}"
    return url, detect_type(file.filename or name)


# ---------- 1 STAR NARXI ----------
@router.post("/per_star")
async def set_per_star(value: float = Body(..., embed=True), u=Depends(require_admin)):
    async with SessionLocal() as s:
        await set_setting(s, "per_star", str(value))
        await s.commit()
    return {"ok": True, "per_star": value}


# ---------- KARTA MEDIASI (stars/premium/gifts/ref) ----------
@router.post("/media")
async def upload_card_media(slot: str = Form(...), file: UploadFile = File(...), u=Depends(require_admin)):
    if slot not in ("stars", "premium", "gifts", "ref"):
        raise HTTPException(400, "slot noto'g'ri")
    url, mtype = await save_file(file)
    async with SessionLocal() as s:
        await set_setting(s, f"media_{slot}", json.dumps({"src": url, "type": mtype}))
        await s.commit()
    return {"ok": True, "src": url, "type": mtype}


# ---------- PREMIUM REJALAR ----------
@router.get("/premium")
async def list_premium(u=Depends(require_admin)):
    async with SessionLocal() as s:
        rows = (await s.execute(select(PremiumPlan).order_by(PremiumPlan.sort))).scalars().all()
        return [{"id": p.id, "months": p.months, "price": p.price, "discount": p.discount,
                 "admin_only": p.admin_only, "active": p.active} for p in rows]


@router.post("/premium")
async def upsert_premium(data: dict = Body(...), u=Depends(require_admin)):
    async with SessionLocal() as s:
        if data.get("id"):
            p = await s.get(PremiumPlan, data["id"])
            if not p:
                raise HTTPException(404, "topilmadi")
        else:
            p = PremiumPlan(months=data.get("months", 1), price=0)
            s.add(p)
        p.months = data.get("months", p.months)
        p.price = data.get("price", p.price)
        p.discount = data.get("discount", p.discount)
        p.admin_only = data.get("admin_only", p.admin_only)
        await s.commit()
        await s.refresh(p)
        return {"ok": True, "id": p.id}


@router.delete("/premium/{pid}")
async def delete_premium(pid: int, u=Depends(require_admin)):
    async with SessionLocal() as s:
        p = await s.get(PremiumPlan, pid)
        if p:
            p.active = False
            await s.commit()
    return {"ok": True}


# ---------- GIFT lar ----------
@router.get("/gifts")
async def list_gifts(u=Depends(require_admin)):
    async with SessionLocal() as s:
        rows = (await s.execute(select(Gift).order_by(Gift.sort, Gift.id))).scalars().all()
        return [{"id": g.id, "name": g.name, "emoji": g.emoji, "price": g.price, "rare": g.rare,
                 "active": g.active, "media": {"src": g.media_url, "type": g.media_type} if g.media_url else {}}
                for g in rows]


@router.post("/gift")
async def add_gift(name: str = Form(...), price: float = Form(...), rare: bool = Form(False),
                   emoji: str = Form("🎁"), file: UploadFile = File(None), u=Depends(require_admin)):
    media_url, media_type = (None, None)
    if file is not None:
        media_url, media_type = await save_file(file)
    async with SessionLocal() as s:
        g = Gift(name=name, price=price, rare=rare, emoji=emoji,
                 media_url=media_url, media_type=media_type, sort=999)
        s.add(g)
        await s.commit()
        await s.refresh(g)
        return {"ok": True, "id": g.id}


@router.post("/gift/{gid}")
async def edit_gift(gid: int, name: str = Form(None), price: float = Form(None), rare: bool = Form(None),
                    emoji: str = Form(None), file: UploadFile = File(None), u=Depends(require_admin)):
    async with SessionLocal() as s:
        g = await s.get(Gift, gid)
        if not g:
            raise HTTPException(404, "topilmadi")
        if name is not None: g.name = name
        if price is not None: g.price = price
        if rare is not None: g.rare = rare
        if emoji is not None: g.emoji = emoji
        if file is not None:
            g.media_url, g.media_type = await save_file(file)
        await s.commit()
    return {"ok": True}


@router.delete("/gift/{gid}")
async def delete_gift(gid: int, u=Depends(require_admin)):
    async with SessionLocal() as s:
        g = await s.get(Gift, gid)
        if g:
            g.active = False
            await s.commit()
    return {"ok": True}


# ---------- ADMIN boshqaruvi ----------
@router.get("/admins")
async def list_admins(u=Depends(require_admin)):
    async with SessionLocal() as s:
        rows = (await s.execute(select(Admin))).scalars().all()
        return [{"id": a.id, "super": a.id == config.SUPER_ADMIN_ID} for a in rows]


@router.post("/admins")
async def add_admin(admin_id: int = Body(..., embed=True), u=Depends(require_admin)):
    async with SessionLocal() as s:
        if not await s.get(Admin, admin_id):
            s.add(Admin(id=admin_id, added_by=u["id"]))
            await s.commit()
    return {"ok": True}


@router.delete("/admins/{admin_id}")
async def del_admin(admin_id: int, u=Depends(require_admin)):
    if admin_id == config.SUPER_ADMIN_ID:
        raise HTTPException(400, "Asosiy adminni o'chirib bo'lmaydi")
    async with SessionLocal() as s:
        a = await s.get(Admin, admin_id)
        if a:
            await s.delete(a)
            await s.commit()
    return {"ok": True}
