# handlers/translation_handlers.py
from googletrans import Translator
from telethon import events
from config import Config
from database import get_user_settings, log_action

translator = Translator()

class TranslationHandlers:
    @staticmethod
    async def handle_translation_request(event, client):
        """مدیریت درخواست‌های ترجمه دستی"""
        user_id = event.sender_id
        text = event.message.text
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        
        if text == Config.get_menu(lang, "main")[2]:  # ترجمه متن
            await event.reply(Config.get_text(lang, "translate_prompt"))
            USER_STATES[user_id] = "awaiting_text_to_translate"
            
        elif USER_STATES.get(user_id) == "awaiting_text_to_translate":
            try:
                translated = translator.translate(text, dest=settings["dest_lang"]).text
                await BaseHandler.show_main_menu(event, user_id, lang)
                await event.reply(
                    f"{Config.get_text(lang, 'translation')}: {translated}"
                )
                log_action(user_id, f"Translated text: {text[:50]}...")
            except Exception as e:
                await event.reply(Config.get_text(lang, "translation_error"))
                log_action(user_id, f"Translation failed: {str(e)}")

    @staticmethod
    async def handle_incoming_message(event, client):
        """مدیریت پیام‌های دریافتی از کانال‌ها"""
        if not event.chat:
            return

        channel = f"@{event.chat.username}" if hasattr(event.chat, "username") and event.chat.username else str(event.chat.id)
        
        admin_id = next((uid for uid in get_all_admins() if channel in get_user_channels(uid)), None)
        if not admin_id:
            return

        settings = get_user_settings(admin_id)
        if not settings["chat_destination"] or settings["stopped"]:
            return

        await TranslationHandlers._process_channel_message(event, client, channel, admin_id, settings)

    @staticmethod
    async def _process_channel_message(event, client, channel, admin_id, settings):
        """پردازش و ترجمه پیام کانال"""
        lang = settings["interface_lang"]
        news_text = event.message.text or event.message.caption or Config.get_text(lang, "no_text")
        
        try:
            translated = translator.translate(news_text, dest=settings["dest_lang"]).text.lower()
            filters = get_filters(admin_id, channel)
            
            if TranslationHandlers._should_send_message(translated, filters):
                await TranslationHandlers._send_translated_message(
                    client, admin_id, channel, 
                    translated, event.message, settings
                )
                
        except Exception as e:
            log_action(admin_id, f"Translation error in {channel}: {str(e)}")

    @staticmethod
    def _should_send_message(translated_text, filters):
        """تعیین آیا پیام باید ارسال شود یا خیر"""
        blacklist = filters["blacklist"].split(",") if filters["blacklist"] else []
        whitelist = filters["whitelist"].split(",") if filters["whitelist"] else []
        
        has_black = any(word.strip() in translated_text for word in blacklist)
        has_white = any(word.strip() in translated_text for word in whitelist)
        
        if blacklist and whitelist:
            return has_white or not has_black
        elif blacklist:
            return not has_black
        elif whitelist:
            return has_white
        return True

    @staticmethod
    async def _send_translated_message(client, admin_id, channel, translated_text, message, settings):
        """ارسال پیام ترجمه شده به مقصد"""
        lang = settings["interface_lang"]
        message_content = translated_text if settings["message_format"] == "text_only" else \
            f"{translated_text}\n{'از' if lang == 'fa' else 'From' if lang == 'en' else 'من' if lang == 'ar' else 'От'} {channel}"
        
        await client.send_message(settings["chat_destination"], message_content)
        log_action(admin_id, f"Sent translation from {channel}")
        
        if message.media:
            await client.forward_messages(
                settings["chat_destination"],
                message.id,
                message.chat_id
            )
            log_action(admin_id, f"Forwarded media from {channel}") 
