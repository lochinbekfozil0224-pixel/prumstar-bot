# PRUM STAR — Backend (web service) — 1+3-bosqich

Railway'da **bitta web service**: Telegram bot (webhook) + Mini App API + Admin API + media fayllar.

## 📁 Fayllar
- `app.py` — FastAPI: webhook, API'larni birlashtiradi, media beradi
- `bot.py` — bot handlerlari (/start, obuna, salom)
- `api.py` — Mini App API (config, gifts, me, history, rating, referral, lang)
- `admin_api.py` — Admin API (narx, media yuklash, gift, premium, adminlar)
- `auth.py` — initData HMAC tekshiruvi (xavfsizlik)
- `db.py` — baza, `config.py` — sozlamalar, `helpers.py` — emoji/obuna/tugma
- `texts.py` — bot matnlari (premium emojili)

## 🚀 Railway'ga joylash

1. Bu papkani GitHub'ga yuklang.
2. Railway → **Deploy from GitHub repo**.
3. **+ New → Database → PostgreSQL** qo'shing (DATABASE_URL avto keladi).
4. **+ New → Volume** qo'shing, **Mount path = `/data`** (yuklangan rasmlar saqlanishi uchun. Volume bo'lmasa redeploy'da rasmlar o'chadi!).
5. Railway → **Settings → Networking → Generate Domain** bosing. Hosil bo'lgan havolani oling.
6. **Variables** ga yozing:

   | Nomi | Qiymati |
   |------|---------|
   | `BOT_TOKEN` | @BotFather'dan **YANGI** token |
   | `SUPER_ADMIN_ID` | `8135915671` |
   | `CHANNEL_USERNAME` | `@PRUM_STAR` |
   | `HELP_USERNAME` | `@yordamad` |
   | `BOT_USERNAME` | `PrumStarBot` |
   | `PUBLIC_URL` | 5-qadamdagi domen (https://...up.railway.app) |
   | `WEBAPP_URL` | Vercel app havolasi |
   | `MEDIA_DIR` | `/data/media` |

7. Deploy bo'lgach log'da "Webhook o'rnatildi" chiqsa — tayyor.
   Botga `/start` yozing; "Ilovani ochish" → Mini App ochiladi.

## 🔗 Mini App'ni backendga ulash
Vercel'dagi `index.html` ichida:
```js
const API_BASE = "https://SIZNING-railway-domeningiz.up.railway.app";
```
Bo'sh qolsa Mini App namuna ma'lumot bilan ishlaydi (admin saqlay olmaydi).

## 🔐 Xavfsizlik
- Eski token ochiq ko'rindi → **@BotFather → /revoke** qiling.
- @PrumStarBot **@PRUM_STAR kanalida admin** bo'lsin.
- Admin panelni faqat ID `8135915671` va siz qo'shgan adminlar ko'radi (server tekshiradi, soxta o'tmaydi).

## ⭐️ Premium emoji
Bot egasida (akkauntingizda) **Telegram Premium** bo'lsa, bot premium emoji yuboradi.

## 🧪 Test qilingan
- initData imzo tekshiruvi (soxta rad etiladi)
- 1 star narxi o'zgartirish, mehmonga 403
- Gift qo'shish (media bilan), karta mediasi yuklash
- Admin qo'shish/ro'yxat

## ⏭️ Qolgan
4-bosqich: **Paylov to'lov** + Fragment oqimi + sotib olish tugmalarini jonli ulash.
