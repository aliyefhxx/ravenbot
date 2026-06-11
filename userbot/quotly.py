from telethon import events

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
                # 1. Mesajı bota yönləndir
                await conv.send_message(reply_message)
                
                # 2. Əgər .qs-dirsə, şəkli əldə etmək üçün /q s göndər
                if command_type == "qs":
                    await conv.send_message("/q s")
                
                # 3. Botdan gələn cavabı tut
                response = await conv.get_response()
                
                # 4. Cavabı orijinal mesajın olduğu yerə, həmin mesaja reply kimi göndər
                await event.client.send_message(
                    event.chat_id,
                    response,
                    reply_to=reply_message.id
                )
                
        except Exception as e:
            await event.client.send_message(
                event.chat_id, 
                f"<b>❌ QuotLyBot xətası:</b> {str(e)}", 
                parse_mode="html"
            )
