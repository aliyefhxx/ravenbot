"""
emoji_utils.py — Premium Emoji dəstəyi (Ryhavean Userbot)
=========================================================
Bu modul:
  • Bütün adi emojiləri Telegram Premium Custom Emoji ID-lərinə çevirir.
  • TelegramClient (send_message, edit_message, send_file) və
    Message (respond, reply, edit) metodlarını GLOBAL monkey-patch edir.
  • .pinstall ilə endirilən pluginlərdə də avtomatik işləyir, çünki
    patch yalnız hər instansa deyil, **class səviyyəsində** tətbiq olunur.
  • Custom HTML parser (PremiumHTMLParser) Telethon-un parse_mode
    məhdudiyyətini aşaraq MessageEntityCustomEmoji generasiya edir.

İstifadə:
    from emoji_utils import install_premium_emojis
    install_premium_emojis()        # main.py-də userbot başlamazdan əvvəl
"""

from __future__ import annotations
import re
import random
from html import escape as html_escape
from html.parser import HTMLParser as _StdHTMLParser

from telethon import TelegramClient
from telethon.tl.custom import Message
from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityTextUrl
from telethon.extensions import html as tl_html

# ──────────────────────────────────────────────────────────────────────────
# 1. EMOJI → PREMIUM ID xəritəsi
# ──────────────────────────────────────────────────────────────────────────
PREMIUM_EMOJI_MAP: dict[str, int] = {
    # ✅ / ❌ / ⚠️
    "✅": 5237699328843200968,
    "❌": 5210956306952758910,
    "⚠️": 5260683494091866126,
    "⛔": 5237946060664813722,
    "🚫": 5237755760383408500,
    # ⭐ / 🌟 / ✨
    "⭐": 5269174946921015998,
    "🌟": 5260573582032744451,
    "✨": 5267389078512345863,
    "💫": 5260533238362068636,
    # 🔥 / 💥 / ⚡
    "🔥": 5260575112617681492,
    "💥": 5260745285577883628,
    "⚡": 5263946349224909046,
    # 🎵 / 🎶 / 🎧 / 🎤 / 🎼
    "🎵": 5244489483159609086,
    "🎶": 5411371652921435502,
    "🎧": 5363988860747400777,
    "🎤": 5260628176856953568,
    "🎼": 5267389078512345863,
    # ❤️ / 💙 / 💚 / 💛 / 🧡 / 💜 / 🖤 / 🤍 / 🤎 / ♥️
    "❤️": 5237677599715337115,
    "♥️": 5237677599715337115,
    "💙": 5237762629171183910,
    "💚": 5237753341991182236,
    "💛": 5237699557408022762,
    "🧡": 5237764602494801471,
    "💜": 5237699557408022762,
    "🖤": 5237689247405382669,
    "🤍": 5237679223947569354,
    "🤎": 5237750010701706750,
    "💖": 5237679223947569354,
    "💗": 5237679223947569354,
    "💘": 5237679223947569354,
    "💕": 5237699557408022762,
    "💞": 5237679223947569354,
    # 👍 / 👎 / 👌 / 👏 / 🙌 / 🤝 / ✊ / ✋ / 🤙 / 🫶
    "👍": 5269174946921015998,
    "👎": 5210956306952758910,
    "👌": 5237753341991182236,
    "👏": 5237699557408022762,
    "🙌": 5237699557408022762,
    "🤝": 5237699557408022762,
    "✊": 5260575112617681492,
    "✋": 5237677599715337115,
    "🤙": 5237677599715337115,
    "🫶": 5237679223947569354,
    # 😀 😁 😂 🤣 😃 😄 😅 😆 😉 😊 😋
    "😀": 5260573582032744451,
    "😁": 5260573582032744451,
    "😂": 5260628176856953568,
    "🤣": 5260628176856953568,
    "😃": 5260573582032744451,
    "😄": 5260573582032744451,
    "😅": 5260573582032744451,
    "😆": 5260628176856953568,
    "😉": 5260573582032744451,
    "😊": 5260573582032744451,
    "😋": 5260573582032744451,
    # 😎 😍 🥰 😘 😗 😙 😚 🙂 🤗 🤩
    "😎": 5260573582032744451,
    "😍": 5237679223947569354,
    "🥰": 5237679223947569354,
    "😘": 5237679223947569354,
    "🤩": 5269174946921015998,
    "🤗": 5260573582032744451,
    # 🤔 🤨 😐 😑 😶 🙄 😏 😣 😥 😮 🤐 😯 😪 😫 🥱 😴
    "🤔": 5260628176856953568,
    "🤨": 5260628176856953568,
    "😐": 5260628176856953568,
    "🙄": 5260628176856953568,
    "😏": 5260628176856953568,
    "😴": 5260628176856953568,
    # 😢 😭 😤 😠 😡 🤬 🤯 😳 🥵 🥶 😱 😨 😰 😥 😓
    "😢": 5260628176856953568,
    "😭": 5260628176856953568,
    "😡": 5210956306952758910,
    "🤬": 5210956306952758910,
    "🤯": 5260745285577883628,
    "😱": 5260745285577883628,
    # 🤤 😈 👿 💀 ☠️ 👻 👽 🤖 👾
    "💀": 5237689247405382669,
    "👻": 5260573582032744451,
    "🤖": 5260573582032744451,
    "👽": 5260573582032744451,
    # 🌹 🌸 🌺 🌻 🌷 💐 🌼
    "🌹": 5237677599715337115,
    "🌸": 5237679223947569354,
    "🌺": 5237679223947569354,
    "🌻": 5237699557408022762,
    "🌷": 5237679223947569354,
    "💐": 5237679223947569354,
    # 🎉 🎊 🎁 🎂 🎈 🎀
    "🎉": 5269174946921015998,
    "🎊": 5269174946921015998,
    "🎁": 5237679223947569354,
    "🎂": 5237679223947569354,
    "🎈": 5237679223947569354,
    # 📌 📍 📎 ✏️ ✒️ 🖊️ 🖋️ 📝 📄 📃 📑 📊 📈 📉
    "📌": 5260575112617681492,
    "📝": 5260628176856953568,
    "📊": 5260628176856953568,
    "📈": 5237753341991182236,
    "📉": 5210956306952758910,
    # 🔔 🔕 📢 📣 📯 🔊 🔉 🔈 🔇
    "🔔": 5260628176856953568,
    "🔕": 5260628176856953568,
    "📢": 5260628176856953568,
    # 🔒 🔓 🔐 🔑 🗝️
    "🔒": 5260575112617681492,
    "🔓": 5237753341991182236,
    "🔑": 5269174946921015998,
    # 🛠️ ⚙️ 🔧 🔨 ⛏️ 🪓 🔩 🧰
    "🛠️": 5260628176856953568,
    "⚙️": 5260628176856953568,
    "🔧": 5260628176856953568,
    # 🤖 / bot / dev
    "💻": 5260628176856953568,
    "🖥️": 5260628176856953568,
    "📱": 5260628176856953568,
    "⌨️": 5260628176856953568,
    "🖱️": 5260628176856953568,
    # arrows
    "➡️": 5260628176856953568,
    "⬅️": 5260628176856953568,
    "⬆️": 5260628176856953568,
    "⬇️": 5260628176856953568,
    "↗️": 5260628176856953568,
    "↘️": 5260628176856953568,
    "🔄": 5260628176856953568,
    "🔃": 5260628176856953568,
    "▶️": 5237753341991182236,
    "◀️": 5237753341991182236,
    "⏸️": 5260628176856953568,
    "⏹️": 5210956306952758910,
    # i/info
    "ℹ️": 5260628176856953568,
    "❓": 5260628176856953568,
    "❔": 5260628176856953568,
    "❕": 5260628176856953568,
    "‼️": 5210956306952758910,
    "⁉️": 5260628176856953568,
    # ⏳ ⌛ ⏰ ⏱️ ⏲️ 🕐
    "⏳": 5260628176856953568,
    "⌛": 5260628176856953568,
    "⏰": 5260628176856953568,
    # 🌍 🌎 🌏 🌐 🗺️
    "🌍": 5260628176856953568,
    "🌎": 5260628176856953568,
    "🌏": 5260628176856953568,
    "🌐": 5260628176856953568,
    # weather
    "☀️": 5269174946921015998,
    "🌙": 5260628176856953568,
    "☁️": 5260628176856953568,
    "🌧️": 5260628176856953568,
    "⛅": 5260628176856953568,
    # food / drink
    "☕": 5260628176856953568,
    "🍺": 5260628176856953568,
    "🍻": 5260628176856953568,
    # misc
    "📸": 5260628176856953568,
    "📷": 5260628176856953568,
    "🎬": 5260628176856953568,
    "🎮": 5260628176856953568,
    "🎯": 5260575112617681492,
    "🏆": 5269174946921015998,
    "🥇": 5269174946921015998,
    "🥈": 5260628176856953568,
    "🥉": 5237750010701706750,
    "💎": 5237762629171183910,
    "💰": 5237699557408022762,
    "💵": 5237753341991182236,
    "💸": 5237753341991182236,
    "🛒": 5260628176856953568,
}

