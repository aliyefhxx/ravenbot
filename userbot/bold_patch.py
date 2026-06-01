"""
Bütün userbot mesajlarını avtomatik qalın (bold) edir.
main.py-də start_userbot() çağırılmadan ƏVVƏL apply_bold_patch() çağır.
"""
from pyrogram import Client, enums

# Qalın etmək istəmədiyimiz parse mode-lar (məs. kod blokları)
_SKIP_MODES = {enums.ParseMode.DISABLED}


def _wrap_bold_html(text):
    if text is None:
        return text
    text = str(text)
    if not text.strip():
        return text
    # Artıq tam <b>...</b> ilə bükülübsə təkrar bükmə
    stripped = text.strip()
    if stripped.startswith("<b>") and stripped.endswith("</b>"):
        return text
    return f"<b>{text}</b>"


def apply_bold_patch():
    # Orijinal metodları saxla
    _orig_send_message = Client.send_message
    _orig_edit_message_text = Client.edit_message_text
    _orig_send_photo = Client.send_photo
    _orig_send_document = Client.send_document
    _orig_send_video = Client.send_video
    _orig_send_audio = Client.send_audio
    _orig_send_animation = Client.send_animation
    _orig_send_voice = Client.send_voice
    _orig_edit_message_caption = Client.edit_message_caption

    def _patch_kwargs(kwargs, text_key):
        parse_mode = kwargs.get("parse_mode")
        if parse_mode in _SKIP_MODES:
            return
        # parse_mode-u HTML-ə zorla, çünki <b> taglarını istifadə edirik
        kwargs["parse_mode"] = enums.ParseMode.HTML
        if text_key in kwargs and kwargs[text_key] is not None:
            kwargs[text_key] = _wrap_bold_html(kwargs[text_key])

    async def send_message(self, chat_id, text, *args, **kwargs):
        kwargs["parse_mode"] = enums.ParseMode.HTML if kwargs.get("parse_mode") not in _SKIP_MODES else kwargs["parse_mode"]
        if kwargs.get("parse_mode") != enums.ParseMode.DISABLED:
            text = _wrap_bold_html(text)
        return await _orig_send_message(self, chat_id, text, *args, **kwargs)

    async def edit_message_text(self, chat_id, message_id, text, *args, **kwargs):
        if kwargs.get("parse_mode") not in _SKIP_MODES:
            kwargs["parse_mode"] = enums.ParseMode.HTML
            text = _wrap_bold_html(text)
        return await _orig_edit_message_text(self, chat_id, message_id, text, *args, **kwargs)

    async def edit_message_caption(self, chat_id, message_id, caption=None, *args, **kwargs):
        if kwargs.get("parse_mode") not in _SKIP_MODES:
            kwargs["parse_mode"] = enums.ParseMode.HTML
            caption = _wrap_bold_html(caption)
        return await _orig_edit_message_caption(self, chat_id, message_id, caption, *args, **kwargs)

    def _media_wrapper(orig):
        async def wrapper(self, chat_id, file, *args, **kwargs):
            if kwargs.get("parse_mode") not in _SKIP_MODES:
                kwargs["parse_mode"] = enums.ParseMode.HTML
                if kwargs.get("caption"):
                    kwargs["caption"] = _wrap_bold_html(kwargs["caption"])
            return await orig(self, chat_id, file, *args, **kwargs)
        return wrapper

    Client.send_message = send_message
    Client.edit_message_text = edit_message_text
    Client.edit_message_caption = edit_message_caption
    Client.send_photo = _media_wrapper(_orig_send_photo)
    Client.send_document = _media_wrapper(_orig_send_document)
    Client.send_video = _media_wrapper(_orig_send_video)
    Client.send_audio = _media_wrapper(_orig_send_audio)
    Client.send_animation = _media_wrapper(_orig_send_animation)
    Client.send_voice = _media_wrapper(_orig_send_voice)
