import asyncio
import re
import math
import time
from Script import script
from info import SLOW_MODE_DELAY, WAIT_TIME
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from database.users_chats_db import db
from pyrogram.errors import MessageNotModified
from utils import get_size, get_settings, replace_blacklist, temp
from database.ia_filterdb import get_search_results


BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST
slow_mode = SLOW_MODE_DELAY
waitime = WAIT_TIME


@Client.on_callback_query(filters.regex(r"^forward"))
async def paids_next_page(bot, query):
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
    settings = await get_settings(query.message.chat.id)
    if settings['button']:
        btn = [
        [
            InlineKeyboardButton(
                text=f"[{get_size(file.file_size)}] {await replace_blacklist(file.file_name, blacklist)}",
                callback_data=f'files#{file.file_id}'
                )
            ]
        for file in files
        ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"forward_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"forward_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"forward_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"forward_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer() 



# paid filter for premium user only
async def paids_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        if message.text.startswith("/"):
            return  # ignore commands

        if re.match(r"(^\/|^,|^!|^\.|^[\U0001F600-\U000E007F])", message.text):
            return

        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)

            if not files:
                await message.reply_text("No Results Found. Try Another Keyword.")
                return

        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll

    pre = 'file'
    btn = [
        [
            InlineKeyboardButton(
                text=f"[{get_size(file.file_size)}] {await replace_blacklist(file.file_name, blacklist)}",
                callback_data=f'{pre}#{file.file_id}'
                )
            ]
        for file in files
        ]

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"forward_{req}_{key}_{offset}")]
        )
    else:
        btn.append([InlineKeyboardButton(text="🗓 1/1", callback_data="pages")])

    cap = f"Here is what I found for your query {search}"
    await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))

    if spoll:
        await msg.message.delete()


@Client.on_callback_query(filters.regex(r"^paidnext"))
async def paid_next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    # get user name in query.answer
    m = int(req)
    k = await bot.get_users(m)
    name = k.first_name if not k.last_name else k.first_name + " " + k.last_name
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(f"That's not for you buddy!\nOnly ~{name} can access this query", show_alert=True)
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
    settings = await get_settings(query.message.chat.id)
    if settings['button']:
        # Construct a text message with hyperlinks
        search_results_text = []
        for file in files:
            shortlink = f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}"
            file_link = f"🎬 [{get_size(file.file_size)} ~ {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
            search_results_text.append(file_link)

        search_results_text = "\n\n".join(search_results_text)

    btn = []
    btn.append([InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5")])
    
    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"paidnext_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"paidnext_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"paidnext_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"paidnext_{req}_{key}_{n_offset}")
            ],
        )
    try:
         m = await query.edit_message_text(
            text=search_results_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
         # delete msg after 5 min
         await asyncio.sleep(300)
         await m.delete()

    except MessageNotModified:
        pass
    await query.answer()


async def paid_filter(client, msg, spoll=False):
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
        shortlink = f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}"
        file_link = f"🎬 [{get_size(file.file_size)} ~ {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []   
    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"paidnext_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    cap = f"Here is what i found for your query {search}"
    m = await message.reply_text(text=f"**{cap}**\n\n{search_results_text}", reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    await db.update_timestamps(message.from_user.id, int(time.time()))
    if waitime is not None:
        await asyncio.sleep(waitime)
        await m.delete()