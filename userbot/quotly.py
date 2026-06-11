from telethon import events

def register_quotly(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.delete()
            return

        command_type = event.pattern_match.group(1)
        await event.delete()
        bot_username = "QuotLyBot"

        try:
            async with event.client.conversation(bot_username) as conv:
                # 1. Mesajı forward edirik (müəllifi qorumaq üçün)
                await event.client.forward_messages(bot_username, reply_message)
                
                # 2. İlk cavabı gözləyirik
                response1 = await conv.get_response()
                
                # 3. .qs üçün əmr göndəririk
                if command_type == "qs":
                    await conv.send_message("/q s", reply_to=response1.id)
                    final_response = await conv.get_response()
                else:
                    final_response = response1
                
                # 4. Həlledici məqam: Yönləndirmə kimi deyil, 
                # faylın özünü reply olaraq göndəririk
                await event.client.send_file(
                    event.chat_id,
                    final_response,
                    reply_to=reply_message.id
                )
                
        except Exception:
            pass
