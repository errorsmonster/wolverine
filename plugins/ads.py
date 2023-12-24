from pyrogram import Client, filters
from datetime import datetime, timedelta
from database.config_db import update_advirtisment, get_advirtisment
from info import ADMINS
import asyncio

@Client.on_message(filters.private & filters.command("set_ads") & filters.user(ADMINS))
async def set_ads(client, message):
    # Parse command arguments
    command_args = message.text.split()[1:]
    if len(command_args) != 2:
        await message.reply_text("Usage: /set_ads <ads_name> <duration/impression_count>")
        return

    ads_name, duration_or_impression = command_args
    expiry_date = None
    impression_count = None

    # Check if duration or impression count is provided
    if not duration_or_impression.isdigit():
        await message.reply_text("Duration or impression count must be a number.")
        return

    # If duration is provided, calculate expiry date
    if duration_or_impression:
        expiry_date = datetime.now() + timedelta(days=int(duration_or_impression))
    # If impression count is provided, convert it to integer
    else:
        impression_count = int(duration_or_impression)

    # Check if reply message exists
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("Reply to a message to set it as your advertisement.")
        return

    # Update advertisement in the database
    await update_advirtisment(reply.message_id, ads_name, expiry_date, impression_count)
    await asyncio.sleep(3)
    _, name, _ = await get_advirtisment()
    await message.reply_text(f"Advertisement: '{name}' has been set.")