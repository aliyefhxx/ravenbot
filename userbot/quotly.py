from telethon import events, functions, types

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
                # 1. Mesajın orijinal sahibini düzgün göstərmək üçün 
                # botla söhbəti başladaq (və ya mesajı birbaşa göndərək)
                await conv.send_message(reply_message)
                
                # 2. Botun cavabını (sticker) gözləyirik
                # timeout-u 15 saniyəyə qaldırdıq ki, gecikmə olsa da xəta verməsin
                response = await conv.get_response(timeout=15)
                
                # 3. .qs üçün əlavə əmr
                if command_type == "qs":
                    # Botun bizə göndərdiyi ilk mesajın üzərinə /q s yazırıq
                    await conv.send_message("/q s", reply_to=response.id)
                    # Şəkli gözləyirik
                    response = await conv.get_response(timeout=15)
                
                # 4. Cavabı orijinal mesaja göndəririk
                await event.client.send_message(
                    event.chat_id,
                    response,
                    reply_to=reply_message.id
                )
                
        except Exception as e:
            # Xətanın qarşısını almaq üçün burada sessiyanı bitiririk
            pass
