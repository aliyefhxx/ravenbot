"""
==================================================
💬 QUOTLY SİSTEMİ - QUOTE TO IMAGE/STICKER
==================================================
Telegram mesajlarını QuotLy-style şəkil və stickerə çevirir
"""

import io
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from telethon import events
from db import get_setting, set_setting

# 10 Premium görünüşlü gradient rəng palitrası
PREMIUM_COLORS = [
    # 1. Purple Dream
    {"start": (138, 43, 226), "end": (75, 0, 130), "text": (255, 255, 255)},
    # 2. Ocean Blue
    {"start": (0, 105, 148), "end": (0, 191, 255), "text": (255, 255, 255)},
    # 3. Sunset Orange
    {"start": (255, 94, 77), "end": (255, 165, 0), "text": (255, 255, 255)},
    # 4. Forest Green
    {"start": (34, 139, 34), "end": (144, 238, 144), "text": (255, 255, 255)},
    # 5. Royal Gold
    {"start": (255, 215, 0), "end": (184, 134, 11), "text": (0, 0, 0)},
    # 6. Rose Pink
    {"start": (255, 20, 147), "end": (255, 182, 193), "text": (255, 255, 255)},
    # 7. Dark Slate
    {"start": (47, 79, 79), "end": (112, 128, 144), "text": (255, 255, 255)},
    # 8. Crimson Red
    {"start": (220, 20, 60), "end": (139, 0, 0), "text": (255, 255, 255)},
    # 9. Midnight Blue
    {"start": (25, 25, 112), "end": (72, 61, 139), "text": (255, 255, 255)},
    # 10. Emerald Green
    {"start": (0, 201, 87), "end": (0, 128, 96), "text": (255, 255, 255)},
]


def create_gradient(width: int, height: int, color_scheme: dict) -> Image.Image:
    """Gradient arxa fon yaradır"""
    base = Image.new('RGB', (width, height), color_scheme["start"])
    top = Image.new('RGB', (width, height), color_scheme["end"])
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (y / height)))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


async def generate_quote_image(
    text: str,
    author_name: str,
    author_username: str = "",
    color_id: int = 0,
    width: int = 512,
    padding: int = 40,
) -> io.BytesIO:
    """
    QuotLy-style quote şəkil yaradır
    
    Args:
        text: Quote mətni
        author_name: Müəllif adı
        author_username: Müəllif username
        color_id: Rəng ID (0-9)
        width: Şəklin eni
        padding: Padding
        
    Returns:
        BytesIO şəkil
    """
    # Rəng seçimi
    if color_id < 0 or color_id >= len(PREMIUM_COLORS):
        color_id = 0
    color_scheme = PREMIUM_COLORS[color_id]
    
    # Font yükləmə (sistem fontundan istifadə)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        # Fallback
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Mətni wrap et
    wrapped_text = textwrap.fill(text, width=35)
    
    # Temporary draw to calculate text height
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    text_bbox = temp_draw.multiline_textbbox((0, 0), wrapped_text, font=font_medium)
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate total height
    total_height = padding * 2 + text_height + 80  # 80 for author info + watermark
    
    # Create gradient background
    img = create_gradient(width, total_height, color_scheme)
    
    # Add subtle shadow effect
    img = img.filter(ImageFilter.SMOOTH_MORE)
    
    draw = ImageDraw.Draw(img)
    text_color = color_scheme["text"]
    
    # Draw quote icon
    y_pos = padding
    draw.text((padding, y_pos), '"', font=font_large, fill=text_color)
    
    # Draw quote text
    y_pos += 40
    draw.multiline_text(
        (padding + 10, y_pos),
        wrapped_text,
        font=font_medium,
        fill=text_color,
        spacing=8
    )
    
    # Draw author info
    y_pos += text_height + 20
    author_text = f"— {author_name}"
    if author_username:
        author_text += f" (@{author_username})"
    draw.text((padding + 10, y_pos), author_text, font=font_small, fill=text_color)
    
    # Draw watermark @rveanx at bottom right
    watermark = "@rveanx"
    watermark_bbox = draw.textbbox((0, 0), watermark, font=font_small)
    watermark_width = watermark_bbox[2] - watermark_bbox[0]
    draw.text(
        (width - watermark_width - padding, total_height - padding),
        watermark,
        font=font_small,
        fill=(255, 255, 255, 180)
    )
    
    # Convert to BytesIO
    output = io.BytesIO()
    img.save(output, format='PNG', quality=95)
    output.seek(0)
    return output


