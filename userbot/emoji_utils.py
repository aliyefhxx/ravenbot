"""
==================================================
💎 PREMİUM EMOJİ SİSTEMİ - RYHAVEAN
==================================================
Telegram Premium Custom Emoji mapping sistemi
"""

# Premium Telegram Custom Emoji ID map
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
