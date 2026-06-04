"""Dinamik plugin yükləmə sistemi"""
import importlib.util
import sys
import traceback
import logging
import re
from pathlib import Path
from security import analyze_plugin
from db import pool

log = logging.getLogger("plugins")
PLUGIN_DIR = Path(__file__).parent / "plugins"
PLUGIN_DIR.mkdir(exist_ok=True)

loaded: dict[str, object] = {}

# Kodu təmizləyən və client-ə uyğunlaşdıran funksiya
def preprocess_code(code: str) -> str:
    # 1. userbot importlarını sil
    code = re.sub(r'from userbot\..* import .*\n', '', code)
    code = re.sub(r'from userbot import .*\n', '', code)
    # 2. CmdHelp və Help obyektlərini sil
    code = re.sub(r'Help\s*=\s*CmdHelp\(.*\)', '', code)
    code = re.sub(r'Help\..*', '', code)
    # 3. register dekoratorlarını client.on ilə əvəz et
    code = re.sub(r'@register\(.*pattern=(.*)\)', r'@client.on(events.NewMessage(pattern=\1))', code)
    # 4. 'brend' və ya digər funksiya adlarını 'event' ilə dəyiş (ümumi çevirmə)
    code = code.replace("brend", "event")
    return code

# Pluginin içindən bütün mümkün komanda strukturlarını tapırıq
def extract_commands(code: str) -> str:
    # Bu regex həm pattern=r"^\.komanda", həm də pattern=r"^\.komanda$" formatlarını dəstəkləyir
    matches = re.findall(r'pattern=r"\^\\\.([\w]+)', code)
    
    # Əgər yuxarıdakı tapmasa, sadə pattern formatlarını yoxlayır
    if not matches:
        matches = re.findall(r'pattern="\^\.([\w]+)', code)
        
    if not matches:
        return "Komanda tapılmadı"
    
    # Unikal komandaları siyahıya alır
    unique_matches = sorted(list(set(matches)))
    return ", ".join([f".{cmd}" for cmd in unique_matches])

async def install_plugin(name: str, code: str, client) -> tuple[bool, str]:
    # Kodu bazaya yazmazdan əvvəl avtomatik təmizləyirik
    processed_code = preprocess_code(code)
    
    safe, reason = analyze_plugin(processed_code)
    if not safe:
        return False, f"❌ Təhlükəsizlik: {reason}"
    
    path = PLUGIN_DIR / f"{name}.py"
    path.write_text(processed_code, encoding="utf-8")
    
    try:
        await _load_one(path, client)
    except Exception as e:
        path.unlink(missing_ok=True)
        return False, f"❌ Yükləmə xətası: {e}"
    
    # Komandaları avtomatik çıxarırıq
    commands = extract_commands(processed_code)
    
    # İstədiyiniz formatda bildiriş
    notification = (
        f"📂 <b>Plugin adı {name} Modulu Yükləndi!</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"ℹ️ <b>Info:</b> {commands}"
    )
    await client.send_message("me", notification, parse_mode="html")
    
    async with pool().acquire() as c:
        await c.execute(
            "INSERT INTO plugins(name,code) VALUES($1,$2) "
            "ON CONFLICT(name) DO UPDATE SET code=EXCLUDED.code", name, processed_code
        )
    return True, f"✅ <b>{name}</b> plugini quruldu"

async def uninstall_plugin(name: str) -> tuple[bool, str]:
    path = PLUGIN_DIR / f"{name}.py"
    mod_name = f"plugins.{name}"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    loaded.pop(name, None)
    path.unlink(missing_ok=True)
    async with pool().acquire() as c:
        await c.execute("DELETE FROM plugins WHERE name=$1", name)
    return True, f"🗑 <b>{name}</b> plugini silindi"

async def _load_one(path: Path, client):
    name = path.stem
    spec = importlib.util.spec_from_file_location(f"plugins.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    # Pluginə client obyektini ötürürük
    mod.client = client
    # Events-i modula əlavə edirik ki, çalışa bilsin
    from telethon import events
    mod.events = events
    try:
        spec.loader.exec_module(mod)
        loaded[name] = mod
        log.info("Plugin yükləndi: %s", name)
    except Exception:
        err = traceback.format_exc()
        log.error("Plugin xətası %s: %s", name, err)
        try:
            await client.send_message("me", f"⚠️ Plugin xətası <b>{name}</b>:\n<code>{err[:3000]}</code>", parse_mode="html")
        except Exception:
            pass

async def load_all(client):
    async with pool().acquire() as c:
        rows = await c.fetch("SELECT name, code FROM plugins")
    for r in rows:
        p = PLUGIN_DIR / f"{r['name']}.py"
        p.write_text(r["code"], encoding="utf-8")
    for p in PLUGIN_DIR.glob("*.py"):
        if p.name.startswith("_"):
            continue
        await _load_one(p, client)
