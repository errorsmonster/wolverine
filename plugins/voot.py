import re
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils import get_shortlink
from database.users_chats_db import db


#voot function 
@Client.on_message(filters.private & filters.text & filters.regex("https://www.voot.com/(shows|movie)/(.*)"))
async def link_voot(client, message):
    regex = re.compile(r"https://www.voot.com/(shows|movie)/(.*)")
    match = regex.match(message.text)
    if not match:
        await message.reply("Invalid link")
    try:
        proce = await message.reply("**Processing...**")
        await asyncio.sleep(1)
        data = await get_voot(message.text)
        await proce.delete()

        title, description, thumbnail, video_url = (data[k] for k in ("title", "description", "thumnail", "Video_URL"))
        video_url = await get_shortlink(video_url) if not await db.is_premium_status(message.from_user.id) else video_url
        vot = await message.reply_photo(
            photo = f"{thumbnail}",
            caption = f"**{title}**\n\n`{description}`",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Watch', url=video_url)]]
            )
        )
        await asyncio.sleep(600)
        await vot.delete()

    except Exception as e:
        data = await get_voot(message.text)
        emsg = data["message"]
        await message.reply(f'𝐄𝐫𝐫𝐨𝐫: `{emsg}`', quote=True)

#voot response 
async def get_voot(link):
    url = "https://api.voot2.workers.dev/"
    params = {'q': link}

    # Replace '&' with '?' in the params dictionary
    params = {k.replace('&', '?'): v for k, v in params.items()}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, raise_for_status=True) as response:
            return await response.json()