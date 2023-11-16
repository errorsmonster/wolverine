from database.ia_filterdb import get_file_details, get_search_results
from info import FORWARD_CHANNEL
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

async def get_files_from_database(client, query):
    m = await client.send_message(
        chat_id=FORWARD_CHANNEL,
        text=f"**Fetching files from the database and forwarding**",
    ) 

    files, _, _ = await get_search_results(query, max_results=100, offset=0)
    total = 0


    for file in files:
        file_id = file.file_id
        file_details = await get_file_details(file_id)
        file_info = file_details[0]
        caption = file_info.caption or file_info.file_name

        try:
            await forward_file(client, file_id, caption)
            total += 1
        except FloodWait as e:
            logging.warning(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)

    await m.edit(f"**Successfully forwarded {total} files from the database.**")
