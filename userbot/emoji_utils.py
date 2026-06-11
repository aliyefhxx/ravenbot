"""
==================================================
💎  EMOJİ SİSTEMİ - RYHAVEAN (PREMIUM AUTO-HOOK)
==================================================
Bu modul import edilən kimi Telethon'un göndərmə / redaktə
metodlarına monkey-patch tətbiq edir. Beləliklə həm
`commands.py` daxilindəki, həm də sonradan `.pinstall` ilə
yüklənən bütün pluginlərdə yazılan adi emojilər avtomatik
olaraq premium emojilərə çevrilir.

Qeyd: Premium emojilərin görünməsi üçün userbot hesabı
TELEGRAM PREMIUM olmalıdır.
"""

import re
import logging
from telethon import TelegramClient
from telethon.tl.custom.message import Message

log = logging.getLogger("emoji_utils")

# ---------------------------------------------------------------
# 1) PREMIUM EMOJİ TABLOSU
# ---------------------------------------------------------------
PREMIUM_EMOJI_MAP = {
    "✨": "<emoji id=5316742794562254812>✨</emoji>",
    "✅": "<emoji id=5368741096031552953>✅</emoji>",
    "❌": "<emoji id=5262564492247592066>❌</emoji>",
    "⚡": "<emoji id=5411590687663608498>⚡</emoji>",
    "🚀": "<emoji id=5276424673834317384>🚀</emoji>",
    "🔨": "<emoji id=5384341452337720965>🔨</emoji>",
    "🛡": "<emoji id=5406935230877542714>🛡</emoji>",
    "♻️": "<emoji id=5911100572508885928>♻️</emoji>",
    "📚": "<emoji id=5357479219335012900>📚</emoji>",
    "🔌": "<emoji id=5289939608769929229>🔌</emoji>",
    "👤": "<emoji id=5373012449597335010>👤</emoji>",
    "🧬": "<emoji id=5217444336089714383>🧬</emoji>",
    "🔇": "<emoji id=5462990730253319917>🔇</emoji>",
    "⛔": "<emoji id=5258483856704544199>⛔</emoji>",
    "🪪": "<emoji id=5260561650213220533>🪪</emoji>",
    "🔗": "<emoji id=5201989772448381592>🔗</emoji>",
    "🆔": "<emoji id=5314250708508964241>🆔</emoji>",
    "💬": "<emoji id=5449459513096690896>💬</emoji>",
    "⭐": "<emoji id=5370600589237427906>⭐</emoji>",
    "⚠️": "<emoji id=6172475875368373616>⚠️</emoji>",
    "ℹ️": "<emoji id=5213452215527677338>ℹ️</emoji>",
    "🧹": "<emoji id=5235929467309796721>🧹</emoji>",
    "🗑": "<emoji id=5408832111773757273>🗑</emoji>",
    "📂": "<emoji id=5298853345241358103>📂</emoji>",
    "🏓": "<emoji id=5269563867305879894>🏓</emoji>",
    "🤖": "<emoji id=5237689785425877860>🤖</emoji>",
    "🟢": "<emoji id=5280863578369311403>🟢</emoji>",
    "⏳": "<emoji id=5296482716567495148>⏳</emoji>",
    "🥷": "<emoji id=5210868290187970813>🥷</emoji>",
    # Genişləndirilmiş / qanlı tematika
    "🔥": "<emoji id=5346260403856840475>🔥</emoji>",
    "🩸": "<emoji id=5350305691942888204>🩸</emoji>",
    "💀": "<emoji id=5210956306952758910>💀</emoji>",
    "🖼": "<emoji id=5306579270208242518>🖼</emoji>",
    "📸": "<emoji id=5350452584119279096>📸</emoji>",
    "🎯": "<emoji id=5210956306952758910>🎯</emoji>",
    "💎": "<emoji id=5471968904413515493>💎</emoji>",
    "👁": "<emoji id=5253262503525564449>👁</emoji>",
    "⚙️": "<emoji id=5443038326535759644>⚙️</emoji>",
    "📌": "<emoji id=5872968317553708353>📌</emoji>",
    "🕒": "<emoji id=5407025001346491904>🕒</emoji>",
    "📥": "<emoji id=5237800551036498416>📥</emoji>",
    "📤": "<emoji id=5226751417158775865>📤</emoji>",
    "❤️": "<emoji id=5377320148950722062>❤️</emoji>",
    "💜": "<emoji id=5377491595400165457>💜</emoji>",
    "💛": "<emoji id=5350474846170971916>💛</emoji>",
    "🧠": "<emoji id=5253262503525564449>🧠</emoji>",
}

# Premium emoji tag pattern - artıq çevrilmiş emojiləri qoruyuruq
_ALREADY_PREMIUM_RE = re.compile(
    r"<emoji\s+id=\d+>.*?</emoji>", re.IGNORECASE | re.DOTALL
)
# HTML tag pattern
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def apply_premium_emojis(text: str) -> str:
    """
    Mətndəki bütün adi emojiləri premium emojilərə çevirir.
    Artıq <emoji id=...>...</emoji> ilə wrap olunmuş hissələrə
    toxunmur (ikiqat çevrilmənin qarşısını alır).
    """
    if not text or not isinstance(text, str):
        return text

    # Artıq wrap olunmuş emoji blokarını placeholder ilə əvəz et
    placeholders: list[str] = []

    def _stash(match):
        placeholders.append(match.group(0))
        return f"\x00PREMOJI{len(placeholders) - 1}\x00"

    safe = _ALREADY_PREMIUM_RE.sub(_stash, text)

    # Adi emojiləri premium ilə əvəz et
    for std, prem in PREMIUM_EMOJI_MAP.items():
        if std in safe:
            safe = safe.replace(std, prem)

    # Placeholderları geri qaytar
    def _restore(match):
        idx = int(match.group(1))
        return placeholders[idx]

    return re.sub(r"\x00PREMOJI(\d+)\x00", _restore, safe)


