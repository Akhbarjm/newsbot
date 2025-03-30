# handlers/base_handler.py
from telethon import events
from telethon.tl.types import KeyboardButton, ReplyKeyboardMarkup
from config import Config, USER_STATES
from database import (
    get_user_settings, 
    get_admin_level,
    log_action
)

class BaseHandler:
    @staticmethod
    async def show_main_menu(event, user_id, lang):
        """نمایش منوی اصلی به کاربر"""
        menu_options = Config.get_menu(lang, "main")
        rows = []
        for option in menu_options:
            if get_admin_level(user_id) != 1 and option == menu_options[3]:
                personal_text = {
                    "fa": "شخصی",
                    "en": "Personal",
                    "ar": "شخصي",
                    "ru": "Лично"
                }.get(lang, "Personal")
                option = f"{option} ({personal_text})"
            rows.append([KeyboardButton(text=option)])
        
        await event.reply(
            Config.get_text(lang, "welcome"),
            reply_markup=ReplyKeyboardMarkup(rows=rows)
             )
        USER_STATES[user_id] = "main_menu"

    @staticmethod
    async def handle_start(event, client):
        """مدیریت دستور /start"""
        user_id = event.sender_id
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        
        if not settings["chat_destination"]:
            await event.reply(Config.get_text(lang, "chat_destination"))
            USER_STATES[user_id] = "awaiting_chat_destination"
            return
        
        await BaseHandler.show_main_menu(event, user_id, lang)
        log_action(user_id, "User started bot")

    @staticmethod
    async def handle_chat_destination(event, client, user_id, settings):
        """مدیریت تنظیم چت مقصد"""
        update_settings(user_id, chat_destination=event.message.text)
        await BaseHandler.show_main_menu(event, user_id, settings["interface_lang"])
        log_action(user_id, "Set chat destination")
