from telethon import events
import asyncio

def register_quotly(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.edit("<b>❌ Xəta: Mesaja reply atıb əmri yazın.</b>", parse_mode="html")
            return

        command_type = event.pattern_match.group(1)
        await event.delete()
        bot_username = "QuotLyBot"

        try:
            async with event.client.conversation(bot_username) as conv:
                # 1. Mesajı bota forward et
                await event.client.forward_messages(bot_username, reply_message)
                
                # 2. Botun cavabını (sticker və ya mesaj) gözlə
                # Əgər bot dərhal cavab vermirsə, bir az gözləmə qoyuruq
                response = await conv.get_response(timeout=10)
                
                # 3. .qs üçün əlavə əmr
                if command_type == "qs":
                    # Botun son mesajına reply olaraq /q s yazırıq
                    await conv.send_message("/q s", reply_to=response.id)
                    # Şəkil cavabını gözlə
                    response = await conv.get_response(timeout=10)
                
                # 4. Cavabı geri göndər
                await event.client.send_message(
                    event.chat_id,
                    response,
                    reply_to=reply_message.id
                )
                
        except Exception as e:
            # Əgər bir xəta baş verərsə, sadəcə xətanı bildir
            await event.client.send_message(
                event.chat_id, 
                f"<b>❌ QuotLyBot xətası:</b> {str(e)}", 
                parse_mode="html"
            )
