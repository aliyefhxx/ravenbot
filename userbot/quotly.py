from telethon import events

def register_quotly(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        # 1. Reply yoxlanılması
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.delete()
            return

        command_type = event.pattern_match.group(1)
        await event.delete()
        bot_username = "QuotLyBot"

        try:
            async with event.client.conversation(bot_username) as conv:
                # 2. Mesajı forward et (müəllif adını qorumaq üçün)
                await event.client.forward_messages(bot_username, reply_message)
                
                # 3. Botdan gələn cavabı gözlə
                response = await conv.get_response()
                
                # 4. Əgər .qs-dirsə, şəkil üçün əmri göndər və yenidən cavab gözlə
                if command_type == "qs":
                    await conv.send_message("/q s", reply_to=response.id)
                    response = await conv.get_response()
                
                # 5. Sticker və ya Şəkli göndər
                # Burada 'response.media' botun hazırladığı faylın məzmunudur
                if response.media:
                    await event.client.send_file(
                        event.chat_id,
                        response.media,
                        reply_to=reply_message.id
                    )
                else:
                    # Əgər media yoxdursa (xəta halı), mətn kimi göndər
                    await event.client.send_message(
                        event.chat_id,
                        response.text,
                        reply_to=reply_message.id
                    )
                
        except Exception:
            pass
