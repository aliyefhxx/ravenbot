# userbot/main.py — Tam hazır versiya

import os
import logging
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode

# === Monkey-patch: Bütün mesajları avtomatik qalın (bold) et ===
_original_send_message = Client.send_message
_original_edit_message_text = Client.edit_message_text
_original_edit_message_caption = Client.edit_message_caption

_original_send_photo = Client.send_photo
_original_send_document = Client.send_document
_original_send_video = Client.send_video
_original_send_audio = Client.send_audio
_original_send_animation = Client.send_animation
_original_send_voice = Client.send_voice

def _make_bold(text: str) -> str:
    if not text or not text.strip():
        return text
    text = text.strip()
    if text.startswith("<b>") and text.endswith("</b>"):
        return text
    if text.startswith("```") or text.startswith("<code"):
        return text
    return f"<b>{text}</b>"

async def _patched_send_message(self, chat_id, text, **kwargs):
    kwargs["parse_mode"] = ParseMode.HTML
    if text:
        text = _make_bold(str(text))
    return await _original_send_message(self, chat_id, text, **kwargs)

async def _patched_edit_message_text(self, chat_id, message_id, text, **kwargs):
    kwargs["parse_mode"] = ParseMode.HTML
    if text:
        text = _make_bold(str(text))
    return await _original_edit_message_text(self, chat_id, message_id, text, **kwargs)

async def _patched_edit_message_caption(self, chat_id, message_id, caption, **kwargs):
    kwargs["parse_mode"] = ParseMode.HTML
    if caption:
        caption = _make_bold(str(caption))
    return await _original_edit_message_caption(self, chat_id, message_id, caption, **kwargs)

async def _patched_send_media(self, original, chat_id, **kwargs):
    kwargs["parse_mode"] = ParseMode.HTML
    if kwargs.get("caption"):
        kwargs["caption"] = _make_bold(str(kwargs["caption"]))
    return await original(self, chat_id, **kwargs)

def apply_bold_patch():
    Client.send_message = _patched_send_message
    Client.edit_message_text = _patched_edit_message_text
    Client.edit_message_caption = _patched_edit_message_caption
    Client.send_photo = lambda self, chat_id, **kwargs: _patched_send_media(_original_send_photo, self, chat_id, **kwargs)
    Client.send_document = lambda self, chat_id, **kwargs: _patched_send_media(_original_send_document, self, chat_id, **kwargs)
    Client.send_video = lambda self, chat_id, **kwargs: _patched_send_media(_original_send_video, self, chat_id, **kwargs)
    Client.send_audio = lambda self, chat_id, **kwargs: _patched_send_media(_original_send_audio, self, chat_id, **kwargs)
    Client.send_animation = lambda self, chat_id, **kwargs: _patched_send_media(_original_send_animation, self, chat_id, **kwargs)
    Client.send_voice = lambda self, chat_id, **kwargs: _patched_send_media(_original_send_voice, self, chat_id, **kwargs)

# ==============================================================

# Redis import (əgər varsa)
try:
    from .helpers import ratelimit
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("userbot")

# Env dəyişənləri
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

PLUGINS = dict(root="userbot/plugins")

async def start_userbot():
    apply_bold_patch()  # ← Monkey-patch burada tətbiq olunur

    if HAS_REDIS:
        try:
            await ratelimit.init_redis()
            logger.info("Redis initialized")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")

    client = Client(
        name="ravenbot",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=STRING_SESSION or None,
        bot_token=BOT_TOKEN or None,
        plugins=PLUGINS,
        parse_mode=ParseMode.HTML,
    )

    await client.start()
    logger.info("Userbot started! 7/24 aktiv.")
    await idle()
    await client.stop()

if __name__ == "__main__":
    asyncio.run(start_userbot())