# .song üçün xüsusi premium emoji ID-ləri (random seçilir)
SONG_PREMIUM_EMOJI_IDS = [
    5244489483159609086,
    5411371652921435502,
    5363988860747400777,
]

def get_random_song_emoji_id() -> int:
    """`.song` üçün random premium emoji ID qaytarır."""
    return random.choice(SONG_PREMIUM_EMOJI_IDS)

def song_caption() -> str:
    """`.song` üçün caption HTML qaytarır — random premium emoji + 'Ryhavean Download'."""
    eid = get_random_song_emoji_id()
    # 🎵 yer tutucu — Telethon parser onu MessageEntityCustomEmoji-yə çevirəcək
    return f'<emoji id="{eid}">🎵</emoji> <b>Ryhavean Download</b>'


# ──────────────────────────────────────────────────────────────────────────
# 2. Premium HTML Parser (Telethon parse_mode replacement)
# ──────────────────────────────────────────────────────────────────────────
_EMOJI_TAG_RE = re.compile(
    r'<emoji\s+id\s*=\s*["\']?(\d+)["\']?\s*>(.*?)</emoji>',
    re.IGNORECASE | re.DOTALL,
)

class PremiumHTMLParser:
    """
    Telethon parse_mode interface — `<emoji id="...">X</emoji>` taglarını
    MessageEntityCustomEmoji-yə çevirir.

    İşləmə prinsipi:
      1. `<emoji id=N>X</emoji>` → `<a href="tg://emoji?id=N">X</a>`
      2. Standart Telethon HTML parseri MessageEntityTextUrl üretir
      3. `tg://emoji?id=N` URL-li entity-lər MessageEntityCustomEmoji-yə çevrilir
    """

    @staticmethod
    def parse(text: str):
        if not text:
            return text, []

        # <emoji id=N>X</emoji> → <a href="tg://emoji?id=N">X</a>
        def _to_anchor(m):
            eid = m.group(1)
            inner = m.group(2)
            return f'<a href="tg://emoji?id={eid}">{inner}</a>'

        converted = _EMOJI_TAG_RE.sub(_to_anchor, text)

        # Telethon-un standart HTML parserindən istifadə
        msg, entities = tl_html.parse(converted)

        # MessageEntityTextUrl(tg://emoji?id=N) → MessageEntityCustomEmoji
        new_entities = []
        for e in entities:
            if isinstance(e, MessageEntityTextUrl) and e.url.startswith("tg://emoji?id="):
                try:
                    eid = int(e.url.split("=", 1)[1])
                    new_entities.append(MessageEntityCustomEmoji(
                        offset=e.offset, length=e.length, document_id=eid
                    ))
                    continue
                except (ValueError, IndexError):
                    pass
            new_entities.append(e)

        return msg, new_entities

    @staticmethod
    def unparse(text: str, entities):
        if not entities:
            return tl_html.unparse(text, entities)

        # CustomEmoji → anchor (Telethon unparse onları emal edə bilsin)
        converted_entities = []
        for e in entities:
            if isinstance(e, MessageEntityCustomEmoji):
                converted_entities.append(MessageEntityTextUrl(
                    offset=e.offset, length=e.length,
                    url=f"tg://emoji?id={e.document_id}",
                ))
            else:
                converted_entities.append(e)
        return tl_html.unparse(text, converted_entities)


