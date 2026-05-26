"""
Baza modellari va ulanish. Mini App, admin panel va to'lovlar shu jadvallardan foydalanadi.
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Integer, Float, Boolean, DateTime, Text, func, select
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL, SUPER_ADMIN_ID

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str] = mapped_column(Text, nullable=True)
    lang: Mapped[str] = mapped_column(String(8), default="uz")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    stars_earned: Mapped[float] = mapped_column(Float, default=0.0)   # reyting (umumiy)
    stars_month: Mapped[float] = mapped_column(Float, default=0.0)    # reyting (oy)
    stars_week: Mapped[float] = mapped_column(Float, default=0.0)     # reyting (hafta)
    spent_uzs: Mapped[float] = mapped_column(Float, default=0.0)      # jami sarflagan so'm
    ref_stars: Mapped[float] = mapped_column(Float, default=0.0)      # referal yulduzlari
    ref_count: Mapped[int] = mapped_column(Integer, default=0)        # do'stlar soni
    referred_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PremiumPlan(Base):
    __tablename__ = "premium_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    months: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    admin_only: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Gift(Base):
    __tablename__ = "gifts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    emoji: Mapped[str] = mapped_column(String(16), nullable=True)       # media bo'lmasa ko'rinadi
    media_url: Mapped[str] = mapped_column(Text, nullable=True)         # yuklangan GIF/MP4/Lottie
    media_type: Mapped[str] = mapped_column(String(16), nullable=True)  # gif/mp4/lottie/img
    price: Mapped[float] = mapped_column(Float)
    rare: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    target_username: Mapped[str] = mapped_column(String(64), nullable=True)
    kind: Mapped[str] = mapped_column(String(16))      # balance/stars/premium/gift
    title: Mapped[str] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Float)       # so'm
    qty: Mapped[float] = mapped_column(Float, default=0)  # stars soni yoki oy
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/paid/done/failed
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)


# ---------- yordamchilar ----------
async def get_setting(s: AsyncSession, key: str, default=None):
    row = await s.get(Setting, key)
    return row.value if row and row.value is not None else default


async def set_setting(s: AsyncSession, key: str, value: str):
    row = await s.get(Setting, key)
    if row:
        row.value = value
    else:
        s.add(Setting(key=key, value=value))


async def is_admin(s: AsyncSession, user_id: int) -> bool:
    if user_id == SUPER_ADMIN_ID:
        return True
    return (await s.get(Admin, user_id)) is not None


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_defaults():
    async with SessionLocal() as s:
        if not await s.get(Admin, SUPER_ADMIN_ID):
            s.add(Admin(id=SUPER_ADMIN_ID))

        if await get_setting(s, "per_star") is None:
            await set_setting(s, "per_star", "224")   # 1 star narxi (so'm)

        if not (await s.execute(select(PremiumPlan).limit(1))).first():
            s.add(PremiumPlan(months=1, price=52000, discount=0, admin_only=True, sort=0))
            s.add(PremiumPlan(months=3, price=190000, discount=20, sort=1))
            s.add(PremiumPlan(months=6, price=250000, discount=37, sort=2))
            s.add(PremiumPlan(months=12, price=420000, discount=42, sort=3))

        if not (await s.execute(select(Gift).limit(1))).first():
            gifts = [
                ("Ayiq","🧸",4000,0),("Yurak","💝",4000,0),("Atirgul","🌹",7000,0),
                ("Sovg'a","🎁",7000,0),("Archa","🎄",14000,1),("Yangi Yil Ayig'i","🧸",14000,1),
                ('Yurak "Love"',"💗",14000,1),("Yurakli Ayiq","🧸",14000,1),("Shampan","🍾",14000,0),
                ("Raketa","🚀",14000,0),("Gul","💐",14000,0),("Tort","🎂",14000,0),
                ("Pushti Ayiq","🧸",14000,1),("Tangalik Ayiq","🍀",14000,1),("Olmos","💎",14000,0),
            ]
            for i,(nm,em,pr,rr) in enumerate(gifts):
                s.add(Gift(name=nm, emoji=em, price=pr, rare=bool(rr), sort=i))

        await s.commit()
