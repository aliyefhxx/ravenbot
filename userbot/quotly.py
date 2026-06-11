"""
==================================================
QUOTLY BOT INTEGRATION - HƏR MÜHİTDƏ İŞLƏYİR
==================================================
.q  -> @QuotLyBot-a göndərir (Sticker olaraq qaytarır)
.qs -> @QuotLyBot-a göndərir (Şəkil olaraq qaytarır)
"""

from telethon import events, functions, types

def register_quotly(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|qs)$"))
    async def quotly_handler(event):
        # Reply-in yoxlanılması
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.edit("<b>❌ Xəta: Bu əmri istifadə etmək üçün bir mesaja reply atmalısınız!</b>", parse_mode="html")
            return

        # Hansı əmr olduğunu təyin et
        is_sticker = (event.pattern_match.group(1) == "q")
        
        # İstifadəçi mesajını sil
        await event.delete()

        # Mesajı botun olduğu chat-ə yönləndirmək əvəzinə, 
        # botun özünə mesajı forward etmək və ya botun özünü trigger etmək
        # Telegram-da başqa bota mesajı reply ilə göndərmək üçün botla şəxsi söhbətə mesaj atırıq
        
        bot_username = "QuotLyBot"
        
        try:
            # Botun chat-ini al
            bot_entity = await event.client.get_input_entity(bot_username)
            
            # Mesajı bota göndər (reply olaraq)
            # .q üçün bot mesajı sticker-ə çevirir, .qs üçün şəkli çevirir
            # Qeyd: Botun öz komanda formatı /q və /q s şəklindədir
            cmd = "/q" if is_sticker else "/q s"
            
            # Botu trigger edirik
            async with event.client.conversation(bot_username) as conv:
                await conv.send_message(reply_message)
                await conv.send_message(cmd)
                response = await conv.get_response()
                
                # Cavabı orijinal mesajın olduğu yerə göndər
                await event.client.send_message(
                    event.chat_id,
                    response,
                    reply_to=reply_message.id
                )
                
        except Exception as e:
            await event.client.send_message(
                event.chat_id, 
                f"<b>❌ Xəta: QuotLyBot ilə əlaqə qurmaq mümkün olmadı.</b>\nDetallar: {str(e)}", 
                parse_mode="html"
            )

