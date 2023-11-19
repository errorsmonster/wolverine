from pyrogram import Client, filters
from database.ia_filterdb import get_file_details, get_search_results, get_all_file_ids
from info import FORWARD_CHANNEL, ADMINS
from pyrogram.errors import FloodWait
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR)

cancel_forwarding = False


async def forward_file(client, file_id, caption):
    try:
        await client.send_cached_media(
            chat_id=FORWARD_CHANNEL,
            file_id=file_id,
            caption=caption,
        )
        return True
    except Exception as e:
        logging.error(f"Error forwarding file: {e}")
        return False


async def get_files_from_database(client, message, file_type):
    global cancel_forwarding
    m = await message.reply_text(text=f"**Fetching files from the database.**")
    
    cancel_forwarding = False
    
    files, _, _ = await get_search_results(file_type, max_results=1000000, offset=0)
    total = 0
    for file in files:
        if cancel_forwarding:
            await m.edit("**File forwarding process has been canceled.**")
            return

        file_id = file.file_id
        file_details = await get_file_details(file_id)
        file_info = file_details[0]
        caption = file_info.caption or file_info.file_name
        try:
            success = await forward_file(client, file_id, caption)
            if success:
                total += 1
                await m.edit(f"**{total}** files have been forwarded.")
        except FloodWait as e:
            logging.warning(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)

    await m.edit(f"**Successfully forwarded {total} files from the database.**")


async def get_files_from_db(client, message):
    global cancel_forwarding
    m = await message.reply_text(text=f"**Fetching files from the database.**")
    
    cancel_forwarding = False
    
    files = await get_all_file_ids()
    total = 0
    for file in files:
        if cancel_forwarding:
            await m.edit("**File forwarding process has been canceled.**")
            return

        file_id = file
        logging.warning(file_id)
        file_details = await get_file_details(file_id)
        file_info = file_details[0]
        caption = file_info.caption or file_info.file_name
        try:
            success = await forward_file(client, file_id, caption)
            if success:
                total += 1
                await m.edit(f"**{total}** files have been forwarded.")
        except FloodWait as e:
            logging.warning(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)

    await m.edit(f"**Successfully forwarded {total} files from the database.**")


@Client.on_message(filters.command("copydb") & filters.user(ADMINS))
async def copydb_command(client, message):
    global cancel_forwarding

    if len(message.command) > 1:
        sub_command = message.command[1].lower()
        if sub_command == "cancel":
            cancel_forwarding = True
            await message.reply("**File forwarding canceled.**")
            return
    file_type = "mkv"
    try:
        await get_files_from_db(client, message)
    except Exception as e:
        await message.reply(f"**Error: {e}**")
