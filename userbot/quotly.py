from telethon import events

def register_quotly(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.delete()
            return

        is_qs = (event.pattern_match.group(1) == "qs")
        await event.delete()
        bot_username = "QuotLyBot"

        try:
            # 1. Mesajı bota forward et ki, müəllif adını düzgün alsın
            await event.client.forward_messages(bot_username, reply_message)
            
            # 2. Botun cavab verməsini gözlə (bəzən 1-2 saniyə çəkə bilir)
            async with event.client.conversation(bot_username) as conv:
                # Əgər .qs-dirsə, botun stiker əvəzinə şəkil verməsi üçün komandanı göndər
                if is_qs:
                    # Botun sonuncu gələn mesajına (forward etdiyimizə) cavab olaraq /q s yazırıq
                    await conv.send_message("/q s", reply_to=reply_message.id)
                
                # Botun cavabını tut
                response = await conv.get_response()
                
                # 3. Əsas məqam: Botdan gələn media faylını birbaşa sizin chat-ə göndər
                # Burada 'response' botun bizə göndərdiyi mesajdır
                await event.client.send_file(
                    event.chat_id,
                    response.media,
                    reply_to=reply_message.id
                )
                
        except Exception as e:
            # Əgər xəta versə, sizə xətanı göstərsin (debug üçün)
            await event.client.send_message(event.chat_id, f"❌ Xəta: {str(e)}")
