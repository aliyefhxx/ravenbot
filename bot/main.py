"""Ryhavean Userbot - Telegram Bot
/start əmrinə cavab verir, Deploy WebApp və Owner düymələrini göstərir.
"""
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_PANEL_URL = os.getenv("WEB_PANEL_URL", "https://ryhavean-panel.onrender.com")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "ryhavean")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env yoxdur")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

WELCOME = (
    "🤖 <b>Ryhavean Userbot</b>\n\n"
    "Telegram hesabınızı daha rahat idarə etmək üçün hazırlanmış "
    "güclü və təhlükəsiz Userbot sistemi.\n\n"
    "Aşağıdakı düymələrdən birini seçin:"
)

def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Deploy", web_app=WebAppInfo(url=WEB_PANEL_URL))],
        [InlineKeyboardButton(text="👤 Owner", url=f"https://t.me/{OWNER_USERNAME}")],
    ])

@dp.message(CommandStart())
async def start_handler(msg: Message) -> None:
    await msg.answer(WELCOME, reply_markup=main_keyboard())

@dp.message(F.text == "/help")
async def help_handler(msg: Message) -> None:
    await msg.answer(
        "ℹ️ <b>Ryhavean Userbot</b>\n\n"
        "Deploy üçün /start əmrindən istifadə edin və <b>Deploy</b> düyməsinə basın.\n"
        "Bütün userbot komandalarının siyahısı üçün userbot aktivləşdikdən sonra "
        "öz hesabınızda <code>.help</code> yazın.",
        reply_markup=main_keyboard(),
    )

async def main() -> None:
    logging.info("Ryhavean Bot başladılır...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
