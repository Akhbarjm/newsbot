# handlers/filter_handlers.py
from telethon.tl.types import KeyboardButton, ReplyKeyboardMarkup
from config import Config, USER_STATES
from database import (
    get_user_settings, get_filters,
    add_filter, log_action
)

class FilterHandlers:
    @staticmethod
    async def handle_filter_menu(event, client):
        """مدیریت منوی فیلترها"""
        user_id = event.sender_id
        text = event.message.text
        settings = get_user_settings(user_id)
        lang = settings["interface_lang"]
        current_state = USER_STATES.get(user_id)

        # انتخاب کانال برای فیلتر
        if text == Config.get_menu(lang, "channels")[4]:
            channels = get_user_channels(user_id)
            await event.reply(
                Config.get_text(lang, "select_channel").format(list="\n".join(channels))
            )
            USER_STATES[user_id] = "awaiting_filter_channel"

        # پردازش انتخاب کانال
        elif current_state == "awaiting_filter_channel":
            if text in get_user_channels(user_id):
                update_settings(user_id, pending_channel=text)
                await FilterHandlers._show_filter_menu(event, lang)
                USER_STATES[user_id] = "filter_menu"
            else:
                await event.reply(
                    Config.get_text(lang, "error_invalid_channel"),
                    reply_markup=ChannelHandlers._get_channels_keyboard(lang, get_admin_level(user_id))
                )

        # مدیریت منوی فیلترها
        elif current_state == "filter_menu":
            await FilterHandlers._process_filter_menu(event, client, user_id, text, settings)

    @staticmethod
    async def _show_filter_menu(event, lang):
        """نمایش منوی فیلترها"""
        keyboard = ReplyKeyboardMarkup(
            rows=[[KeyboardButton(text=item)] for item in Config.get_menu(lang, "filter")]
        )
        await event.reply(
            Config.get_menu(lang, "filter")[0].split()[0] + ":",
            reply_markup=keyboard
        )

    @staticmethod
    async def _process_filter_menu(event, client, user_id, text, settings):
        """پردازش گزینه‌های منوی فیلتر"""
        lang = settings["interface_lang"]
        channel = settings["pending_channel"]

        if text == Config.get_menu(lang, "filter")[0]:  # کلمات بلک‌لیست
            await event.reply(Config.get_text(lang, "blacklist_words"))
            USER_STATES[user_id] = "awaiting_blacklist_words"

        elif text == Config.get_menu(lang, "filter")[1]:  # کلمات وایت‌لیست
            await event.reply(Config.get_text(lang, "whitelist_words"))
            USER_STATES[user_id] = "awaiting_whitelist_words"

        elif USER_STATES.get(user_id) == "awaiting_blacklist_words":
            current_filters = get_filters(user_id, channel)
            add_filter(user_id, channel, text, current_filters["whitelist"])
            await event.reply(
                Config.get_text(lang, "filter_added").format(channel=channel),
                reply_markup=FilterHandlers._get_filter_keyboard(lang)
            )
            log_action(user_id, f"Set blacklist for {channel}: {text}")

        elif USER_STATES.get(user_id) == "awaiting_whitelist_words":
            current_filters = get_filters(user_id, channel)
            add_filter(user_id, channel, current_filters["blacklist"], text)
            await event.reply(
                Config.get_text(lang, "filter_added").format(channel=channel),
                reply_markup=FilterHandlers._get_filter_keyboard(lang)
            )
            log_action(user_id, f"Set whitelist for {channel}: {text}")

        elif text == Config.get_menu(lang, "filter")[2]:  # بازگشت
            await ChannelHandlers.handle_channels_menu(event, client)
