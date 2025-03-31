# handlers/channel_handlers.py
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import KeyboardButton, ReplyKeyboardMarkup
from config import Config, USER_STATES
from database import (
    get_user_channels, get_user_settings, get_filters,
    add_channel, remove_channel, add_blacklist,
    update_settings, log_action, is_blacklisted
)

class ChannelHandlers:
    @staticmethod
    async def handle_channels_menu(event, client):
        """مدیریت منوی کانال‌ها"""
        user_id = event.sender_id
        text = event.message.text
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        level = get_admin_level(user_id) or 0

        # نمایش لیست کانال‌ها
        if text == Config.get_menu(lang, "channels")[0]:
            channels = get_user_channels(user_id)
            channel_list = "\n".join(channels) if channels else Config.get_text(lang, "empty_list")
            await event.reply(
                Config.get_text(lang, "channels_list").format(list=channel_list),
                reply_markup=ChannelHandlers._get_channels_keyboard(lang, level)
            )

        # افزودن کانال جدید
        elif text == Config.get_menu(lang, "channels")[1]:
            await event.reply(Config.get_text(lang, "add_channel_prompt"))
            USER_STATES[user_id] = "awaiting_channel_id"

        # سایر موارد...
        
    @staticmethod
    async def handle_channel_actions(event, client):
        """مدیریت عملیات مربوط به کانال‌ها"""
        user_id = event.sender_id
        text = event.message.text
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        level = get_admin_level(user_id) or 0
        current_state = USER_STATES.get(user_id)

        # پردازش افزودن کانال
        if current_state == "awaiting_channel_id":
            await ChannelHandlers._process_add_channel(event, client, user_id, text, lang, level)
            USER_STATES[user_id] = "channels_menu"

        # پردازش حذف کانال
        elif current_state == "awaiting_remove_channel":
            remove_channel(user_id, text)
            await event.reply(
                Config.get_text(lang, "channel_removed"),
                reply_markup=ChannelHandlers._get_channels_keyboard(lang, level)
            )
            log_action(user_id, f"Removed channel {text}")
            USER_STATES[user_id] = "channels_menu"

        # سایر عملیات...

    @staticmethod
    async def _process_add_channel(event, client, user_id, channel_id, lang, level):
        """پردازش افزودن کانال جدید"""
        if is_blacklisted(channel_id):
            await event.reply(
                Config.get_text(lang, "blacklist_error"),
                reply_markup=ChannelHandlers._get_channels_keyboard(lang, level)
            )
            return

        limits = {1: 20, 2: 20, 3: 15, 4: 10}
        if len(get_user_channels(user_id)) >= limits[level]:
            await event.reply(
                Config.get_text(lang, "limit_exceeded").format(limit=limits[level]),
                reply_markup=ChannelHandlers._get_channels_keyboard(lang, level)
            )
            return

        try:
            await client.get_entity(channel_id)
            add_channel(user_id, channel_id)
            await event.reply(
                Config.get_text(lang, "channel_added"),
                reply_markup=ChannelHandlers._get_channels_keyboard(lang, level)
            )
            log_action(user_id, f"Added channel {channel_id}")
        except ValueError as e:
            if "Cannot find any entity" in str(e):
                await event.reply(Config.get_text(lang, "invite_link_prompt"))
                USER_STATES[user_id] = "awaiting_invite_link"
            else:
                await event.reply(
                    Config.get_text(lang, "error_invalid_channel"),
                    reply_markup=ChannelHandlers._get_channels_keyboard(lang, level)
                )

    @staticmethod
    def _get_channels_keyboard(lang, level):
        """تهیه کیبورد منوی کانال‌ها"""
        channels_menu = Config.get_menu(lang, "channels")
        if level != 1:
            channels_menu = [item for item in channels_menu if item != Config.get_menu(lang, "channels")[3]]
        
        return ReplyKeyboardMarkup(
            rows=[[KeyboardButton(text=item)] for item in channels_menu]
        )
