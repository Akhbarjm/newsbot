# handlers/system_handlers.py
from telethon.tl.types import KeyboardButton, ReplyKeyboardMarkup
from config import Config, USER_STATES
from database import update_settings, log_action, get_admin_level

class SystemHandlers:
    @staticmethod
    async def handle_stop_commands(event, client):
        """مدیریت دستورات توقف بات"""
        user_id = event.sender_id
        text = event.message.text
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        level = get_admin_level(user_id) or 0

        if text == Config.get_menu(lang, "main")[3] and level == 1:
            await SystemHandlers._show_stop_options(event, lang)
            USER_STATES[user_id] = "stop_menu"

        elif USER_STATES.get(user_id) == "stop_menu":
            await SystemHandlers._process_stop_command(event, client, user_id, text, settings)

    @staticmethod
    async def _show_stop_options(event, lang):
        """نمایش گزینه‌های توقف"""
        keyboard = ReplyKeyboardMarkup(
            rows=[[KeyboardButton(text=item)] for item in Config.get_menu(lang, "stop_options")]
        )
        await event.reply(
            Config.get_text(lang, "stop_question"),
            reply_markup=keyboard
        )

    @staticmethod
    async def _process_stop_command(event, client, user_id, text, settings):
        """پردازش دستور توقف"""
        lang = settings["interface_lang"]
        level = get_admin_level(user_id) or 0

        personal_text = Config.get_menu(lang, "stop_options")[0]
        if text in [f"{Config.get_menu(lang, 'main')[3]} ({'شخصی' if lang == 'fa' else 'Personal' if lang == 'en' else 'شخصي' if lang == 'ar' else 'Лично'})", personal_text]:
            update_settings(user_id, stopped=True)
            await BaseHandler.show_main_menu(event, user_id, lang)
            await event.reply(Config.get_text(lang, "stop_personal"))
            log_action(user_id, "Bot stopped personally")

        elif text == Config.get_menu(lang, "stop_options")[1] and level == 1:
            await event.reply(Config.get_text(lang, "stop_global"))
            log_action(user_id, "Bot stopped globally")
            raise SystemExit

        elif text == Config.get_menu(lang, "stop_options")[2]:
            await BaseHandler.show_main_menu(event, user_id, lang) 
