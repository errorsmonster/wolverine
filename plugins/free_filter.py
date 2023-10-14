import asyncio
import re
import math
import time
from Script import script
from info import SLOW_MODE_DELAY
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from database.users_chats_db import db
from pyrogram.errors import MessageNotModified
from utils import get_size, replace_blacklist, temp
from database.ia_filterdb import get_search_results
from plugins.shortner import linkgen


BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST
slow_mode = SLOW_MODE_DELAY


@Client.on_callback_query(filters.regex(r"^free"))
async def free_next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("ok")
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return

    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await linkgen(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
        file_link = f"🎬 [{get_size(file.file_size)} ~ {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []    
    btn.append([
            InlineKeyboardButton("Upgrade", url=f"https://t.me/{temp.U_NAME}?start=upgrade"),
            InlineKeyboardButton("Refer", url=f"https://t.me/{temp.U_NAME}?start=refer")
            ],[
            InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5")])

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10

    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"free_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"free_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"free_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"free_{req}_{key}_{n_offset}")
            ],
        )
    try:
         await query.edit_message_text(
            text=search_results_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()



async def free_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                return
        else:
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
       
    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await linkgen(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
        file_link = f"🎬 [{get_size(file.file_size)} ~ {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []  
    btn.append([
            InlineKeyboardButton("Upgrade", url=f"https://t.me/{temp.U_NAME}?start=upgrade"),
            InlineKeyboardButton("Refer", url=f"https://t.me/{temp.U_NAME}?start=refer")
            ],[
            InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5")])

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"free_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    cap = f"Here is what i found for your query {search}"
    m = await message.reply_text(text=f"**{cap}**\n\n{search_results_text}", reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    await db.update_timestamps(message.from_user.id, int(time.time()))
    # delete msg after 2 min
    await asyncio.sleep(120)
    await m.delete()