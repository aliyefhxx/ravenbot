"""
==================================================
💎  EMOJİ SİSTEMİ - RYHAVEAN (PREMIUM AUTO-HOOK v2)
==================================================
Genişləndirilmiş premium emoji xəritəsi + bütün
göndərmə/redaktə metodları üçün monkey-patch.
Plugin və commands.py-də adi emoji yazsan da
avtomatik premium emoji ilə əvəzlənir.

QEYD: Premium emojilərin görünməsi üçün userbot
hesabı TELEGRAM PREMIUM olmalıdır.
"""

import re
import logging
from telethon import TelegramClient
from telethon.tl.custom.message import Message

log = logging.getLogger("emoji_utils")

# ---------------------------------------------------------------
# 1) PREMIUM EMOJİ XƏRİTƏSİ (genişləndirilmiş)
# ---------------------------------------------------------------
PREMIUM_EMOJI_MAP = {
    # Status
    "✨": "<emoji id=5316742794562254812>✨</emoji>",
    "✅": "<emoji id=5368741096031552953>✅</emoji>",
    "❌": "<emoji id=5262564492247592066>❌</emoji>",
    "⚠️": "<emoji id=6172475875368373616>⚠️</emoji>",
    "ℹ️": "<emoji id=5213452215527677338>ℹ️</emoji>",
    "⛔": "<emoji id=5258483856704544199>⛔</emoji>",
    "🟢": "<emoji id=5280863578369311403>🟢</emoji>",
    "🔴": "<emoji id=5384541201116429014>🔴</emoji>",
    "🟡": "<emoji id=5267693896723595821>🟡</emoji>",

    # Action / system
    "⚡": "<emoji id=5411590687663608498>⚡</emoji>",
    "🚀": "<emoji id=5276424673834317384>🚀</emoji>",
    "🔨": "<emoji id=5384341452337720965>🔨</emoji>",
    "🛡": "<emoji id=5406935230877542714>🛡</emoji>",
    "🛡️": "<emoji id=5406935230877542714>🛡️</emoji>",
    "♻️": "<emoji id=5911100572508885928>♻️</emoji>",
    "📚": "<emoji id=5357479219335012900>📚</emoji>",
    "🔌": "<emoji id=5289939608769929229>🔌</emoji>",
    "🔇": "<emoji id=5462990730253319917>🔇</emoji>",
    "🔊": "<emoji id=5443070674757946385>🔊</emoji>",
    "🪪": "<emoji id=5260561650213220533>🪪</emoji>",
    "🔗": "<emoji id=5201989772448381592>🔗</emoji>",
    "🆔": "<emoji id=5314250708508964241>🆔</emoji>",
    "🧹": "<emoji id=5235929467309796721>🧹</emoji>",
    "🗑": "<emoji id=5408832111773757273>🗑</emoji>",
    "🗑️": "<emoji id=5408832111773757273>🗑️</emoji>",
    "📂": "<emoji id=5298853345241358103>📂</emoji>",
    "📌": "<emoji id=5301196558363485286>📌</emoji>",
    "📍": "<emoji id=5305015666747367210>📍</emoji>",
    "💾": "<emoji id=5251076002595108882>💾</emoji>",
    "📜": "<emoji id=5224700827206113090>📜</emoji>",
    "📖": "<emoji id=5357479219335012900>📖</emoji>",
    "📝": "<emoji id=5283102004126237179>📝</emoji>",
    "🔢": "<emoji id=5226915377489567989>🔢</emoji>",
    "🧮": "<emoji id=5283102004126237179>🧮</emoji>",
    "🌐": "<emoji id=5263634036681963773>🌐</emoji>",

    # User / chat
    "👤": "<emoji id=5373012449597335010>👤</emoji>",
    "👥": "<emoji id=5325985556672861764>👥</emoji>",
    "👮": "<emoji id=5325985556672861764>👮</emoji>",
    "💬": "<emoji id=5449459513096690896>💬</emoji>",
    "🤖": "<emoji id=5237689785425877860>🤖</emoji>",
    "🥷": "<emoji id=5210868290187970813>🥷</emoji>",
    "🧠": "<emoji id=5253262503525564449>🧠</emoji>",

    # Time / pong
    "⏳": "<emoji id=5296482716567495148>⏳</emoji>",
    "⏱": "<emoji id=5296482716567495148>⏱</emoji>",
    "🕒": "<emoji id=5296482716567495148>🕒</emoji>",
    "🏓": "<emoji id=5269563867305879894>🏓</emoji>",

    # Fun / theme
    "🔥": "<emoji id=5346260403856840475>🔥</emoji>",
    "🩸": "<emoji id=5350305691942888204>🩸</emoji>",
    "💀": "<emoji id=5210956306952758910>💀</emoji>",
    "🌌": "<emoji id=5316742794562254812>🌌</emoji>",
    "🎯": "<emoji id=5210956306952758910>🎯</emoji>",
    "💎": "<emoji id=5316742794562254812>💎</emoji>",
    "⭐": "<emoji id=5370600589237427906>⭐</emoji>",

    # Hearts
    "❤️": "<emoji id=5443070674757946385>❤️</emoji>",
    "🤍": "<emoji id=5377491595400165457>🤍</emoji>",
    "💖": "<emoji id=5443070674757946385>💖</emoji>",
    "💞": "<emoji id=5443070674757946385>💞</emoji>",
    "💕": "<emoji id=5443070674757946385>💕</emoji>",
    "💜": "<emoji id=5377491595400165457>💜</emoji>",
    "💛": "<emoji id=5350474846170971916>💛</emoji>",

    # Media
    "🎧": "<emoji id=5350452584119279096>🎧</emoji>",
    "🎵": "<emoji id=5350452584119279096>🎵</emoji>",
    "🎶": "<emoji id=5350452584119279096>🎶</emoji>",
    "🎬": "<emoji id=5306579270208242518>🎬</emoji>",
    "🖼": "<emoji id=5306579270208242518>🖼</emoji>",
    "🖼️": "<emoji id=5306579270208242518>🖼️</emoji>",
    "📸": "<emoji id=5350452584119279096>📸</emoji>",
    "📷": "<emoji id=5350452584119279096>📷</emoji>",
    "🔳": "<emoji id=5350452584119279096>🔳</emoji>",

    # Games & dice
    "🎲": "<emoji id=5346260403856840475>🎲</emoji>",
    "🎱": "<emoji id=5346260403856840475>🎱</emoji>",
    "🪙": "<emoji id=5346260403856840475>🪙</emoji>",
    "🎳": "<emoji id=5346260403856840475>🎳</emoji>",
    "🏀": "<emoji id=5346260403856840475>🏀</emoji>",
    "⚽": "<emoji id=5346260403856840475>⚽</emoji>",
    "🎰": "<emoji id=5346260403856840475>🎰</emoji>",

    # Feelings / fun
    "😂": "<emoji id=5346260403856840475>😂</emoji>",
    "😍": "<emoji id=5443070674757946385>😍</emoji>",
    "🤔": "<emoji id=5253262503525564449>🤔</emoji>",
    "💤": "<emoji id=5296482716567495148>💤</emoji>",
    "🌞": "<emoji id=5267693896723595821>🌞</emoji>",
    "🌫": "<emoji id=5267693896723595821>🌫</emoji>",
    "🍀": "<emoji id=5267693896723595821>🍀</emoji>",
    "🏳️‍🌈": "<emoji id=5377491595400165457>🏳️‍🌈</emoji>",

    # Misc info
    "🌦": "<emoji id=5263634036681963773>🌦</emoji>",
    "🧪": "<emoji id=5263634036681963773>🧪</emoji>",
    "💰": "<emoji id=5350474846170971916>💰</emoji>",
    "💻": "<emoji id=5237689785425877860>💻</emoji>",
    "🧬": "<emoji id=5217444336089714383>🧬</emoji>",
}

