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
    m = await message.reply_text(text=f"Fetching files from the database.") 
    files, _, _ = await get_search_results(file_type, max_results=1000000, offset=0)
    total = 0
    for file in files:
        file_id = file.file_id
        file_details = await get_file_details(file_id)
        file_info = file_details[0]
        caption = file_info.caption or file_info.file_name
        try:
            sucess = await forward_file(client, file_id, caption)
            if sucess:
                total += 1
                await m.edit(f"**{total}** files has been forwarded.")
        except FloodWait as e:
            logging.warning(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)
    await m.edit(f"**Successfully forwarded {total} files from the database.**")


@Client.on_message(filters.command("copydb") & filters.user(ADMINS))
async def get_files(client, message):
    file_type = "mkv"
    try:
        await get_files_from_database(client, message, file_type)
    except Exception as e:
        await message.reply(f"**Error: {e}**")
