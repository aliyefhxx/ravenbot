"""
==================================================
🤖 BÜTÜN DAXİLİ KOMANDALAR - RYHAVEAN USERBOT
==================================================
"""

import asyncio
import io
import random
import logging
import time
import os
import sys
from telethon import events
from telethon.tl.types import (
    ChatBannedRights, InputPhotoEmpty, InputPeerUser,
)
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest, GetUserPhotosRequest
from telethon.errors import FloodWaitError, ChatAdminRequiredError, UserAdminInvalidError
from telethon.tl.functions.users import GetFullUserRequest

from config import Config
from db import pool, get_setting, set_setting
import ratelimit
import plugin_loader

log = logging.getLogger("cmds")
P = Config.CMD_PREFIX

START_TIME = time.time()

# ============ 🛠 YARDIMÇI FUNKSİYALAR ============
def cmd_re(name: str) -> str:
    return rf"(?i)^\{P}{name}(?:\s|$)(.*)"

async def edit_safe(event, text: str):
    try:
        await event.edit(text, parse_mode="html", link_preview=False)
    except Exception:
        await event.respond(text, parse_mode="html", link_preview=False)

async def rl_check(event, key: str, limit=5, per=10) -> bool:
    ok = await ratelimit.allow(f"{event.sender_id}:{key}", limit, per)
    if not ok:
        await edit_safe(event, "⏳ <b>Çox sürətli! Bir az gözləyin.</b>")
    return ok

async def get_target_user(event):
    """Reply / username / id -dən target tap"""
    arg = event.pattern_match.group(1).strip() if event.pattern_match else ""
    if event.is_reply:
        msg = await event.get_reply_message()
        return msg.sender_id, msg.sender
    if not arg:
        return None, None
    arg = arg.split()[0]
    try:
        if arg.isdigit() or (arg.startswith("-") and arg[1:].isdigit()):
            ent = await event.client.get_entity(int(arg))
        else:
            ent = await event.client.get_entity(arg.lstrip("@"))
        return ent.id, ent
    except Exception:
        return None, None

# ============ 💎 KOMANDALAR ============

