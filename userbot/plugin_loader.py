"""
==================================================
🤖 DİNAMİK PLUGIN YÜKLƏMƏ SİSTEMİ - RYHAVEAN (PREMIUM EMOJI ENABLED)
==================================================
"""

import importlib.util
import sys
import traceback
import logging
import re
import asyncio
import random
from pathlib import Path
from telethon import events, functions, types
from telethon.tl.types import MessageEntityCustomEmoji
from security import analyze_plugin
from db import pool

log = logging.getLogger("plugins")
PLUGIN_DIR = Path(__file__).parent / "plugins"
PLUGIN_DIR.mkdir(exist_ok=True)

loaded: dict[str, object] = {}
premium_emojis = []

# Premium emoji paketlərindən ID-ləri çəkən funksiya
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

# Mesaj göndərmə sistemini "patch" edirik
def patch_client(client):
    original_send_message = client.send_message

    async def send_message_patched(entity, message, **kwargs):
        if isinstance(message, str) and premium_emojis:
            # Unicode emojiləri tapır
            emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]')
            matches = list(emoji_pattern.finditer(message))
            
            if matches:
                entities = kwargs.get('formatting_entities') or []
                # Mesajı görünməz boşluqla zənginləşdiririk
                for match in matches:
                    entities.append(MessageEntityCustomEmoji(
                        offset=match.start(),
                        length=1,
                        document_id=random.choice(premium_emojis)
                    ))
                kwargs['formatting_entities'] = entities
                # Adi emojini boşluqla əvəz et ki, vizual olaraq sadəcə premium görünsün
                message = emoji_pattern.sub(" ", message)
        
        return await original_send_message(entity, message, **kwargs)

    client.send_message = send_message_patched

def preprocess_code(code: str) -> str:
    code = re.sub(r'from userbot\..* import .*\n', '', code)
    code = re.sub(r'from userbot import .*\n', '', code)
    code = re.sub(r'Help\s*=\s*CmdHelp\(.*\)', '', code)
    code = re.sub(r'Help\..*', '', code)
    code = re.sub(r'@register\(.*pattern=(.*)\)', r'@client.on(events.NewMessage(pattern=\1))', code)
    code = code.replace("brend", "event")
    return code

def extract_commands(code: str) -> str:
    patterns = [r'pattern=r"\^\\\.([\w]+)"', r'pattern="\^\.([\w]+)"', r'pattern=r"\.([\w]+)"', r'pattern="\.\.([\w]+)"']
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, code))
    if not matches: return "<i>Komanda tapılmadı</i>"
    unique_matches = sorted(list(set(matches)))
    return ", ".join([f"<code>.{cmd}</code>" for cmd in unique_matches])

async def install_plugin(name: str, code: str, client) -> tuple[bool, str]:
    processed_code = preprocess_code(code)
    safe, reason = analyze_plugin(processed_code)
    if not safe: return False, f"❌ <b>Təhlükəsizlik xətası (Plugin: <code>{name}</code>):</b> {reason}"
    
    path = PLUGIN_DIR / f"{name}.py"
    path.write_text(processed_code, encoding="utf-8")
    
    try:
        await _load_one(path, client, notify=False)
    except Exception as e:
        path.unlink(missing_ok=True)
        return False, f"❌ <b>Yükləmə xətası (Plugin: <code>{name}</code>):</b> {e}"
    
    async with pool().acquire() as c:
        await c.execute("INSERT INTO plugins(name,code) VALUES($1,$2) ON CONFLICT(name) DO UPDATE SET code=EXCLUDED.code", name, processed_code)
    return True, f"✅ <b>Plugin '<u>{name}</u>' uğurla yükləndi və aktivləşdirildi!</b>"

async def uninstall_plugin(name: str) -> tuple[bool, str]:
    path = PLUGIN_DIR / f"{name}.py"
    mod_name = f"plugins.{name}"
    if mod_name in sys.modules: del sys.modules[mod_name]
    loaded.pop(name, None)
    path.unlink(missing_ok=True)
    async with pool().acquire() as c:
        await c.execute("DELETE FROM plugins WHERE name=$1", name)
    return True, f"🗑 <b>Plugin '<u>{name}</u>' sistemdən silindi.</b>"

async def _load_one(path: Path, client, notify=False):
    name = path.stem
    spec = importlib.util.spec_from_file_location(f"plugins.{name}", path)
    mod = importlib.module_from_spec(spec)
    mod.client = client
    mod.events = events
    try:
        spec.loader.exec_module(mod)
        loaded[name] = mod
        log.info("Plugin uğurla yükləndi: %s", name)
    except Exception:
        err = traceback.format_exc()
        log.error("Plugin xətası %s: %s", name, err)
        if notify:
            try: await client.send_message("me", f"⚠️ <b>Plugin xətası:</b> <code>{name}</code>\n\n<code>{err[:3000]}</code>", parse_mode="html")
            except: pass

async def load_all(client):
    patch_client(client)
    await update_premium_emojis(client)
    async with pool().acquire() as c:
        rows = await c.fetch("SELECT name, code FROM plugins")
    for r in rows:
        p = PLUGIN_DIR / f"{r['name']}.py"
        p.write_text(r["code"], encoding="utf-8")
    for p in PLUGIN_DIR.glob("*.py"):
        if p.name.startswith("_"): continue
        await _load_one(p, client, notify=False)
