# handlers/admin_handlers.py (بخش 1)
from telethon import events
from .base_handler import BaseHandler
from config import Config, CREATOR_ID, MASTER_PASSWORD, USER_STATES
from database import (
    get_user_settings, get_admin_level, get_all_admins,
    add_admin, update_settings, log_action
)

class AdminHandlers:
    @staticmethod
    async def handle_creator_registration(event, client):
        """ثبت سازنده اصلی"""
        user_id = event.sender_id
        if user_id == CREATOR_ID and event.message.text == MASTER_PASSWORD:
            add_admin(user_id, 1)
            await event.reply(Config.get_text("fa", "creator_success"))
            await event.reply(Config.get_text("fa", "chat_destination"))
            log_action(user_id, "Creator registered")
            USER_STATES[user_id] = "awaiting_chat_destination"
            return True
        return False

    @staticmethod
    async def handle_admin_commands(event, client):
        """مدیریت دستورات ادمین"""
        user_id = event.sender_id
        text = event.message.text
        level = get_admin_level(user_id) or 0
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]

        # مدیریت وضعیت‌های مختلف
        current_state = USER_STATES.get(user_id)

        if current_state == "awaiting_chat_destination":
            await BaseHandler.handle_chat_destination(event, client, user_id, settings)
            return

        if text == "/start" or current_state == "main_menu":
            await BaseHandler.handle_start(event, client)
            return

        if text == Config.get_menu(lang, "main")[0] and level in [1, 2, 3]:
            await AdminHandlers.show_admin_menu(event, lang, level)
            USER_STATES[user_id] = "admins_menu"
            return

    @staticmethod
    async def show_admin_menu(event, lang, level):
        """نمایش منوی مدیریت ادمین‌ها"""
        admin_menu = Config.get_menu(lang, "admins")
        if level != 1:
            admin_menu = [item for item in admin_menu if item != Config.get_menu(lang, "admins")[2]]
            if level != 2:
                admin_menu = [item for item in admin_menu if item != Config.get_menu(lang, "admins")[3]]
        
        keyboard = ReplyKeyboardMarkup(
            rows=[[KeyboardButton(text=item)] for item in admin_menu]
        )
        await event.reply(
            Config.get_menu(lang, "admins")[0].split()[0] + ":",
            reply_markup=keyboard
  ) 
