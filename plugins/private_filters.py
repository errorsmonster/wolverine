import re
import math
from Script import script
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from pyrogram.errors import MessageNotModified
from utils import get_size, get_settings, replace_blacklist
from database.ia_filterdb import get_search_results
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST


@Client.on_message(filters.private & filters.text & filters.incoming)
async def private_filter(client, message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id)
        
    if await db.is_premium_status(user_id) is True:
        await paid_filter(client, message)
    else:
        await paid_filter(client, message)
        
        
        
@Client.on_callback_query(filters.regex(r"^pnext"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("oKda", show_alert=True)
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
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
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
            [InlineKeyboardButton("⏪ BACK", callback_data=f"pnext_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"pnext_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"pnext_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"pnext_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer() 


async def paid_filter(client, msg, spoll=False):
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
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"pnext_{req}_{key}_{offset}")]
        )
    else:
        btn.append([InlineKeyboardButton(text="🗓 1/1", callback_data="pages")])

    cap = f"Here is what I found for your query {search}"
    await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))

    if spoll:
        await msg.message.delete()
