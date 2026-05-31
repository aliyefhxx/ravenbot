"""Nümunə plugin - .ping
İstifadəçilər oxşar pluginlər yaza bilərlər.
"""
from telethon import events

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.ping$"))
async def ping(event):
    await event.edit("🏓 Pong! Plugin işləyir.")
