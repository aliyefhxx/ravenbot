"""Ryhavean Userbot - Render Web Service (7/24 self-ping)"""
import asyncio
import logging
import os
import sys
import re
import random
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityCustomEmoji

from config import Config
import db, ratelimit, plugin_loader, commands, security

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ryhavean")

tg_client: TelegramClient | None = None
premium_emojis = []

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

# Premium emoji paketlərini çəkən funksiya
async def update_premium_emojis(client):
    global premium_emojis
    packs = ["HmmHDEmoji", "FrogeEmoji"]
    new_emojis = []
    for pack in packs:
        try:
            stickerset = await client(functions.messages.GetStickerSetRequest(
                stickerset=types.InputStickerSetShortName(short_name=pack),
                hash=0
            ))
            for doc in stickerset.documents:
                new_emojis.append(doc.id)
        except Exception as e:
            log.error(f"Emoji pack yüklənmə xətası ({pack}): {e}")
    premium_emojis = new_emojis

# Client-i patch edən funksiya
def patch_client(client):
    original_send_message = client.send_message

    async def send_message_patched(entity, message, **kwargs):
        if isinstance(message, str) and premium_emojis:
            emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]')
            matches = list(emoji_pattern.finditer(message))
            if matches:
                entities = kwargs.get('formatting_entities') or []
                for match in matches:
                    entities.append(MessageEntityCustomEmoji(
                        offset=match.start(),
                        length=1,
                        document_id=random.choice(premium_emojis)
                    ))
                kwargs['formatting_entities'] = entities
                message = emoji_pattern.sub(" ", message)
        return await original_send_message(entity, message, **kwargs)

    client.send_message = send_message_patched

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
    
    # Premium emoji sistemini aktivləşdiririk
    patch_client(tg_client)
    await update_premium_emojis(tg_client)
    
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

async def _userbot_runner():
    try:
        await start_userbot()
    except Exception:
        log.exception("Userbot kritik xəta - prosess restart")
        os._exit(1)

async def _self_ping_loop():
    url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("SELF_URL")
    if not url:
        log.warning("⚠️ RENDER_EXTERNAL_URL tapılmadı — self-ping deaktivdir")
        return

    ping_url = url.rstrip("/") + "/health"
    log.info("🔁 Self-ping aktivdir: %s (hər 10 dəq)", ping_url)
    await asyncio.sleep(60)

    async with httpx.AsyncClient(timeout=15.0) as http:
        while True:
            try:
                r = await http.get(ping_url)
                log.info("🔁 Self-ping: %s", r.status_code)
            except Exception as e:
                log.warning("Self-ping xətası: %s", e)
            await asyncio.sleep(600)

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
