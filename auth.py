"""
Telegram Mini App initData ni tekshirish (HMAC-SHA256).
Bu orqali API kim chaqirayotganini ishonchli biladi (soxta so'rovlar o'tmaydi).
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException

import config


def verify_init_data(init_data: str) -> dict:
    """initData to'g'ri bo'lsa user dict qaytaradi, aks holda xato."""
    if not init_data:
        raise HTTPException(401, "initData yo'q")
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except Exception:
        raise HTTPException(401, "initData buzuq")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "hash yo'q")

    data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed))
    secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise HTTPException(403, "Imzo noto'g'ri")

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(401, "user yo'q")
    user = json.loads(user_raw)
    return user


async def get_current_user(x_init_data: str = Header(default="")) -> dict:
    """FastAPI dependency: har bir himoyalangan endpoint shu orqali userni oladi."""
    return verify_init_data(x_init_data)
