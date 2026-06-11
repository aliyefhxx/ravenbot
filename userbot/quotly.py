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
                # 1. Mesajı forward edirik (bu zaman bot müəllifi düzgün tanıyır)
                await event.client.forward_messages(bot_username, reply_message)
                
                # Botun mesajı qəbul etdiyinə dair cavabını gözləyirik (spam-ın qarşısını alır)
                await conv.get_response()
                
                # 2. Əgər .qs-dirsə, şəkil formatı üçün /q s göndər
                if command_type == "qs":
                    # Ən son göndərdiyimiz mesaja cavab olaraq yazırıq
                    last_msg = await conv.get_history()
                    await conv.send_message("/q s", reply_to=last_msg[0].id)
                    # Şəkil cavabını gözlə
                    response = await conv.get_response()
                else:
                    # .q üçün botun avtomatik göndərdiyi sticker-i al
                    response = await conv.get_response()
                
                # 3. Cavabı orijinal mesajın olduğu yerə, həmin mesaja reply kimi göndər
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
