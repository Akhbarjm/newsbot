# handlers/settings_handlers.py
from telethon.tl.types import KeyboardButton, ReplyKeyboardMarkup
from config import Config, USER_STATES
from database import (
    get_user_settings, update_settings, log_action
)

class SettingsHandlers:
    @staticmethod
    async def handle_settings_menu(event, client):
        """مدیریت منوی تنظیمات"""
        user_id = event.sender_id
        text = event.message.text
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        current_state = USER_STATES.get(user_id)

        # نمایش منوی تنظیمات
        if text == Config.get_menu(lang, "main")[4]:
            await SettingsHandlers._show_settings_menu(event, lang)
            USER_STATES[user_id] = "settings_menu"

        # پردازش گزینه‌های تنظیمات
        elif current_state == "settings_menu":
            await SettingsHandlers._process_settings(event, client, user_id, text, settings)

    @staticmethod
    async def _show_settings_menu(event, lang):
        """نمایش منوی تنظیمات"""
        keyboard = ReplyKeyboardMarkup(
            rows=[[KeyboardButton(text=item)] for item in Config.get_menu(lang, "settings")]
        )
        await event.reply(
            Config.get_menu(lang, "settings")[0].split()[0] + ":",
            reply_markup=keyboard
        )

    @staticmethod
    async def _process_settings(event, client, user_id, text, settings):
        """پردازش گزینه‌های تنظیمات"""
        lang = settings["interface_lang"]

        if text == Config.get_menu(lang, "settings")[0]:  # زبان رابط
            await event.reply(Config.get_text(lang, "interface_lang"))
            USER_STATES[user_id] = "awaiting_interface_lang"

        elif text == Config.get_menu(lang, "settings")[1]:  # زبان مقصد
            await event.reply(Config.get_text(lang, "dest_lang"))
            USER_STATES[user_id] = "awaiting_dest_lang"

        # سایر گزینه‌های تنظیمات...
