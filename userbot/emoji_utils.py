"""
==================================================
🌌 Ryhavean Premium Emoji Utility v3
==================================================
Bütün send_message / edit_message / respond / reply / send_file
metodlarına class-level monkey-patch tətbiq edir.
.pinstall ilə yüklənən pluginlər də avtomatik premium emoji göstərir.
==================================================
"""
import re
import random
from telethon import TelegramClient
from telethon.tl.custom import Message
from telethon.tl.types import (
    MessageEntityCustomEmoji,
    MessageEntityTextUrl,
)
from telethon.extensions import html as tl_html

# ============================================================
# Premium Emoji ID Map (150+ emoji)
# ============================================================
PREMIUM_EMOJI_MAP = {
    # Music / Audio
    "🎵": 5244489483159609086,
    "🎶": 5411371652921435502,
    "🎧": 5363988860747400777,
    "🎤": 5188534946971357056,
    "🎼": 5247200526806083584,
    "🎷": 5224774246105601256,
    "🎸": 5188377706580342082,
    "🥁": 5224774246105601256,
    # Status / Actions
    "✅": 5237699328843200968,
    "❌": 5237803726629079638,
    "⚠️": 5237794650988008052,
    "ℹ️": 5237926954068725838,
    "✔": 5237699328843200968,
    "❎": 5237803726629079638,
    "⛔": 5237803726629079638,
    "🚫": 5237803726629079638,
    "🆗": 5237699328843200968,
    "🆘": 5237803726629079638,
    # Hearts
    "❤️": 5237800551539573619,
    "💖": 5237800551539573619,
    "💕": 5237800551539573619,
    "💗": 5237800551539573619,
    "💓": 5237800551539573619,
    "💝": 5237800551539573619,
    "💘": 5237800551539573619,
    "🧡": 5237800551539573619,
    "💛": 5237800551539573619,
    "💚": 5237800551539573619,
    "💙": 5237800551539573619,
    "💜": 5237800551539573619,
    "🖤": 5237800551539573619,
    "🤍": 5237800551539573619,
    "🤎": 5237800551539573619,
    # Faces
    "😀": 5404870795943391909,
    "😁": 5404870795943391909,
    "😂": 5443055575834826266,
    "🤣": 5443055575834826266,
    "😃": 5404870795943391909,
    "😄": 5404870795943391909,
    "😅": 5404870795943391909,
    "😆": 5404870795943391909,
    "😉": 5404870795943391909,
    "😊": 5404870795943391909,
    "😍": 5237800551539573619,
    "🥰": 5237800551539573619,
    "😎": 5188377706580342082,
    "🤩": 5237800551539573619,
    "🥳": 5237800551539573619,
    "😢": 5237794650988008052,
    "😭": 5237794650988008052,
    "😡": 5237803726629079638,
    "🤬": 5237803726629079638,
    "🥶": 5237794650988008052,
    "😱": 5237803726629079638,
    "🤔": 5237926954068725838,
    "🙄": 5237926954068725838,
    "😴": 5404870795943391909,
    "😈": 5237803726629079638,
    "👿": 5237803726629079638,
    "👻": 5237794650988008052,
    "💀": 5237803726629079638,
    "☠️": 5237803726629079638,
    "🤖": 5188377706580342082,
    "👽": 5188377706580342082,
    "👾": 5188377706580342082,
    # Hands & people
    "👍": 5237699328843200968,
    "👎": 5237803726629079638,
    "👏": 5237699328843200968,
    "🙌": 5237699328843200968,
    "🤝": 5237699328843200968,
    "💪": 5237699328843200968,
    "🙏": 5237926954068725838,
    "✊": 5237699328843200968,
    "👊": 5237699328843200968,
    "✌️": 5237699328843200968,
    "🤞": 5237699328843200968,
    "🤟": 5237699328843200968,
    "🤘": 5237699328843200968,
    "👌": 5237699328843200968,
    "👋": 5237699328843200968,
    # Symbols
    "⭐": 5188534946971357056,
    "🌟": 5188534946971357056,
    "✨": 5188534946971357056,
    "💫": 5188534946971357056,
    "🔥": 5443055575834826266,
    "💧": 5188377706580342082,
    "💦": 5188377706580342082,
    "☀️": 5188534946971357056,
    "🌙": 5247200526806083584,
    "⚡": 5443055575834826266,
    "❄️": 5188377706580342082,
    "🌈": 5188534946971357056,
    "☁️": 5247200526806083584,
    # Objects / Tools
    "💎": 5188534946971357056,
    "👑": 5188534946971357056,
    "🎁": 5237800551539573619,
    "🎉": 5237699328843200968,
    "🎊": 5237699328843200968,
    "🎈": 5237699328843200968,
    "💰": 5188534946971357056,
    "💵": 5188534946971357056,
    "💸": 5188534946971357056,
    "💳": 5188534946971357056,
    "🪙": 5188534946971357056,
    # Tech / Comm
    "📱": 5188377706580342082,
    "💻": 5188377706580342082,
    "⌨️": 5188377706580342082,
    "🖥️": 5188377706580342082,
    "🖱️": 5188377706580342082,
    "📷": 5188377706580342082,
    "📸": 5188377706580342082,
    "🎥": 5188377706580342082,
    "📹": 5188377706580342082,
    "📺": 5188377706580342082,
    "📡": 5188377706580342082,
    "🔋": 5188377706580342082,
    "🔌": 5188377706580342082,
    "📞": 5188377706580342082,
    "☎️": 5188377706580342082,
    "📧": 5188377706580342082,
    "📨": 5188377706580342082,
    "📩": 5188377706580342082,
    "📬": 5188377706580342082,
    "📮": 5188377706580342082,
    # Navigation
    "➡️": 5188377706580342082,
    "⬅️": 5188377706580342082,
    "⬆️": 5188377706580342082,
    "⬇️": 5188377706580342082,
    "↗️": 5188377706580342082,
    "↘️": 5188377706580342082,
    "↙️": 5188377706580342082,
    "↖️": 5188377706580342082,
    "🔄": 5188377706580342082,
    "🔁": 5188377706580342082,
    "🔂": 5188377706580342082,
    # Tools / Settings
    "⚙️": 5188377706580342082,
    "🛠️": 5188377706580342082,
    "🔧": 5188377706580342082,
    "🔨": 5188377706580342082,
    "🔒": 5188377706580342082,
    "🔓": 5188377706580342082,
    "🔑": 5188377706580342082,
    "🗝️": 5188377706580342082,
    # Files / Docs
    "📁": 5188377706580342082,
    "📂": 5188377706580342082,
    "📄": 5188377706580342082,
    "📃": 5188377706580342082,
    "📑": 5188377706580342082,
    "📊": 5188377706580342082,
    "📈": 5188377706580342082,
    "📉": 5188377706580342082,
    "🗂️": 5188377706580342082,
    "📋": 5188377706580342082,
    "📝": 5188377706580342082,
    "✏️": 5188377706580342082,
    "🖊️": 5188377706580342082,
    "🖋️": 5188377706580342082,
    # Misc
    "🌍": 5188377706580342082,
    "🌎": 5188377706580342082,
    "🌏": 5188377706580342082,
    "🗺️": 5188377706580342082,
    "🧭": 5188377706580342082,
    "⏰": 5188377706580342082,
    "⏱️": 5188377706580342082,
    "⏲️": 5188377706580342082,
    "🕐": 5188377706580342082,
    "📅": 5188377706580342082,
    "📆": 5188377706580342082,
    "🗓️": 5188377706580342082,
}

