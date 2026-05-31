"""Ryhavean Userbot - giriş nöqtəsi"""
import asyncio
import logging
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import Config
import db, ratelimit, plugin_loader, commands, security

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ryhavean")

def get_session_string() -> str:
    raw = Config.SESSION_STRING
    if not raw:
        log.critical("SESSION_STRING env yoxdur")
        sys.exit(1)
    # Şifrələnmişdirsə açırıq
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

async def main():
    log.info("🚀 Ryhavean Userbot başladılır...")
    await db.init_db()
    await ratelimit.init_redis()

    client = TelegramClient(
        StringSession(get_session_string()),
        Config.API_ID,
        Config.API_HASH,
        device_model="Ryhavean Userbot",
        system_version="1.0.0",
        app_version="1.0.0",
    )
    await client.start()
    me = await client.get_me()
    log.info("✅ Daxil oldu: %s (@%s) id=%s", me.first_name, me.username, me.id)

    commands.register(client)
    await plugin_loader.load_all(client)
    await post_restart_notice(client)

    try:
        await client.send_message("me", "✨ <b>Ryhavean Userbot uğurla aktiv edildi.</b>", parse_mode="html")
    except Exception:
        pass

    log.info("🟢 Userbot işləyir. Komandalar üçün .help yazın.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        log.exception("Kritik xəta - konteyner restart ediləcək")
        sys.exit(1)  # Northflank/Docker restart policy
