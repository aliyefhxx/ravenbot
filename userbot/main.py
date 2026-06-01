"""Ryhavean Userbot - Render Web Service giriş nöqtəsi"""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import Config
import db, ratelimit, plugin_loader, commands, security

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ryhavean")

# Qlobal client referansı (health endpoint üçün)
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
    """Userbot-u başlat və disconnect olana qədər işlət."""
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
    await plugin_loader.load_all(tg_client)
    await post_restart_notice(tg_client)

    try:
        await tg_client.send_message("me", "✨ <b>Ryhavean Userbot uğurla aktiv edildi.</b>", parse_mode="html")
    except Exception:
        pass

    log.info("🟢 Userbot işləyir. Komandalar üçün .help yazın.")
    await tg_client.run_until_disconnected()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI start olanda userbot-u arxa fonda başlat
    task = asyncio.create_task(_runner())
    yield
    # Shutdown
    task.cancel()
    if tg_client and tg_client.is_connected():
        await tg_client.disconnect()


async def _runner():
    try:
        await start_userbot()
    except Exception:
        log.exception("Userbot kritik xəta - prosess restart ediləcək")
        # Render avtomatik restart edəcək
        os._exit(1)


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
