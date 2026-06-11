"""
==================================================
🖼  QUOTLY + .SEKIL KOMANDASI - RYHAVEAN
==================================================
.q  / .qs   -> QuotLyBot vasitəsilə stiker düzəldir və
              ORİJİNAL mesaja CAVAB olaraq göndərir.
.sekil ad   -> SEKIL_KANAL kanalından random şəkil çəkir
              və qanlı/dramatik caption ilə komanda yazılan
              yerə göndərir (reply varsa orijinal mesaja cavab).
"""

import os
import random
import asyncio
import logging
import time
from telethon import events
from telethon.tl.types import MessageMediaPhoto

# emoji_utils import-u monkey-patch tətbiq edir + apply_premium_emojis verir
from emoji_utils import apply_premium_emojis

log = logging.getLogger("quotly")

SEKIL_KANAL = "@ryhavean_pics"  # kanal adını burdan dəyiş
_PHOTO_CACHE: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 600  # 10 dəqiqə


# ---------------------------------------------------------------
#  .q / .qs
# ---------------------------------------------------------------
def register_quotly(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        reply_message = await event.get_reply_message()
        if not reply_message:
            try:
                await event.delete()
            except Exception:
                pass
            return

        command = event.pattern_match.group(1)
        try:
            await event.delete()
        except Exception:
            pass

        bot_username = "QuotLyBot"

        try:
            async with event.client.conversation(
                bot_username, timeout=30, exclusive=False
            ) as conv:
                # 1) Mesajı bota forward et
                await event.client.forward_messages(bot_username, reply_message)

                # 2) Botdan media-lı cavab gözlə (bəzən əvvəlcə "...işlənir" mətni gəlir)
                final_response = None
                for _ in range(6):
                    try:
                        resp = await conv.get_response(timeout=10)
                    except asyncio.TimeoutError:
                        break
                    if resp.media:
                        final_response = resp
                        break
                    # mətnli ara mesajdırsa, növbətini gözlə
                    final_response = resp

                # 3) .qs olarsa, /q s göndərib şəkil variantını al
                if command == "qs" and final_response is not None:
                    try:
                        await conv.send_message("/q s", reply_to=final_response.id)
                    except Exception:
                        await conv.send_message("/q s")
                    for _ in range(6):
                        try:
                            resp = await conv.get_response(timeout=10)
                        except asyncio.TimeoutError:
                            break
                        if resp.media:
                            final_response = resp
                            break
                        final_response = resp

                if not final_response:
                    return

                # 4) Stiker / şəkli ORİJİNAL mesaja cavab kimi göndər
                if final_response.media:
                    await event.client.send_file(
                        event.chat_id,
                        final_response.media,
                        reply_to=reply_message.id,
                    )
                elif final_response.text:
                    await event.client.send_message(
                        event.chat_id,
                        final_response.text,
                        reply_to=reply_message.id,
                    )

        except asyncio.TimeoutError:
            log.warning(".q: QuotLyBot cavab vermədi (timeout)")
        except Exception as e:
            log.exception(".q xətası: %s", e)

    # -----------------------------------------------------------
    #  .sekil <ad>
    # -----------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sekil(?:\s+(.+))?$"))
    async def sekil_handler(event):
        ad = (event.pattern_match.group(1) or "").strip()
        if not ad:
            try:
                await event.edit("🩸 <b>İstifadə:</b> <code>.sekil ad</code>", parse_mode="html")
            except Exception:
                pass
            return

        reply_message = await event.get_reply_message()

        try:
            await event.delete()
        except Exception:
            pass

        # 1) Kanaldan foto-list keşi
        photos = await _get_channel_photos(event.client, SEKIL_KANAL)
        if not photos:
            await event.client.send_message(
                event.chat_id,
                apply_premium_emojis(
                    f"❌ <b>{SEKIL_KANAL}</b> kanalından şəkil tapılmadı."
                ),
                parse_mode="html",
            )
            return

        msg = random.choice(photos)

        # 2) Qanlı/dramatik caption
        caption = _bloody_caption(ad)

        # 3) Göndər
        try:
            await event.client.send_file(
                event.chat_id,
                msg.media,
                caption=caption,
                parse_mode="html",
                reply_to=reply_message.id if reply_message else None,
            )
        except Exception as e:
            log.exception(".sekil göndərmə xətası: %s", e)
            await event.client.send_message(
                event.chat_id,
                apply_premium_emojis(f"❌ Şəkil göndərilə bilmədi: <code>{e}</code>"),
                parse_mode="html",
            )


async def _get_channel_photos(client, channel: str, limit: int = 200):
    """Kanaldan foto-lu mesajları çəkir və 10 dəq keş edir."""
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
    """
    Qanlı / dramatik efektli caption.
    Premium emojilər avtomatik patch sayəsində çevriləcək.
    """
    upper = ad.upper()
    inner = (
        f"🩸 <b>『 {upper} 』</b> 🩸\n"
        f"<i>꧁༒ {ad} ༒꧂</i>\n\n"
        f"<blockquote>💀  𝕽𝖞𝖍𝖆𝖛𝖊𝖆𝖓  🔥</blockquote>"
    )
    return apply_premium_emojis(inner)