def register(client):

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("alive")))
    async def alive(event):
        if not await rl_check(event, "alive"): return
        msg = await get_setting("alive_msg") or (
            "✨ <b>Ryhavean Userbot aktivdir</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "🤖 <b>Sistem:</b> <code>online</code>\n"
            "⚡ <b>Versiya:</b> <code>1.0.0</code>\n"
            "🛡 <b>Təhlükəsizlik:</b> <code>aktiv</code>"
        )
        await edit_safe(event, msg)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("dlive")))
    async def dlive(event):
        new = event.pattern_match.group(1).strip()
        if not new:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}dlive yeni mesaj</code>")
        await set_setting("alive_msg", new)
        await edit_safe(event, "✅ <b>Alive mesajı yeniləndi.</b>")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("restart")))
    async def restart(event):
        await edit_safe(event, "♻️ <b>Restart edilir...</b>")
        await set_setting("restart_chat", str(event.chat_id))
        await set_setting("restart_msg", str(event.id))
        os.execv(sys.executable, [sys.executable, *sys.argv])

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("help")))
    async def help_cmd(event):
        cmds = [
            ".alive - <b>botun aktivliyini yoxla</b>",
            ".dlive <mesaj> - <b>alive mesajını dəyiş</b>",
            ".restart - <b>userbotu yenidən başlat</b>",
            ".ban [reply/id/username] - <b>ban et</b>",
            ".unban - <b>banı aç</b>",
            ".mute - <b>mute et</b>",
            ".block / .unblock - <b>bloklama</b>",
            ".info - <b>istifadəçi məlumatı</b>",
            ".tag mention|3|5|random - <b>tag</b>",
            ".setwelcome <mesaj> - <b>xoş gəldin mesajı</b>",
            ".purge [N] - <b>mesaj sil</b>",
            ".klon - <b>profil klonla</b>",
            ".unklon - <b>klonu sıfırla</b>",
            ".pinstall (reply .py) - <b>plugin qur</b>",
            ".unpinstall <ad> - <b>plugin sil</b>",
        ]
        plugins = list(plugin_loader.loaded.keys())
        text = "📚 <b>Ryhavean Userbot Yardım</b>\n━━━━━━━━━━━━━━━\n"
        text += "\n".join(f"• <code>{c}</code>" for c in cmds)
        text += f"\n\n🔌 <b>Yüklü Pluginlər ({len(plugins)}):</b> "
        text += ", ".join(plugins) if plugins else "<i>yoxdur</i>"
        await edit_safe(event, text)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("ban")))
    async def ban(event):
        uid, ent = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}ban</code> (reply) və ya <code>{P}ban @user</code>")
        try:
            rights = ChatBannedRights(until_date=None, view_messages=True)
            await event.client(EditBannedRequest(event.chat_id, uid, rights))
            await edit_safe(event, f"🔨 <b>Ban olundu:</b> <code>{uid}</code>")
        except (ChatAdminRequiredError, UserAdminInvalidError):
            await edit_safe(event, "⚠️ <b>Yetkiniz yoxdur.</b>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unban")))
    async def unban(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}unban @user</code>")
        try:
            rights = ChatBannedRights(until_date=None, view_messages=False)
            await event.client(EditBannedRequest(event.chat_id, uid, rights))
            await edit_safe(event, f"✅ <b>Ban açıldı:</b> <code>{uid}</code>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("mute")))
    async def mute(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}mute</code> (reply/id/username)")
        try:
            rights = ChatBannedRights(until_date=None, send_messages=True)
            await event.client(EditBannedRequest(event.chat_id, uid, rights))
            await edit_safe(event, f"🔇 <b>Mute olundu:</b> <code>{uid}</code>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("block")))
    async def block(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}block</code> (reply/id/username)")
        try:
            await event.client(BlockRequest(uid))
            async with pool().acquire() as c:
                await c.execute("INSERT INTO blocks(user_id) VALUES($1) ON CONFLICT DO NOTHING", uid)
            await edit_safe(event, f"⛔️ <b>Bloklandı:</b> <code>{uid}</code>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unblock")))
    async def unblock(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}unblock</code>")
        try:
            await event.client(UnblockRequest(uid))
            async with pool().acquire() as c:
                await c.execute("DELETE FROM blocks WHERE user_id=$1", uid)
            await edit_safe(event, f"✅ <b>Blok açıldı:</b> <code>{uid}</code>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("info")))
    async def info(event):
        uid, ent = await get_target_user(event)
        if not ent:
            ent = await event.get_sender()
        full = await event.client.get_entity(ent.id)
        try:
            fu = await event.client(GetFullUserRequest(full.id))
            bio = fu.full_user.about or "—"
        except Exception:
            bio = "—"
        premium = "✅" if getattr(full, "premium", False) else "❌"
        text = (
            "👤 <b>İstifadəçi məlumatı</b>\n"
            "━━━━━━━━━━━━━━━\n"
            f"🪪 <b>Ad:</b> <b>{full.first_name or ''} {full.last_name or ''}</b>\n"
            f"🔗 <b>Username:</b> @{full.username or '—'}\n"
            f"🆔 <b>ID:</b> <code>{full.id}</code>\n"
            f"💬 <b>Bio:</b> <i>{bio}</i>\n"
            f"⭐ <b>Premium:</b> {premium}"
        )
        await edit_safe(event, text)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("tag")))
    async def tag(event):
        if not event.is_group:
            return await edit_safe(event, "⚠️ <b>Yalnız qruplarda işləyir.</b>")
        mode = (event.pattern_match.group(1).strip() or "mention").split()[0].lower()
        if mode not in {"mention","3","5","random"}:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}tag mention|3|5|random</code>")
        members = []
        async for u in event.client.iter_participants(event.chat_id, limit=500):
            if u.bot or u.deleted: continue
            members.append(u)
        if mode == "random":
            random.shuffle(members); members = members[:20]
        group_size = {"mention":1, "3":3, "5":5, "random":5}[mode]
        await event.delete()
        chunk = []
        sent = 0
        for u in members:
            chunk.append(f"<a href='tg://user?id={u.id}'>{u.first_name or 'user'}</a>")
            if len(chunk) >= group_size:
                try:
                    await event.client.send_message(event.chat_id, " ".join(chunk), parse_mode="html")
                    sent += 1
                    if sent % 5 == 0:
                        await asyncio.sleep(2)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                chunk = []
        if chunk:
            await event.client.send_message(event.chat_id, " ".join(chunk), parse_mode="html")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("setwelcome")))
    async def setwelcome(event):
        text = event.pattern_match.group(1).strip()
        if not text:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}setwelcome Salam {{mention}}, xoş gəldin</code>")
        async with pool().acquire() as c:
            await c.execute(
                "INSERT INTO welcomes(chat_id,message) VALUES($1,$2) "
                "ON CONFLICT(chat_id) DO UPDATE SET message=EXCLUDED.message",
                event.chat_id, text
            )
        await edit_safe(event, "✅ <b>Xoş gəldin mesajı qeyd edildi.</b>")

    @client.on(events.ChatAction())
    async def welcome_handler(event):
        if not event.user_added and not event.user_joined: return
        async with pool().acquire() as c:
            row = await c.fetchrow("SELECT message FROM welcomes WHERE chat_id=$1", event.chat_id)
        if not row: return
        try:
            user = await event.get_user()
            mention = f"<a href='tg://user?id={user.id}'>{user.first_name or 'dost'}</a>"
            msg = row["message"].replace("{mention}", mention).replace("{name}", user.first_name or "")
            await event.client.send_message(event.chat_id, msg, parse_mode="html")
        except Exception as e:
            log.warning("welcome err: %s", e)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("purge")))
    async def purge(event):
        arg = event.pattern_match.group(1).strip()
        try:
            me = await event.client.get_me()
            if event.is_reply:
                reply = await event.get_reply_message()
                ids = [m.id async for m in event.client.iter_messages(event.chat_id, min_id=reply.id-1)]
                count = len(ids)
            elif arg.isdigit():
                ids = [m.id async for m in event.client.iter_messages(event.chat_id, limit=int(arg))]
                count = len(ids)
            else:
                return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}purge 50</code> və ya reply")
            try:
                await event.client.delete_messages(event.chat_id, ids)
                await event.respond(f"🧹 <b>{count} mesaj silindi.</b>", parse_mode="html")
            except Exception:
                own = [i async for i, m in [(mm.id, mm) async for mm in event.client.iter_messages(event.chat_id, limit=200)] if m.sender_id == me.id]
                await event.client.delete_messages(event.chat_id, own)
                await event.respond(f"🧹 <b>Yetkim yoxdur, yalnız öz {len(own)} mesajım silindi.</b>", parse_mode="html")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("klon")))
    async def klon(event):
        uid, ent = await get_target_user(event)
        if not ent:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}klon</code> (reply və ya id)")
        await edit_safe(event, "🧬 <b>Klonlanır...</b>")
        me = await event.client.get_me()
        full_me = await event.client(GetFullUserRequest(me.id))
        photo_bytes = b""
        try:
            buf = io.BytesIO()
            await event.client.download_profile_photo("me", file=buf)
            photo_bytes = buf.getvalue()
        except Exception:
            pass
        async with pool().acquire() as c:
            await c.execute(
                "INSERT INTO klones(user_id,original_first,original_last,original_bio,original_photo) "
                "VALUES($1,$2,$3,$4,$5) ON CONFLICT(user_id) DO NOTHING",
                me.id, me.first_name or "", me.last_name or "",
                full_me.full_user.about or "", photo_bytes,
            )
        target_full = await event.client(GetFullUserRequest(ent.id))
        try:
            await event.client(UpdateProfileRequest(
                first_name=ent.first_name or "",
                last_name=ent.last_name or "",
                about=(target_full.full_user.about or "")[:70],
            ))
            buf = io.BytesIO()
            await event.client.download_profile_photo(ent.id, file=buf)
            buf.seek(0)
            if buf.getvalue():
                file = await event.client.upload_file(buf, file_name="klon.jpg")
                await event.client(UploadProfilePhotoRequest(file))
            await edit_safe(event, f"✅ <b>Klonlama tamamlandı:</b> <b>{ent.first_name}</b>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unklon")))
    async def unklon(event):
        me = await event.client.get_me()
        async with pool().acquire() as c:
            row = await c.fetchrow("SELECT * FROM klones WHERE user_id=$1", me.id)
        if not row:
            return await edit_safe(event, "ℹ️ <b>Klon məlumatı tapılmadı.</b>")
        try:
            await event.client(UpdateProfileRequest(
                first_name=row["original_first"] or "",
                last_name=row["original_last"] or "",
                about=row["original_bio"] or "",
            ))
            photos = await event.client(GetUserPhotosRequest(me.id, offset=0, max_id=0, limit=1))
            if photos.photos:
                await event.client(DeletePhotosRequest([photos.photos[0]]))
            if row["original_photo"]:
                buf = io.BytesIO(row["original_photo"])
                file = await event.client.upload_file(buf, file_name="orig.jpg")
                await event.client(UploadProfilePhotoRequest(file))
            async with pool().acquire() as c:
                await c.execute("DELETE FROM klones WHERE user_id=$1", me.id)
            await edit_safe(event, "✅ <b>Original profil geri qaytarıldı.</b>")
        except Exception as e:
            await edit_safe(event, f"❌ <b>Xəta:</b> {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("pinstall")))
    async def pinstall(event):
        if not event.is_reply:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}pinstall</code> əmrini .py faylına reply edin")
        reply = await event.get_reply_message()
        if not reply.document or not (reply.file and reply.file.name and reply.file.name.endswith(".py")):
            return await edit_safe(event, "❌ <b>.py faylı lazımdır!</b>")
        data = await reply.download_media(bytes)
        code = data.decode("utf-8", errors="replace")
        name = reply.file.name[:-3]
        ok, msg = await plugin_loader.install_plugin(name, code, event.client)
        if ok:
            commands = plugin_loader.extract_commands(code)
            notification = (
                f"📂 <b>Plugin '{name}' uğurla yükləndi!</b>\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"ℹ️ <b>Info:</b> {commands}"
            )
            await edit_safe(event, notification)
        else:
            await edit_safe(event, f"❌ <b>Xəta:</b> {msg}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unpinstall")))
    async def unpinstall(event):
        name = event.pattern_match.group(1).strip()
        if not name:
            return await edit_safe(event, f"ℹ️ <b>İstifadə:</b> <code>{P}unpinstall &lt;ad&gt;</code>")
        ok, msg = await plugin_loader.uninstall_plugin(name)
        await edit_safe(event, msg)

    log.info("🚀 Ryhavean Userbot bütün komandalar uğurla qeydiyyatdan keçdi.")
