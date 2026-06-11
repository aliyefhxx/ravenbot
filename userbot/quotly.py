"""
==================================================
🖼  QUOTLY + .SEKIL KOMANDASI - RYHAVEAN (FIXED)
==================================================
.q  / .qs   -> QuotLyBot vasitəsilə stiker düzəldir və
              ORİJİNAL mesaja CAVAB olaraq göndərir.
              ("No message was sent previously" xətası
              həll edildi — conversation əvəzinə event
              polling istifadə olunur.)
.sekil ad   -> SEKIL_KANAL kanalından random şəkil çəkir
              və qanlı/dramatik caption ilə göndərir.
"""

import random
import asyncio
import logging
import time
from telethon import events
from telethon.tl.types import MessageMediaPhoto

from emoji_utils import apply_premium_emojis

log = logging.getLogger("quotly")

SEKIL_KANAL = "@ryhavean_pics"
_PHOTO_CACHE: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 600

QUOTLY_BOT = "QuotLyBot"


def _info(cmd: str, usage: str, desc: str) -> str:
    return apply_premium_emojis(
        f"ℹ️ <b>.{cmd}</b> — {desc}\n"
        f"📖 <b>İstifadə:</b> <code>{usage}</code>"
    )


async def _wait_quotly_response(client, bot_id: int, after_ts: float, timeout: int = 25):
    """
    QuotLyBot-dan gələn ilk media-lı (stiker/şəkil) mesajı gözləyir.
    conversation istifadə etmir, ona görə də
    'No message was sent previously' xətasını verə bilməz.
    """
    end = time.time() + timeout
    last_seen = None
    while time.time() < end:
        try:
            async for m in client.iter_messages(bot_id, limit=5):
                if m.date.timestamp() < after_ts - 1:
                    break
                if m.media and (m.sticker or m.photo):
                    return m
                last_seen = m
        except Exception as ex:
            log.debug("iter_messages xətası: %s", ex)
        await asyncio.sleep(1.2)
    return last_seen


def register_quotly(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)($|\s)"))
    async def quotly_handler(event):
        reply_message = await event.get_reply_message()
        if not reply_message:
            try:
                await event.edit(
                    _info("q", ".q (mesaja cavab ver)",
                          "Cavab verdiyin mesajdan stiker / şəkil-quote düzəldir."),
                    parse_mode="html",
                )
            except Exception:
                pass
            return

        command = event.pattern_match.group(1)
        chat_id = event.chat_id
        reply_to_id = reply_message.id

        try:
            await event.delete()
        except Exception:
            pass

        try:
            bot = await client.get_entity(QUOTLY_BOT)
        except Exception as e:
            log.warning("QuotLyBot tapılmadı: %s", e)
            return

        sent_ts = time.time()

        try:
            await client.forward_messages(bot, reply_message)
        except Exception as e:
            log.warning(".q forward xətası: %s", e)
            return

        final_response = await _wait_quotly_response(client, bot.id, sent_ts, timeout=25)

        if command == "qs" and final_response is not None and final_response.sticker:
            try:
                await client.send_message(bot, "/q s", reply_to=final_response.id)
            except Exception:
                try:
                    await client.send_message(bot, "/q s")
                except Exception:
                    pass
            sent_ts2 = time.time()
            shot = await _wait_quotly_response(client, bot.id, sent_ts2, timeout=20)
            if shot is not None:
                final_response = shot

        if not final_response or not final_response.media:
            log.warning(".q: QuotLyBot cavab vermədi")
            return

        try:
            await client.send_file(
                chat_id,
                final_response.media,
                reply_to=reply_to_id,
            )
        except Exception as e:
            log.exception(".q göndərmə xətası: %s", e)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sekil($|\s+(.*))"))
    async def sekil_handler(event):
        ad = (event.pattern_match.group(2) or "").strip() if event.pattern_match.group(2) else ""
        if not ad:
            try:
                await event.edit(
                    _info("sekil", ".sekil <ad>",
                          "Kanaldan random şəkil çəkib qanlı caption ilə göndərir."),
                    parse_mode="html",
                )
            except Exception:
                pass
            return

        reply_message = await event.get_reply_message()
        try:
            await event.delete()
        except Exception:
            pass

        photos = await _get_channel_photos(client, SEKIL_KANAL)
        if not photos:
            await client.send_message(
                event.chat_id,
                apply_premium_emojis(f"❌ <b>{SEKIL_KANAL}</b> kanalından şəkil tapılmadı."),
                parse_mode="html",
            )
            return

        msg = random.choice(photos)
        caption = _bloody_caption(ad)

        try:
            await client.send_file(
                event.chat_id,
                msg.media,
                caption=caption,
                parse_mode="html",
                reply_to=reply_message.id if reply_message else None,
            )
        except Exception as e:
            log.exception(".sekil göndərmə xətası: %s", e)
            await client.send_message(
                event.chat_id,
                apply_premium_emojis(f"❌ Şəkil göndərilə bilmədi: <code>{e}</code>"),
                parse_mode="html",
            )


async def _get_channel_photos(client, channel: str, limit: int = 200):
    now = time.time()
    cached = _PHOTO_CACHE.get(channel)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]
    try:
        entity = await client.get_entity(channel)
    except Exception as e:
        log.warning("Kanal entity tapılmadı (%s): %s", channel, e)
        return []
    photos = []
    try:
        async for m in client.iter_messages(entity, limit=limit):
            if m.media and isinstance(m.media, MessageMediaPhoto):
                photos.append(m)
    except Exception as e:
        log.warning("iter_messages xətası: %s", e)
        return []
    _PHOTO_CACHE[channel] = (now, photos)
    return photos


def _bloody_caption(ad: str) -> str:
    upper = ad.upper()
    inner = (
        f"🩸 <b>『 {upper} 』</b> 🩸\n"
        f"<i>꧁༒ {ad} ༒꧂</i>\n\n"
        f"<blockquote>💀  𝕽𝖞𝖍𝖆𝖛𝖊𝖆𝖓  🔥</blockquote>"
    )
    return apply_premium_emojis(inner)
