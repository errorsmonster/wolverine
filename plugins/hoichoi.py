import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_shortlink
from database.users_chats_db import db


#hoichoi function 
@Client.on_message(filters.private & filters.text & filters.regex("https://www.hoichoi.tv/(webseries|films|shows|movies)/(.*)"))
async def hoichoi_link_handler(client, message):
    try:
        proc = await message.reply("**Processing...**")
        await asyncio.sleep(1)
        data = await get_hoichoi(message.text)
        await proc.delete()
        title, description, image, download = [data[k] for k in ("title", "description", "image", "download")]
        LQ, MQ, HQ = [d["url"] for d in download[:3]]
        LQ, MQ, HQ = await asyncio.gather(*(get_shortlink(url) for url in (LQ, MQ, HQ))) if not await db.is_premium_status(message.from_user.id) else (LQ, MQ, HQ)
        hich = await message.reply_photo(
            photo=image,
            caption=f"**{title}**\n\n`{description}`",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('270p', url=LQ),
                    InlineKeyboardButton('360p', url=MQ),
                    InlineKeyboardButton('720p', url=HQ)
                ]]
            )
        )
        await asyncio.sleep(600)
        await hich.delete()
    except Exception as e:
        data = await get_hoichoi(message.text)
        emsg = data["msg"]
        await message.reply(f'𝐄𝐫𝐫𝐨𝐫: `{emsg}`', quote=True)


#hoichoi response 
async def get_hoichoi(link):
    url = "http://206.189.128.13:8080/"
    params = {'url': link}

    # Replace '&' with '?' in the params dictionary
    params = {k.replace('&', '?'): v for k, v in params.items()}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, raise_for_status=True) as response:
            return await response.json()