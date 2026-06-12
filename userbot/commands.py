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
        await edit_safe(event, "⏳ Çox sürətli! Bir az gözləyin.")
    return ok

async def get_target_user(event):
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
        if not await rl_check(event, "alive"):
            return
        msg = await get_setting("alive_msg") or (
            "✨ Ryhavean Userbot aktivdir\n"
            "━━━━━━━━━━━━━━━\n"
            "🤖 Sistem: <code>online</code>\n"
            "⚡ Versiya: <code>1.0.0</code>\n"
            "🛡 Təhlükəsizlik: <code>aktiv</code>"
        )
        await edit_safe(event, msg)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("dlive")))
    async def dlive(event):
        new = event.pattern_match.group(1).strip()
        if not new:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}dlive yeni mesaj</code>")
        await set_setting("alive_msg", new)
        await edit_safe(event, "✅ Alive mesajı yeniləndi.")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("restart")))
    async def restart(event):
        await edit_safe(event, "♻️ Restart edilir...")
        await set_setting("restart_chat", str(event.chat_id))
        await set_setting("restart_msg", str(event.id))
        os.execv(sys.executable, [sys.executable, *sys.argv])

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("help")))
    async def help_cmd(event):
        plugins = list(plugin_loader.loaded.keys())
        text = (
            "Ryhavean Userbot 🇬🇪\n"
            "━━━━━━━━━━━━━━━\n"
            "🛡 İdarəetmə:\n"
            "<code>.alive</code> | <code>.dlive</code> | <code>.restart</code>\n\n"
            "🔨 Moderasiya:\n"
            "<code>.ban</code> | <code>.unban</code> | <code>.mute</code> | <code>.block</code> | <code>.unblock</code>\n\n"
            "👤 İstifadəçi & Qrup:\n"
            "<code>.info</code> | <code>.tag</code> | <code>.setwelcome</code>\n\n"
            "🧬 Profil Klonlama:\n"
            "<code>.klon</code> | <code>.unklon</code>\n\n"
            "🔌 Plugin İdarəetmə:\n"
            "<code>.pinstall</code> | <code>.unpinstall</code>\n"
            "━━━━━━━━━━━━━━━\n"
            f"🔌 Yüklü Pluginlər ({len(plugins)}):\n"
            f"{', '.join(plugins) if plugins else 'Yoxdur'}"
        )
        await edit_safe(event, text)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("ban")))
    async def ban(event):
        uid, ent = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}ban</code> (reply) və ya <code>{P}ban @user</code>")
        try:
            rights = ChatBannedRights(until_date=None, view_messages=True)
            await event.client(EditBannedRequest(event.chat_id, uid, rights))
            await edit_safe(event, f"🔨 Ban olundu: <code>{uid}</code>")
        except (ChatAdminRequiredError, UserAdminInvalidError):
            await edit_safe(event, "⚠️ Yetkiniz yoxdur.")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unban")))
    async def unban(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}unban @user</code>")
        try:
            rights = ChatBannedRights(until_date=None, view_messages=False)
            await event.client(EditBannedRequest(event.chat_id, uid, rights))
            await edit_safe(event, f"✅ Ban açıldı: <code>{uid}</code>")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("mute")))
    async def mute(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}mute</code> (reply/id/username)")
        try:
            rights = ChatBannedRights(until_date=None, send_messages=True)
            await event.client(EditBannedRequest(event.chat_id, uid, rights))
            await edit_safe(event, f"🔇 Mute olundu: <code>{uid}</code>")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("block")))
    async def block(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}block</code> (reply/id/username)")
        try:
            await event.client(BlockRequest(uid))
            async with pool().acquire() as c:
                await c.execute("INSERT INTO blocks(user_id) VALUES($1) ON CONFLICT DO NOTHING", uid)
            await edit_safe(event, f"⛔ Bloklandı: <code>{uid}</code>")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unblock")))
    async def unblock(event):
        uid, _ = await get_target_user(event)
        if not uid:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}unblock</code>")
        try:
            await event.client(UnblockRequest(uid))
            async with pool().acquire() as c:
                await c.execute("DELETE FROM blocks WHERE user_id=$1", uid)
            await edit_safe(event, f"✅ Blok açıldı: <code>{uid}</code>")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

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
            "👤 İstifadəçi məlumatı\n"
            "━━━━━━━━━━━━━━━\n"
            f"🪪 Ad: {full.first_name or ''} {full.last_name or ''}\n"
            f"🔗 Username: @{full.username or '—'}\n"
            f"🆔 ID: <code>{full.id}</code>\n"
            f"💬 Bio: <i>{bio}</i>\n"
            f"⭐ Premium: {premium}"
        )
        await edit_safe(event, text)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("tag")))
    async def tag(event):
        if not event.is_group:
            return await edit_safe(event, "⚠️ Yalnız qruplarda işləyir.")
        mode = (event.pattern_match.group(1).strip() or "mention").split()[0].lower()
        if mode not in {"mention", "3", "5", "random"}:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}tag mention|3|5|random</code>")
        
        members = []
        async for u in event.client.iter_participants(event.chat_id, limit=500):
            if u.bot or u.deleted:
                continue
            members.append(u)
        
        if mode == "random":
            random.shuffle(members)
            members = members[:20]
        
        group_size = {"mention": 1, "3": 3, "5": 5, "random": 5}[mode]
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
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}setwelcome Salam {{mention}}, xoş gəldin</code>")
        async with pool().acquire() as c:
            await c.execute(
                "INSERT INTO welcomes(chat_id,message) VALUES($1,$2) "
                "ON CONFLICT(chat_id) DO UPDATE SET message=EXCLUDED.message",
                event.chat_id, text
            )
        await edit_safe(event, "✅ Xoş gəldin mesajı qeyd edildi.")

    @client.on(events.ChatAction())
    async def welcome_handler(event):
        if not event.user_added and not event.user_joined:
            return
        async with pool().acquire() as c:
            row = await c.fetchrow("SELECT message FROM welcomes WHERE chat_id=$1", event.chat_id)
        if not row:
            return
        try:
            user = await event.get_user()
            mention = f"<a href='tg://user?id={user.id}'>{user.first_name or 'dost'}</a>"
            msg = row["message"].replace("{mention}", mention).replace("{name}", user.first_name or "")
            await event.client.send_message(event.chat_id, msg, parse_mode="html")
        except Exception as e:
            log.warning("welcome err: %s", e)

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("klon")))
    async def klon(event):
        uid, ent = await get_target_user(event)
        if not ent:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}klon</code> (reply və ya id)")
        await edit_safe(event, "🧬 Klonlanır...")
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
            await edit_safe(event, f"✅ Klonlama tamamlandı: {ent.first_name}")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unklon")))
    async def unklon(event):
        me = await event.client.get_me()
        async with pool().acquire() as c:
            row = await c.fetchrow("SELECT * FROM klones WHERE user_id=$1", me.id)
        if not row:
            return await edit_safe(event, "ℹ️ Klon məlumatı tapılmadı.")
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
            await edit_safe(event, "✅ Original profil geri qaytarıldı.")
        except FloodWaitError as e:
            await edit_safe(event, f"⏳ FloodWait: {e.seconds} saniyə gözləyin")
        except Exception as e:
            await edit_safe(event, f"❌ Xəta: {e}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("pinstall")))
    async def pinstall(event):
        if not event.is_reply:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}pinstall</code> əmrini .py faylına reply edin")
        reply = await event.get_reply_message()
        if not reply.document or not (reply.file and reply.file.name and reply.file.name.endswith(".py")):
            return await edit_safe(event, "❌ .py faylı lazımdır!")
        data = await reply.download_media(bytes)
        code = data.decode("utf-8", errors="replace")
        name = reply.file.name[:-3]
        ok, msg = await plugin_loader.install_plugin(name, code, event.client)
        if ok:
            commands = plugin_loader.extract_commands(code)
            notification = (
                f"📂 Plugin '<u>{name}</u>' uğurla yükləndi!\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"ℹ️ Info: {commands}"
            )
            await edit_safe(event, notification)
        else:
            await edit_safe(event, f"❌ Xəta: {msg}")

    @client.on(events.NewMessage(outgoing=True, pattern=cmd_re("unpinstall")))
    async def unpinstall(event):
        name = event.pattern_match.group(1).strip()
        if not name:
            return await edit_safe(event, f"ℹ️ İstifadə: <code>{P}unpinstall &lt;ad&gt;</code>")
        ok, msg = await plugin_loader.uninstall_plugin(name)
        await edit_safe(event, msg)

    log.info("🚀 Ryhavean Userbot bütün komandalar uğurla qeydiyyatdan keçdi.")
