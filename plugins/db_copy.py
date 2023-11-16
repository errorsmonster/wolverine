from pyrogram import Client, filters
from database.ia_filterdb import get_file_details, get_search_results
from info import FORWARD_CHANNEL, ADMINS
from pyrogram.errors import FloodWait
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR)

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
    total = 0
    m = await message.reply_text(
        text=f"**Fetching files from the database and forwarding**",
    ) 

    files, _, _ = await get_search_results(file_type, max_results=1000000, offset=0)
    for file in files:
        file_id = file.file_id
        file_details = await get_file_details(file_id)
        file_info = file_details[0]
        caption = file_info.caption or file_info.file_name

        try:
            success = await forward_file(client, file_id, caption)
            await m.edit(
                text=f"**Total - {total}**",
            )
            if success:
                total += 1
        except FloodWait as e:
            logging.warning(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)

    await m.edit(f"**Successfully forwarded {total} files from the database.**")


@Client.on_message(filters.command("copy_database") & filters.user(ADMINS))
async def get_files(client, message):
    m = await message.reply_text("**Forwarding files from the database**")
    file_type = "mkv"
    try:
        await get_files_from_database(client, message, file_type)
        await m.edit("**Successfully forwarded all files from the database.**")
    except Exception as e:
        await m.edit(f"**Error: {e}**")
