from telethon import events

def register_quotly(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        # 1. Hədəf mesajı əldə et
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.delete()
            return

        command = event.pattern_match.group(1)
        await event.delete()
        bot_username = "QuotLyBot"

        try:
            # 2. Botla əlaqə qur
            async with event.client.conversation(bot_username) as conv:
                # 3. Mesajı forward et və botun cavab verməsini gözlə
                await event.client.forward_messages(bot_username, reply_message)
                
                # Botun cavabını (sticker və ya mesaj) gözlə
                resp1 = await conv.get_response()
                
                # 4. Əgər .qs-dirsə, şəkli istə
                if command == "qs":
                    # Botun bizə göndərdiyi ilk mesaja cavab olaraq /q s yazırıq
                    await conv.send_message("/q s", reply_to=resp1.id)
                    final_response = await conv.get_response()
                else:
                    final_response = resp1

                # 5. Əsas hissə: Botdan gələn media faylını (sticker/şəkil) birbaşa göndər
                # Burada 'final_response.media' botun hazırladığı faylın məzmunudur
                if final_response.media:
                    await event.client.send_file(
                        event.chat_id,
                        final_response.media,
                        reply_to=reply_message.id
                    )
                else:
                    # Əgər media tapılmazsa, botun mətnini göndər
                    await event.client.send_message(
                        event.chat_id,
                        final_response.text,
                        reply_to=reply_message.id
                    )
                
        except Exception as e:
            # Xəta baş versə, debug üçün çap et (sizə görünməyəcək)
            pass