_ALREADY_PREMIUM_RE = re.compile(
    r"<emoji\s+id=\d+>.*?</emoji>", re.IGNORECASE | re.DOTALL
)


def apply_premium_emojis(text):
    if not text or not isinstance(text, str):
        return text
    placeholders: list[str] = []

    def _stash(match):
        placeholders.append(match.group(0))
        return f"\x00PREMOJI{len(placeholders) - 1}\x00"

    safe = _ALREADY_PREMIUM_RE.sub(_stash, text)
    for std, prem in PREMIUM_EMOJI_MAP.items():
        if std in safe:
            safe = safe.replace(std, prem)

    def _restore(match):
        idx = int(match.group(1))
        return placeholders[idx]

    return re.sub(r"\x00PREMOJI(\d+)\x00", _restore, safe)


def vip_format(text: str, auto_bold: bool = True) -> str:
    if not text:
        return text
    result = text
    if auto_bold:
        lines = result.split("\n")
        bold_lines = []
        for line in lines:
            s = line.strip()
            if s and not s.startswith("<"):
                bold_lines.append(f"<b>{line}</b>")
            else:
                bold_lines.append(line)
        result = "\n".join(bold_lines)
    return apply_premium_emojis(result)


# ---------------------------------------------------------------
# 2) AVTOMATIK MONKEY-PATCH
# ---------------------------------------------------------------
_PATCH_FLAG = "_ryhavean_premium_patched"


