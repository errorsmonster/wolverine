from pyrogram import Client, filters
from database.ia_filterdb import Media, get_file_details, get_search_results
from info import ADMINS, FORWARD_CHANNEL
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

async def get_files_from_database(client, query, max_results):
    m = await client.send_message(
        chat_id=FORWARD_CHANNEL,
        text=f"**Fetching {max_results} files from the database and forwarding**",
    )

    files, _, _ = await get_search_results(query.lower(), max_results, offset=0)
    total = 0

    for i, file in enumerate(files, start=1):
        file_id = file.file_id
        file_details = await get_file_details(file_id)
        file_info = file_details[0]
        caption = file_info.caption or file_info.file_name

        try:
            success = await forward_file(client, file_id, caption)
            if success:
                logging.info(f"Forwarded file: {caption}")
            total += 1
        except FloodWait as e:
            logging.warning(f"FloodWait: Waiting for {e.x} seconds.")
            await asyncio.sleep(e.x)

        if i % 10 == 0:
            logging.info(f"Forwarded {i}/{len(files)} files from the database.")

    await m.edit(f"**Successfully forwarded {total} files from the database.**")

@Client.on_message(filters.command("copy_database") & filters.user(ADMINS))
async def get_files(client, message):
    m = await message.reply_text("**Forwarding files from the database**")
    total_files = int(await Media.count_documents())
    query = "mkv"

    try:
        await get_files_from_database(client, query, max_results=total_files)
        await m.edit("**Successfully forwarded all files from the database.**")
    except Exception as e:
        await m.edit(f"**Error: {e}**")
