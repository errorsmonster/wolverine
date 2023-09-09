import math
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from database.users_chats_db import db
from pyrogram.errors import MessageNotModified
from utils import get_size, temp, get_settings, replace_blacklist
from plugins.shortner import get_shortlink
from database.ia_filterdb import get_search_results
from Script import script


BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST


@Client.on_callback_query(filters.regex(r"^hyper"))
async def hyper_next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("ok")
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return

    settings = await get_settings(query.message.chat.id)

    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
        file_link = f"🎬 [[{get_size(file.file_size)}] {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    # Construct navigation buttons
    btn = []
    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10

    btn.append([InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5"),])    

    if n_offset == 0:
        btn.append([
            InlineKeyboardButton("⏪ BACK", callback_data=f"hyper_{req}_{key}_{off_set}"),
            InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages")
        ])
    elif off_set is None:
        btn.append([
            InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
            InlineKeyboardButton("NEXT ⏩", callback_data=f"hyper_{req}_{key}_{n_offset}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("⏪ BACK", callback_data=f"hyper_{req}_{key}_{off_set}"),
            InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
            InlineKeyboardButton("NEXT ⏩", callback_data=f"hyper_{req}_{key}_{n_offset}")
        ])

    # Edit the message to include hyperlinked text and the inline keyboard
    try:
        await query.edit_message_text(
            text=search_results_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


async def hyper_filter(client, msg, spoll=False):
    if spoll:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    else:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith(("/", ",", "!", ".", "\U0001F600-\U000E007F")):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                return await message.reply_text(f"No Results Found For - {search}. Try Another Keyword.")
        else:
            return

    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
        file_link = f"🎬 [[{get_size(file.file_size)}] {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    page_number = 1 if offset == "" else math.ceil(int(total_results) / 10)

    if page_number > 1:
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        inline_keyboard = [
            [InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5"),],
            [
                InlineKeyboardButton(text=f"🗓 {page_number}", callback_data="pages"),
                InlineKeyboardButton(text="NEXT ⏩", callback_data=f"hyper_{req}_{key}_{offset}")
            ],
        ]
    else:
        inline_keyboard = [
            [InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5"),],
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")],
            ]

    cap = f"Here is what I found for your query {search}"
    await db.update_timestamps(message.from_user.id, int(time.time()))

    # Send the text message with hyperlinks and inline keyboard buttons
    await message.reply_text(
        text=f"**{cap}**\n\n{search_results_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )

    if spoll:
        await msg.message.delete()