# ──────────────────────────────────────────────────────────────────────────
# 3. Mətni Premium-laşdırma
# ──────────────────────────────────────────────────────────────────────────
def apply_premium_emojis(text: str) -> str:
    """
    Mətndəki bütün adi emojiləri `<emoji id="...">X</emoji>` tag-ı ilə əvəzləyir.
    Əgər mətndə artıq `<emoji ...>` tag-ı varsa, ona toxunmur.
    """
    if not text or not isinstance(text, str):
        return text

    # Artıq <emoji> tag-larını qoruyaq — onları placeholder ilə əvəz edib sonda geri qaytarırıq
    placeholders: list[str] = []
    def _stash(m):
        placeholders.append(m.group(0))
        return f"\x00PREMOJI{len(placeholders)-1}\x00"

    safe = _EMOJI_TAG_RE.sub(_stash, text)

    # Indi adi emojiləri çevirək (uzun-dan qısa, çünki ❤️ kimi multi-codepoint var)
    for emoji in sorted(PREMIUM_EMOJI_MAP.keys(), key=len, reverse=True):
        if emoji in safe:
            eid = PREMIUM_EMOJI_MAP[emoji]
            safe = safe.replace(emoji, f'<emoji id="{eid}">{emoji}</emoji>')

    # Placeholders-ı geri qaytar
    def _restore(m):
        idx = int(m.group(1))
        return placeholders[idx]
    safe = re.sub(r"\x00PREMOJI(\d+)\x00", _restore, safe)
    return safe