# .song üçün random premium emoji ID'lər
SONG_PREMIUM_EMOJI_IDS = [
    5244489483159609086,  # 🎵
    5411371652921435502,  # 🎶
    5363988860747400777,  # 🎧
]
SONG_EMOJI_CHAR = ["🎵", "🎶", "🎧"]


# ============================================================
# Premium Emoji konvertasiya alqoritmi
# ============================================================
def _build_premium_text_and_entities(text: str):
    """
    Mətndəki standart emojiləri tapır və MessageEntityCustomEmoji entity'ləri yaradır.
    Telegram'a göndərilərkən premium emoji kimi göstərilir.
    """
    if not text:
        return text, []

    entities = []
    # Regex: bütün məlumatdakı emojiləri (uzunluq görə sıralanmış) tap
    sorted_emojis = sorted(PREMIUM_EMOJI_MAP.keys(), key=len, reverse=True)
    pattern = "|".join(re.escape(e) for e in sorted_emojis)
    if not pattern:
        return text, []

    # UTF-16 offset hesablamaq üçün
    utf16_text = text.encode("utf-16-le")

    def utf16_len(s):
        return len(s.encode("utf-16-le")) // 2

    new_entities = []
    for m in re.finditer(pattern, text):
        emoji_char = m.group(0)
        emoji_id = PREMIUM_EMOJI_MAP.get(emoji_char)
        if not emoji_id:
            continue
        offset = utf16_len(text[: m.start()])
        length = utf16_len(emoji_char)
        new_entities.append(
            MessageEntityCustomEmoji(
                offset=offset,
                length=length,
                document_id=emoji_id,
            )
        )

    return text, new_entities