def _maybe_convert(value):
    if isinstance(value, str):
        new_v = apply_premium_emojis(value)
        return new_v, new_v != value
    return value, False


def _wrap_client(method, text_kw: str):
    async def wrapper(self, *args, **kwargs):
        changed = False
        if text_kw in kwargs and isinstance(kwargs[text_kw], str):
            v, c = _maybe_convert(kwargs[text_kw])
            kwargs[text_kw] = v
            changed |= c
        if "caption" in kwargs and isinstance(kwargs["caption"], str):
            v, c = _maybe_convert(kwargs["caption"])
            kwargs["caption"] = v
            changed |= c
        # send_message(entity, text) / edit_message(entity, message, text)
        if len(args) >= 2 and isinstance(args[1], str):
            v, c = _maybe_convert(args[1])
            if c:
                args = (args[0], v) + tuple(args[2:])
                changed = True
        elif len(args) >= 3 and isinstance(args[2], str):
            v, c = _maybe_convert(args[2])
            if c:
                args = (args[0], args[1], v) + tuple(args[3:])
                changed = True
        if changed and "parse_mode" not in kwargs:
            kwargs["parse_mode"] = "html"
        return await method(self, *args, **kwargs)
    wrapper.__wrapped__ = method
    return wrapper


def _wrap_message(method, text_kw: str = "text"):
    async def wrapper(self, *args, **kwargs):
        changed = False
        if text_kw in kwargs and isinstance(kwargs[text_kw], str):
            v, c = _maybe_convert(kwargs[text_kw])
            kwargs[text_kw] = v
            changed |= c
        # bəzi metodlarda message kwarg ilə də gəlir
        if "message" in kwargs and isinstance(kwargs["message"], str):
            v, c = _maybe_convert(kwargs["message"])
            kwargs["message"] = v
            changed |= c
        if "caption" in kwargs and isinstance(kwargs["caption"], str):
            v, c = _maybe_convert(kwargs["caption"])
            kwargs["caption"] = v
            changed |= c
        if args and isinstance(args[0], str):
            v, c = _maybe_convert(args[0])
            if c:
                args = (v,) + tuple(args[1:])
                changed = True
        if changed and "parse_mode" not in kwargs:
            kwargs["parse_mode"] = "html"
        return await method(self, *args, **kwargs)
    wrapper.__wrapped__ = method
    return wrapper


def _install_patches():
    if getattr(TelegramClient, _PATCH_FLAG, False):
        return
    try:
        TelegramClient.send_message = _wrap_client(TelegramClient.send_message, "message")
        TelegramClient.edit_message = _wrap_client(TelegramClient.edit_message, "text")
        TelegramClient.send_file = _wrap_client(TelegramClient.send_file, "caption")

        Message.edit = _wrap_message(Message.edit, "text")
        Message.reply = _wrap_message(Message.reply, "text")
        Message.respond = _wrap_message(Message.respond, "text")

        setattr(TelegramClient, _PATCH_FLAG, True)
        log.info("💎 Premium emoji auto-patch tətbiq olundu.")
    except Exception as e:
        log.warning("Premium emoji patch tətbiq olunmadı: %s", e)


_install_patches()
