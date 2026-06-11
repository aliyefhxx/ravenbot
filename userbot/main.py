"""Ryhavean Userbot - Render Web Service (7/24 self-ping)"""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import Config
import db
import ratelimit
import plugin_loader
import commands
import security
import quotly

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ryhavean")

tg_client: TelegramClient | None = None


def get_session_string() -> str:
    raw = Config.SESSION_STRING
    if not raw:
        log.critical("SESSION_STRING env yoxdur")
        sys.exit(1)
    if raw.startswith("enc:"):
        try:
            return security.decrypt(raw[4:])
        except Exception as e:
            log.critical("Session deşifrə xətası: %s", e)
            sys.exit(1)
    return raw


async def post_restart_notice(client):
    chat = await db.get_setting("restart_chat")
    mid = await db.get_setting("restart_msg")
    if chat and mid:
        try:
            await client.edit_message(int(chat), int(mid), "✅ <b>Restart tamamlandı</b>", parse_mode="html")
        except Exception:
            pass
        await db.set_setting("restart_chat", "")
        await db.set_setting("restart_msg", "")


async def start_userbot():
    global tg_client
    log.info("🚀 Ryhavean Userbot başladılır...")
    await db.init_db()
    await ratelimit.init_redis()

    tg_client = TelegramClient(
        StringSession(get_session_string()),
        Config.API_ID,
        Config.API_HASH,
        device_model="Ryhavean Userbot",
        system_version="1.0.0",
        app_version="1.0.0",
    )
    await tg_client.start()
    me = await tg_client.get_me()
    log.info("✅ Daxil oldu: %s (@%s) id=%s", me.first_name, me.username, me.id)

    commands.register(tg_client)
    quotly.register_quotly(tg_client)
    await plugin_loader.load_all(tg_client)
    await post_restart_notice(tg_client)

    try:
        await tg_client.send_message("me", "✨ <b>Ryhavean Userbot uğurla aktiv edildi.</b>", parse_mode="html")
    except Exception:
        pass

    log.info("🟢 Userbot işləyir. Komandalar üçün .help yazın.")
    await tg_client.run_until_disconnected()


async def _userbot_runner():
    try:
        await start_userbot()
    except Exception:
        log.exception("Userbot kritik xəta - prosess restart")
        os._exit(1)


async def _self_ping_loop():
    """
    Render Free planında 15 dəq inaktivlikdən sonra service yuxuya gedir.
    Hər 10 dəqiqədən bir öz URL-ni ping edirik ki, həmişə oyaq qalsın.
    """
    # Render avtomatik olaraq RENDER_EXTERNAL_URL env-i təyin edir
    url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("SELF_URL")
    if not url:
        log.warning("⚠️ RENDER_EXTERNAL_URL tapılmadı — self-ping deaktivdir")
        return

    ping_url = url.rstrip("/") + "/health"
    log.info("🔁 Self-ping aktivdir: %s (hər 10 dəq)", ping_url)

    # İlk ping-i 60 sandyə sonra
    await asyncio.sleep(60)

    async with httpx.AsyncClient(timeout=15.0) as http:
        while True:
            try:
                r = await http.get(ping_url)
                log.info("🔁 Self-ping: %s", r.status_code)
            except Exception as e:
                log.warning("Self-ping xətası: %s", e)
            await asyncio.sleep(600)  # 10 dəqiqə


@asynccontextmanager
async def lifespan(app: FastAPI):
    userbot_task = asyncio.create_task(_userbot_runner())
    ping_task = asyncio.create_task(_self_ping_loop())
    yield
    ping_task.cancel()
    userbot_task.cancel()
    if tg_client and tg_client.is_connected():
        await tg_client.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    connected = tg_client.is_connected() if tg_client else False
    return {"status": "ok", "userbot_connected": connected}


@app.get("/health")
async def health():
    if tg_client and tg_client.is_connected():
        return {"status": "healthy"}
    return {"status": "starting"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