def apply_premium_emojis(text, existing_entities=None):
    """Mətn üçün premium emoji entity'lərini hazırlayır."""
    if not text:
        return text, existing_entities or []
    new_text, new_ents = _build_premium_text_and_entities(text)
    if existing_entities:
        return new_text, list(existing_entities) + new_ents
    return new_text, new_ents


def song_caption():
    """
    .song mahnı yükləndikdə random premium emoji + 'Ryhavean Download' caption qaytarır.
    """
    idx = random.randint(0, len(SONG_PREMIUM_EMOJI_IDS) - 1)
    emoji_char = SONG_EMOJI_CHAR[idx]
    emoji_id = SONG_PREMIUM_EMOJI_IDS[idx]
    text = f"{emoji_char} Ryhavean Download"
    # UTF-16 offset = 0, length = utf16 emoji ölçüsü
    length = len(emoji_char.encode("utf-16-le")) // 2
    entities = [
        MessageEntityCustomEmoji(
            offset=0,
            length=length,
            document_id=emoji_id,
        )
    ]
    return text, entities


# ============================================================
# CLASS-LEVEL MONKEY PATCH
# .pinstall ilə yüklənən pluginlər də bu patch'dən istifadə edir
# ============================================================
_original_send_message = TelegramClient.send_message
_original_edit_message = TelegramClient.edit_message
_original_send_file = TelegramClient.send_file


async def _patched_send_message(self, entity, message=None, *args, **kwargs):
    if isinstance(message, str):
        new_text, new_ents = apply_premium_emojis(message, kwargs.get("formatting_entities"))
        if new_ents:
            kwargs["formatting_entities"] = new_ents
            # parse_mode olmamalıdır ki, entity'lər prioritet alsın
            kwargs["parse_mode"] = None
            message = new_text
    return await _original_send_message(self, entity, message, *args, **kwargs)


async def _patched_edit_message(self, entity, message=None, text=None, *args, **kwargs):
    target_text = text
    if isinstance(target_text, str):
        new_text, new_ents = apply_premium_emojis(target_text, kwargs.get("formatting_entities"))
        if new_ents:
            kwargs["formatting_entities"] = new_ents
            kwargs["parse_mode"] = None
            text = new_text
    return await _original_edit_message(self, entity, message, text, *args, **kwargs)


async def _patched_send_file(self, entity, file, *args, **kwargs):
    caption = kwargs.get("caption")
    if isinstance(caption, str):
        new_text, new_ents = apply_premium_emojis(caption, kwargs.get("formatting_entities"))
        if new_ents:
            kwargs["formatting_entities"] = new_ents
            kwargs["parse_mode"] = None
            kwargs["caption"] = new_text
    return await _original_send_file(self, entity, file, *args, **kwargs)


_original_message_edit = Message.edit
_original_message_respond = Message.respond
_original_message_reply = Message.reply


async def _patched_message_edit(self, text=None, *args, **kwargs):
    if isinstance(text, str):
        new_text, new_ents = apply_premium_emojis(text, kwargs.get("formatting_entities"))
        if new_ents:
            kwargs["formatting_entities"] = new_ents
            kwargs["parse_mode"] = None
            text = new_text
    return await _original_message_edit(self, text, *args, **kwargs)


async def _patched_message_respond(self, message=None, *args, **kwargs):
    if isinstance(message, str):
        new_text, new_ents = apply_premium_emojis(message, kwargs.get("formatting_entities"))
        if new_ents:
            kwargs["formatting_entities"] = new_ents
            kwargs["parse_mode"] = None
            message = new_text
    return await _original_message_respond(self, message, *args, **kwargs)


async def _patched_message_reply(self, message=None, *args, **kwargs):
    if isinstance(message, str):
        new_text, new_ents = apply_premium_emojis(message, kwargs.get("formatting_entities"))
        if new_ents:
            kwargs["formatting_entities"] = new_ents
            kwargs["parse_mode"] = None
            message = new_text
    return await _original_message_reply(self, message, *args, **kwargs)


# ... (yuxarıdakı kodlar olduğu kimi qalır)

def install_patches():
    """Class-level patch tətbiq edir. main.py'da əvvəlcə çağırılmalıdır."""
    TelegramClient.send_message = _patched_send_message
    TelegramClient.edit_message = _patched_edit_message
    TelegramClient.send_file = _patched_send_file
    Message.edit = _patched_message_edit
    Message.respond = _patched_message_respond
    Message.reply = _patched_message_reply

# 👇 BU HİSSƏNİ MÜTLƏQ ƏLAVƏ ET:
def vip_format(text: str, auto_bold: bool = True) -> str:
    """commands.py-in axtardığı funksiya"""
    text, _ = apply_premium_emojis(text)
    return text

# Avtomatik tətbiq
install_patches()