# ──────────────────────────────────────────────────────────────────────────
# 4. GLOBAL MONKEY-PATCH (TelegramClient + Message CLASS səviyyəsində)
# ──────────────────────────────────────────────────────────────────────────
_PATCHED = False

def install_premium_emojis() -> None:
    """
    TelegramClient və Message metodlarını GLOBAL şəkildə patch edir.
    Bu funksiya userbot başlamazdan ÖNCƏ çağırılmalıdır — bundan sonra
    .pinstall ilə endirilən bütün pluginlərdə avtomatik işləyəcək, çünki
    patch class səviyyəsindədir, yeni instance yaratmaq tələb olunmur.
    """
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    _orig_send_message = TelegramClient.send_message
    _orig_edit_message = TelegramClient.edit_message
    _orig_send_file = TelegramClient.send_file
    _orig_msg_respond = Message.respond
    _orig_msg_reply = Message.reply
    _orig_msg_edit = Message.edit

    def _inject(kwargs: dict) -> dict:
        """parse_mode-u PremiumHTMLParser-ə dəyiş və mətni çevir."""
        # message / text / caption sahələrini emal et
        for key in ("message", "text", "caption", "file_caption"):
            if key in kwargs and isinstance(kwargs[key], str):
                kwargs[key] = apply_premium_emojis(kwargs[key])
        kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return kwargs

    async def _send_message(self, entity, message=None, **kwargs):
        if isinstance(message, str):
            message = apply_premium_emojis(message)
            kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return await _orig_send_message(self, entity, message, **kwargs)

    async def _edit_message(self, entity, message=None, text=None, **kwargs):
        if isinstance(text, str):
            text = apply_premium_emojis(text)
            kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return await _orig_edit_message(self, entity, message, text, **kwargs)

    async def _send_file(self, entity, file, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = apply_premium_emojis(kwargs["caption"])
            kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return await _orig_send_file(self, entity, file, **kwargs)

    async def _msg_respond(self, message=None, **kwargs):
        if isinstance(message, str):
            message = apply_premium_emojis(message)
            kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return await _orig_msg_respond(self, message, **kwargs)

    async def _msg_reply(self, message=None, **kwargs):
        if isinstance(message, str):
            message = apply_premium_emojis(message)
            kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return await _orig_msg_reply(self, message, **kwargs)

    async def _msg_edit(self, text=None, **kwargs):
        if isinstance(text, str):
            text = apply_premium_emojis(text)
            kwargs.setdefault("parse_mode", PremiumHTMLParser)
        return await _orig_msg_edit(self, text, **kwargs)

    # CLASS səviyyəsində dəyişdir → bütün gələcək instance-lar (pluginlər daxil)
    TelegramClient.send_message = _send_message
    TelegramClient.edit_message = _edit_message
    TelegramClient.send_file = _send_file
    Message.respond = _msg_respond
    Message.reply = _msg_reply
    Message.edit = _msg_edit

    print("[emoji_utils] ✅ Premium emoji patch tətbiq edildi (global, class-level).")


# Avtomatik tətbiq — import edən kimi işə düşür (pluginlər üçün də)
install_premium_emojis()
