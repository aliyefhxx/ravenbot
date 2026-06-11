"""
==================================================
💎 PREMİUM EMOJİ SİSTEMİ - RYHAVEAN
==================================================
Telegram Premium Custom Emoji mapping sistemi
"""

# Premium Telegram Custom Emoji ID map
PREMIUM_EMOJI_MAP = {
    "✨": "<emoji id=5368324170671202286>✨</emoji>",
    "✅": "<emoji id=5314250708508964227>✅</emoji>",
    "❌": "<emoji id=5314250708508964228>❌</emoji>",
    "⚡": "<emoji id=5314250708508964229>⚡</emoji>",
    "🚀": "<emoji id=5368324170671202287>🚀</emoji>",
    "🔨": "<emoji id=5314250708508964230>🔨</emoji>",
    "🛡": "<emoji id=5314250708508964231>🛡</emoji>",
    "♻️": "<emoji id=5314250708508964232>♻️</emoji>",
    "📚": "<emoji id=5314250708508964233>📚</emoji>",
    "🔌": "<emoji id=5314250708508964234>🔌</emoji>",
    "👤": "<emoji id=5314250708508964235>👤</emoji>",
    "🧬": "<emoji id=5314250708508964236>🧬</emoji>",
    "🔇": "<emoji id=5314250708508964237>🔇</emoji>",
    "⛔": "<emoji id=5314250708508964238>⛔</emoji>",
    "🪪": "<emoji id=5314250708508964239>🪪</emoji>",
    "🔗": "<emoji id=5314250708508964240>🔗</emoji>",
    "🆔": "<emoji id=5314250708508964241>🆔</emoji>",
    "💬": "<emoji id=5314250708508964242>💬</emoji>",
    "⭐": "<emoji id=5314250708508964243>⭐</emoji>",
    "⚠️": "<emoji id=5314250708508964244>⚠️</emoji>",
    "ℹ️": "<emoji id=5314250708508964245>ℹ️</emoji>",
    "🧹": "<emoji id=5314250708508964246>🧹</emoji>",
    "🗑": "<emoji id=5314250708508964247>🗑</emoji>",
    "📂": "<emoji id=5314250708508964248>📂</emoji>",
    "🏓": "<emoji id=5314250708508964249>🏓</emoji>",
    "🤖": "<emoji id=5314250708508964250>🤖</emoji>",
    "🟢": "<emoji id=5314250708508964251>🟢</emoji>",
    "⏳": "<emoji id=5314250708508964252>⏳</emoji>",
}


def to_premium(text: str) -> str:
    """
    Mətnin içindəki bütün standart emojiləri Premium Telegram emoji ilə əvəz edir.
    
    Args:
        text: Emoji olan mətn
        
    Returns:
        Premium emoji ilə mətn
    """
    for std_emoji, premium_emoji in PREMIUM_EMOJI_MAP.items():
        text = text.replace(std_emoji, premium_emoji)
    return text


def make_bold(text: str) -> str:
    """
    Mətnin hər sətirini qalın (bold) edir.
    
    Args:
        text: Normal mətn
        
    Returns:
        Bold mətn
    """
    lines = text.split('\n')
    bold_lines = []
    for line in lines:
        if line.strip():
            # Əgər artıq <b> tag-ı yoxdursa əlavə et
            if not line.strip().startswith('<b>'):
                bold_lines.append(f"<b>{line}</b>")
            else:
                bold_lines.append(line)
        else:
            bold_lines.append(line)
    return '\n'.join(bold_lines)


def vip_format(text: str, auto_bold: bool = True) -> str:
    """
    Mətni VIP formatına çevirir: Premium emoji + Bold
    
    Args:
        text: Adi mətn
        auto_bold: Avtomatik bold et (default: True)
        
    Returns:
        VIP formatlanmış mətn
    """
    result = to_premium(text)
    if auto_bold:
        result = make_bold(result)
    return result
