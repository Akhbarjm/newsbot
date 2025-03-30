# main.py
import logging
from telethon import TelegramClient
from telethon.events import NewMessage
from handlers import handle_new_message, handle_admin_message
from config import API_ID, API_HASH
from database import init_db

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

client = TelegramClient("bot_session", API_ID, API_HASH)

@client.on(NewMessage(incoming=True))
async def handler(event):
    if event.is_channel or event.is_group:
        await handle_new_message(event, client)
    else:
        await handle_admin_message(event, client)

async def main():
    init_db()
    await client.start()
    logging.info("اتصال برقرار شد!")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
