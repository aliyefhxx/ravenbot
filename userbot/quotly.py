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
                # 1. Mesajı forward edirik (bu zaman orijinal müəllif qorunur)
                await event.client.forward_messages(bot_username, reply_message)
                
                # 2. Botun mesajı işləməsi üçün 1 saniyə gözləyirik
                # Botun "Sticker yaranır" və ya bənzəri cavabını tuturuq
                response = await conv.get_response()
                
                # 3. .qs əmri üçün
                if command_type == "qs":
                    # Botun göndərdiyi ilk mesaja (sticker/image) cavab olaraq əmri yazırıq
                    await conv.send_message("/q s", reply_to=response.id)
                    # İndi botun bizə göndərdiyi şəkli tuturuq
                    response = await conv.get_response()
                
                # 4. Şəkli/Stikeri orijinal mesaja reply kimi göndəririk
                await event.client.send_message(
                    event.chat_id,
                    response,
                    reply_to=reply_message.id
                )
                
        except Exception:
            # Xəta baş versə belə sessiyanı pass keçirik ki, istifadəçiyə görünməsin
            pass
