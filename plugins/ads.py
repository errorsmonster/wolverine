from pyrogram import Client, filters
from datetime import datetime, timedelta
from database.config_db import update_advirtisment, get_advirtisment
from info import ADMINS
import asyncio


@Client.on_message(filters.private & filters.command("set_ads") & filters.user(ADMINS))
async def set_ads(client, message):

    command_args = message.text.split()[1:]
    if len(command_args) != 2:
        await message.reply_text("Usage: /set_ads <ads_name> <d:duration/i:impression_count>")
        return

    ads_name, duration_or_impression = command_args
    expiry_date = None
    impression_count = None

    if duration_or_impression[0] == 'd':
        # It's a duration
        duration = duration_or_impression[1:]
        if not duration.isdigit():
            await message.reply_text("Duration must be a number.")
            return
        expiry_date = datetime.now() + timedelta(days=int(duration))
    elif duration_or_impression[0] == 'i':
        # It's an impression count
        impression = duration_or_impression[1:]
        if not impression.isdigit():
            await message.reply_text("Impression count must be a number.")
            return
        impression_count = int(impression)
    else:
        await message.reply_text("Invalid prefix. Use 'd' for duration and 'i' for impression count.")
        return

    reply = message.reply_to_message
    if not reply:
        await message.reply_text("Reply to a message to set it as your advertisement.")
        return

    await update_advirtisment(reply.text, ads_name, expiry_date, impression_count)
    await asyncio.sleep(3)
    _, name, _ = await get_advirtisment()
    await message.reply_text(f"Advertisement: '{name}' has been set.")