async def image_to_sticker(image_bytes: io.BytesIO) -> io.BytesIO:
    """
    PNG şəkli WebP sticker formatına çevirir
    
    Args:
        image_bytes: PNG şəkil
        
    Returns:
        WebP sticker
    """
    img = Image.open(image_bytes)
    
    # Resize to 512x512 max (Telegram sticker requirement)
    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    
    # Convert to WebP
    output = io.BytesIO()
    img.save(output, format='WEBP', quality=95)
    output.seek(0)
    output.name = "sticker.webp"
    return output


def register_quotly(client):
    """QuotLy komandalarını qeydiyyatdan keçirir"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.qs(?:\s+(\d+))?$"))
    async def qs_command(event):
        """
        .qs [color_id] - QuotLy-style şəkil yaradır
        color_id: 0-9 arası rəng seçimi (optional)
        """
        if not event.is_reply:
            await event.edit(
                "<b>ℹ️ İstifadə: Mesaja reply edin və <code>.qs</code> yazın</b>\n"
                "<b>Rəng dəyişmək üçün: <code>.qs 1</code> (0-9)</b>",
                parse_mode="html"
            )
            return
        
        # Get color ID from command or user settings
        match = event.pattern_match.group(1)
        if match:
            color_id = int(match) % 10
            # Save user preference
            await set_setting(f"quotly_color_{event.sender_id}", str(color_id))
        else:
            # Load saved color or default to 0
            saved = await get_setting(f"quotly_color_{event.sender_id}", "0")
            color_id = int(saved) % 10
        
        await event.edit("<b>🎨 QuotLy şəkil yaradılır...</b>", parse_mode="html")
        
        try:
            # Get replied message
            reply_msg = await event.get_reply_message()
            text = reply_msg.text or reply_msg.message or "..."
            
            # Get author info
            sender = await reply_msg.get_sender()
            author_name = sender.first_name or "Unknown"
            author_username = sender.username or ""
            
            # Generate image
            img_bytes = await generate_quote_image(
                text=text,
                author_name=author_name,
                author_username=author_username,
                color_id=color_id,
            )
            
            # Send image
            await event.client.send_file(
                event.chat_id,
                img_bytes,
                caption=f"<b>📸 QuotLy by @rveanx | Rəng: {color_id}</b>",
                parse_mode="html"
            )
            await event.delete()
            
        except Exception as e:
            await event.edit(f"<b>❌ Xəta: {e}</b>", parse_mode="html")
    
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.q$"))
    async def q_command(event):
        """
        .q - QuotLy şəkil yaradır və stickerə çevirir
        """
        if not event.is_reply:
            await event.edit(
                "<b>ℹ️ İstifadə: Mesaja reply edin və <code>.q</code> yazın</b>",
                parse_mode="html"
            )
            return
        
        await event.edit("<b>🎨 QuotLy sticker yaradılır...</b>", parse_mode="html")
        
        try:
            # Get replied message
            reply_msg = await event.get_reply_message()
            text = reply_msg.text or reply_msg.message or "..."
            
            # Get author info
            sender = await reply_msg.get_sender()
            author_name = sender.first_name or "Unknown"
            author_username = sender.username or ""
            
            # Get user's saved color
            saved = await get_setting(f"quotly_color_{event.sender_id}", "0")
            color_id = int(saved) % 10
            
            # Generate image
            img_bytes = await generate_quote_image(
                text=text,
                author_name=author_name,
                author_username=author_username,
                color_id=color_id,
            )
            
            # Convert to sticker
            sticker_bytes = await image_to_sticker(img_bytes)
            
            # Send sticker
            await event.client.send_file(
                event.chat_id,
                sticker_bytes,
                force_document=False
            )
            await event.delete()
            
        except Exception as e:
            await event.edit(f"<b>❌ Xəta: {e}</b>", parse_mode="html")
