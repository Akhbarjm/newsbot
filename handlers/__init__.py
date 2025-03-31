# handlers/__init__.py
from .base_handler import BaseHandler
from .admin_handlers import AdminHandlers
from .channel_handlers import ChannelHandlers
from .filter_handlers import FilterHandlers
from .settings_handlers import SettingsHandlers
from .translation_handlers import TranslationHandlers
from .system_handlers import SystemHandlers

async def handle_admin_message(event, client):
    """هندلر اصلی پیام‌های ادمین"""
    try:
        user_id = event.sender_id
        if not AdminHandlers.is_admin(user_id) and not await AdminHandlers.handle_creator_registration(event, client):
            await client.send_message(user_id, Config.get_text("fa", "not_admin"))
            return

        await AdminHandlers.handle_admin_commands(event, client)
        await ChannelHandlers.handle_channels_menu(event, client)
        await FilterHandlers.handle_filter_menu(event, client)
        await SettingsHandlers.handle_settings_menu(event, client)
        await TranslationHandlers.handle_translation_request(event, client)
        await SystemHandlers.handle_stop_commands(event, client)
        
    except Exception as e:
        log_action(user_id, f"Error in admin handler: {str(e)}")
        await client.send_message(user_id, Config.get_text("fa", "error_occurred"))

async def handle_new_message(event, client):
    """هندلر اصلی پیام‌های دریافتی از کانال‌ها"""
    try:
        await TranslationHandlers.handle_incoming_message(event, client)
    except Exception as e:
        log_action(0, f"Error in message handler: {str(e)}") 
