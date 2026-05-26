"""
Konfiguratsiya — barcha maxfiy ma'lumotlar Railway'dagi Environment Variables'dan olinadi.
Hech qachon token/kalitlarni shu faylga yozma!
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === ASOSIY ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "8135915671"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@PRUM_STAR")
HELP_USERNAME = os.getenv("HELP_USERNAME", "@yordamad")
BOT_USERNAME = os.getenv("BOT_USERNAME", "PrumStarBot")

# === MINI APP ===
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.vercel.app")

# === WEB SERVICE (Railway public domen) ===
# Railway -> Settings -> Networking -> Generate Domain dan olinadi, masalan:
# PUBLIC_URL=https://prumstar-bot-production.up.railway.app
PUBLIC_URL = os.getenv("PUBLIC_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN", ""))
if PUBLIC_URL and not PUBLIC_URL.startswith("http"):
    PUBLIC_URL = "https://" + PUBLIC_URL
PORT = int(os.getenv("PORT", "8000"))

# === MEDIA (yuklangan rasm/animatsiyalar) ===
# Railway Volume ni /data ga ulang. Aks holda redeploy'da o'chadi.
MEDIA_DIR = os.getenv("MEDIA_DIR", "/data/media")

# === BAZA ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///local.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# === PREMIUM EMOJI ID lari ===
EMOJI_STAR = os.getenv("EMOJI_STAR", "5435957248314403262")
EMOJI_CARD = os.getenv("EMOJI_CARD", "5377498341074542641")
EMOJI_OK = os.getenv("EMOJI_OK", "5427009714745517609")
EMOJI_DOWN = os.getenv("EMOJI_DOWN", "5436107770032894454")
