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
from plugins.shortner import urlshare
from database.config_panel import mdb


BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST
slow_mode = SLOW_MODE_DELAY


@Client.on_callback_query(filters.regex(r"^free"))
async def free_next_page(bot, query):
    _, req, key, offset = query.data.split("_")
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
        shortlink = await urlshare(f"https://telegram.me/{temp.U_NAME}?start=encrypt-{query.from_user.id}_{file.file_id}")
        file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []
    
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
            text=f"<b>{search_results_text}</b>",
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
                if await mdb.get_configuration_value("spoll_check"):
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
       
    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await urlshare(f"https://telegram.me/{temp.U_NAME}?start=encrypt-{message.from_user.id}_{file.file_id}")
        file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []

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
    await db.update_value(message.from_user.id, "timestamps", int(time.time()))
    return f"<b>{cap}\n\n{search_results_text}</b>", InlineKeyboardMarkup(btn)