"""
==================================================
🤖 DİNAMİK PLUGIN YÜKLƏMƏ SİSTEMİ - RYHAVEAN
==================================================
"""

import importlib.util
import sys
import traceback
import logging
import re
import asyncio
from pathlib import Path
from security import analyze_plugin
from db import pool

log = logging.getLogger("plugins")
PLUGIN_DIR = Path(__file__).parent / "plugins"
PLUGIN_DIR.mkdir(exist_ok=True)

loaded: dict[str, object] = {}

def preprocess_code(code: str) -> str:
    code = re.sub(r'from userbot\..* import .*\n', '', code)
    code = re.sub(r'from userbot import .*\n', '', code)
    code = re.sub(r'Help\s*=\s*CmdHelp\(.*\)', '', code)
    code = re.sub(r'Help\..*', '', code)
    code = re.sub(r'@register\(.*pattern=(.*)\)', r'@client.on(events.NewMessage(pattern=\1))', code)
    code = code.replace("brend", "event")
    return code

def extract_commands(code: str) -> str:
    patterns = [
        r'pattern=r"\^\\\.([\w]+)"',
        r'pattern="\^\.([\w]+)"',
        r'pattern=r"\.([\w]+)"',
        r'pattern="\.\.([\w]+)"'
    ]
    
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, code))
        
    if not matches:
        return "<i>Komanda tapılmadı</i>"
    
    unique_matches = sorted(list(set(matches)))
    return ", ".join([f"<code>.{cmd}</code>" for cmd in unique_matches])

def format_message(text: str) -> str:
    """
    HTML teqlərini olan mesajları format edir.
    emoji_utils import etmədən sadə format qaytarır.
    """
    return text

async def install_plugin(name: str, code: str, client) -> tuple[bool, str]:
    processed_code = preprocess_code(code)
    
    safe, reason = analyze_plugin(processed_code)
    if not safe:
        return False, f"❌ Təhlükəsizlik xətası (Plugin: <code>{name}</code>): {reason}"
    
    path = PLUGIN_DIR / f"{name}.py"
    
    # Əgər plugin artıq varsa, əvvəlcə sil
    if path.exists():
        log.info(f"Plugin artıq mövcuddur, yenidən yüklənir: {name}")
        await uninstall_plugin(name)
    
    path.write_text(processed_code, encoding="utf-8")
    
    try:
        await _load_one(path, client, notify=False)
    except Exception as e:
        log.error(f"Plugin yükləmə xətası {name}: {e}")
        path.unlink(missing_ok=True)
        return False, f"❌ Yükləmə xətası (Plugin: <code>{name}</code>): {e}"
    
    async with pool().acquire() as c:
        await c.execute(
            "INSERT INTO plugins(name,code) VALUES($1,$2) "
            "ON CONFLICT(name) DO UPDATE SET code=EXCLUDED.code", name, processed_code
        )
    
    log.info(f"✅ Plugin uğurla yükləndi: {name}")
    return True, f"✅ Plugin '<u>{name}</u>' uğurla yükləndi və aktivləşdirildi!"

async def uninstall_plugin(name: str) -> tuple[bool, str]:
    """Plugin-i sistemdən tamamilə silir"""
    path = PLUGIN_DIR / f"{name}.py"
    mod_name = f"plugins.{name}"
    
    # 1. Module-u sys.modules-dan sil
    if mod_name in sys.modules:
        del sys.modules[mod_name]
        log.info(f"Module silindi: {mod_name}")
    
    # 2. Loaded dict-dən sil
    if name in loaded:
        loaded.pop(name, None)
        log.info(f"Loaded dict-dən silindi: {name}")
    
    # 3. Faylı disk-dən sil
    if path.exists():
        try:
            path.unlink()
            log.info(f"Fayl silindi: {path}")
        except Exception as e:
            log.error(f"Fayl silinə bilmədi {path}: {e}")
    
    # 4. Database-dən sil
    try:
        async with pool().acquire() as c:
            result = await c.execute("DELETE FROM plugins WHERE name=$1", name)
            log.info(f"Database-dən silindi: {name} (rows: {result})")
    except Exception as e:
        log.error(f"Database silmə xətası {name}: {e}")
    
    log.info(f"🗑 Plugin tamamilə silindi: {name}")
    return True, f"🗑 Plugin '<u>{name}</u>' sistemdən tamamilə silindi."

async def _load_one(path: Path, client, notify=False):
    name = path.stem
    spec = importlib.util.spec_from_file_location(f"plugins.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    mod.client = client
    from telethon import events
    mod.events = events
    
    try:
        spec.loader.exec_module(mod)
        
        # ƏLAVƏ ETDİYİNİZ HİSSƏ BURADIR:
        if hasattr(mod, "register"):
            try:
                mod.register(client)
                log.info(f"Plugin register() ilə aktivləşdirildi: {name}")
            except Exception as e:
                log.error(f"Plugin register() xətası {name}: {e}")
        
        # Mövcud sətir:
        loaded[name] = mod
        log.info(f"Plugin uğurla yükləndi: {name}")

    except Exception as e:
        err = traceback.format_exc()
        log.error(f"Plugin xətası {name}: {err}")
        if notify:
            try:
                error_msg = f"⚠️ Plugin xətası: <code>{name}</code>\n\n<code>{err[:3000]}</code>"
                await client.send_message("me", error_msg, parse_mode="html")
            except Exception:
                pass
        raise e

async def load_all(client):
    """Bütün pluginləri yükləyir"""
    try:
        async with pool().acquire() as c:
            rows = await c.fetch("SELECT name, code FROM plugins")
        
        for r in rows:
            p = PLUGIN_DIR / f"{r['name']}.py"
            p.write_text(r["code"], encoding="utf-8")
        
        for p in PLUGIN_DIR.glob("*.py"):
            if p.name.startswith("_"):
                continue
            try:
                await _load_one(p, client, notify=False)
            except Exception as e:
                log.error(f"Plugin yüklənmədi {p.name}: {e}")
                
        log.info(f"✅ {len(loaded)} plugin yükləndi")
    except Exception as e:
        log.error(f"Plugin load_all xətası: {e}")