def vip_format(text: str, auto_bold: bool = True) -> str:
    """
    VIP formatı: Əvvəlcə bold edirik, sonra emojiləri premium ilə əvəz edirik.
    """
    if not text:
        return text

    result = text
    if auto_bold:
        lines = result.split("\n")
        bold_lines = []
        for line in lines:
            s = line.strip()
            # HTML tagı ilə başlayan sətirləri bold-a sarımırıq
            if s and not s.startswith("<"):
                bold_lines.append(f"<b>{line}</b>")
            else:
                bold_lines.append(line)
        result = "\n".join(bold_lines)

    return apply_premium_emojis(result)


# ---------------------------------------------------------------
# 2) AVTOMATIK MONKEY-PATCH (bütün pluginlər üçün)
# ---------------------------------------------------------------
# Bütün send_message / edit_message / reply / respond / send_file
# çağırışlarında mətn (message / text / caption / file caption) avtomatik
# olaraq premium emojilər ilə əvəz olunur və parse_mode="html" təyin edilir
# (yalnız mətn dəyişərsə və istifadəçi parse_mode verməyibsə).

_PATCH_FLAG = "_ryhavean_premium_patched"


def _convert_arg(value):
    """Mətn argumentini premium emojilər ilə yenidən qurur."""
    if isinstance(value, str):
        return apply_premium_emojis(value)
    return value


def _wrap(method, text_arg_name: str = "message"):
    """
    Telethon metodlarını sarıyır.
    text_arg_name - mətn üçün istifadə olunan kwarg adı
    ('message' send_message üçün, 'text' edit_message üçün,
    'caption' send_file üçün).
    """

    async def wrapper(self, *args, **kwargs):
        changed = False

        # kwargs içində mətn
        if text_arg_name in kwargs and isinstance(kwargs[text_arg_name], str):
            new_val = apply_premium_emojis(kwargs[text_arg_name])
            if new_val != kwargs[text_arg_name]:
                kwargs[text_arg_name] = new_val
                changed = True

        # caption üçün ayrıca (send_file həm caption ola bilər)
        if "caption" in kwargs and isinstance(kwargs["caption"], str):
            new_val = apply_premium_emojis(kwargs["caption"])
            if new_val != kwargs["caption"]:
                kwargs["caption"] = new_val
                changed = True

        # positional - args[1] adətən mətn olur (entity, message, ...)
        if len(args) >= 2 and isinstance(args[1], str):
            new_val = apply_premium_emojis(args[1])
            if new_val != args[1]:
                args = (args[0], new_val) + tuple(args[2:])
                changed = True
        # edit_message-də signature dəyişkəndir; args[2] mətn ola bilər
        elif len(args) >= 3 and isinstance(args[2], str):
            new_val = apply_premium_emojis(args[2])
            if new_val != args[2]:
                args = (args[0], args[1], new_val) + tuple(args[3:])
                changed = True

        # parse_mode-u yalnız mətn faktiki dəyişdikdə təyin et
        if changed and "parse_mode" not in kwargs:
            kwargs["parse_mode"] = "html"

        return await method(self, *args, **kwargs)

    wrapper.__wrapped__ = method
    return wrapper


def _wrap_message_method(method, text_arg_name: str = "text"):
    """Message.edit / reply / respond üçün."""

    async def wrapper(self, *args, **kwargs):
        changed = False

        if text_arg_name in kwargs and isinstance(kwargs[text_arg_name], str):
            new_val = apply_premium_emojis(kwargs[text_arg_name])
            if new_val != kwargs[text_arg_name]:
                kwargs[text_arg_name] = new_val
                changed = True

        if "caption" in kwargs and isinstance(kwargs["caption"], str):
            new_val = apply_premium_emojis(kwargs["caption"])
            if new_val != kwargs["caption"]:
                kwargs["caption"] = new_val
                changed = True

        if args and isinstance(args[0], str):
            new_val = apply_premium_emojis(args[0])
            if new_val != args[0]:
                args = (new_val,) + tuple(args[1:])
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
        TelegramClient.send_message = _wrap(TelegramClient.send_message, "message")
        TelegramClient.edit_message = _wrap(TelegramClient.edit_message, "text")
        TelegramClient.send_file = _wrap(TelegramClient.send_file, "caption")

        Message.edit = _wrap_message_method(Message.edit, "text")
        Message.reply = _wrap_message_method(Message.reply, "text")
        Message.respond = _wrap_message_method(Message.respond, "text")

        setattr(TelegramClient, _PATCH_FLAG, True)
        log.info("💎 Premium emoji auto-patch tətbiq olundu (client + Message).")
    except Exception as e:
        log.warning("Premium emoji patch tətbiq olunmadı: %s", e)


# Modul import edilən kimi patch tətbiq olunur
_install_patches()
