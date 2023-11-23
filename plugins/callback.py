import asyncio
import re
from urllib.parse import quote
from Script import script
from info import ADMINS, BIN_CHANNEL, URL, SLOW_MODE_DELAY, WAIT_TIME
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from database.top_msg import mdb
from utils import get_size, temp, replace_blacklist
from plugins.shortner import get_shortlink
from database.ia_filterdb import Media, get_file_details, get_search_results
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST
slow_mode = SLOW_MODE_DELAY
waitime = WAIT_TIME

@Client.on_callback_query()
async def callbacks_handlers(client: Client, query: CallbackQuery):
    if query.data == "refer":
        user_id = query.from_user.id
        referral_points = await db.get_refferal_count(user_id)
        refferal_link = f"https://t.me/{temp.U_NAME}?start=ReferID-{user_id}"
        buttons = [[
                    InlineKeyboardButton('🎐 Invite', url=f"https://telegram.me/share/url?url={refferal_link}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83"),
                    InlineKeyboardButton(f"🟢 {referral_points}", callback_data="refer_point"),
                    InlineKeyboardButton('◀️ Back', callback_data="home")
                ]]
        await query.message.edit(
            text=f"<b>Here is your refferal link:\n\n{refferal_link}\n\nShare this link with your friends, Each time they join, Both of you will get 10 refferal points and after 50 points you will get 1 month premium subscription.</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )

    elif query.data == "refer_point":
        user_id = query.from_user.id
        referral_points = await db.get_refferal_count(user_id)
        await query.answer(f"You have {referral_points} refferal points.", show_alert=True
        )

    elif query.data == "terms":
        buttons = [[
                    InlineKeyboardButton("✅ Accept Terms", callback_data="home"),
                ]]
        await query.message.edit(
            text=script.TERMS,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    # Function to delete unwanted files
    elif query.data == "delback":
        keyboard_buttons = [
            ["PreDVD", "PreDVDRip"],
            ["HDTS", "HDTC"],
            ["HDCam", "Sample"],
            ["CamRip", "Print"]
        ]

        btn = [
            [InlineKeyboardButton(button, callback_data=button.lower().replace("-", "")) for button in row]
            for row in keyboard_buttons
        ]
        btn.append(
            [InlineKeyboardButton("⛔️ Close", callback_data="close_data")]
            )

        await query.message.edit(
            text="<b>Select The Type Of Files You Want To Delete..?</b>",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        
    elif query.data in ["predvd", "camrip", "predvdrip", "hdcam", "hdcams", "print", "hdts", "sample", "hdtc"]:
        buttons = [[
            InlineKeyboardButton("10", callback_data=f"dlt#10_{query.data}")
            ],[
            InlineKeyboardButton("100", callback_data=f"dlt#100_{query.data}")
            ],[
            InlineKeyboardButton("1000", callback_data=f"dlt#1000_{query.data}")
            ],[
            InlineKeyboardButton('⛔️ Close', callback_data="close_data"),
            InlineKeyboardButton('◀️ Back', callback_data="delback")
        ]]
        await query.message.edit(
            text=f"<b>How Many {query.data.upper()} Files You Want To Delete?</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    
    elif query.data.startswith("dlt#"):
        limit, file_type = query.data.split("#")[1].split("_")
        buttons = [[
            InlineKeyboardButton('Hell No', callback_data=f"confirm_no")
            ],[           
            InlineKeyboardButton('Yes, Delete', callback_data=f"confirm_yes#{limit}_{file_type}")
            ],[
            InlineKeyboardButton('⛔️ Close', callback_data="close_data")
        ]]
        await query.message.edit(
            text=f"<b>Are You Sure To Delete {limit} {file_type.upper()} Files?</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    elif query.data.startswith("confirm_yes#"):
        limits, file_type = query.data.split("#")[1].split("_")
        limit = int(limits)
        await delete_files(query, limit, file_type)

    elif query.data == "confirm_no":
        await query.message.edit(text=f"<b>Deletion canceled.</b>", reply_markup=None)


    # Function for getting the top search results
    elif query.data == "topsearch":

        def is_valid_string(string):
            return bool(re.match('^[a-zA-Z0-9 ]*$', string))

        await query.answer(f"<b>Fetching Top Searches, Be Patience It'll Take Some Time</b>", show_alert=True)
        top_searches = await mdb.get_top_messages(20)

        unique_messages = set()
        truncated_messages = []

        for msg in top_searches:
            if msg.lower() not in unique_messages and is_valid_string(msg):
                unique_messages.add(msg.lower())

                files, _, _ = await get_search_results(msg.lower())
                if files:
                    if len(msg) > 20:
                        truncated_messages.append(msg[:20 - 3])
                    else:
                        truncated_messages.append(msg)

        # Display two buttons in a row
        keyboard = []
        for i in range(0, len(truncated_messages), 2):
            row_buttons = []
            for j in range(2):
                if i + j < len(truncated_messages):
                    msg = truncated_messages[i + j]
                    row_buttons.append(InlineKeyboardButton(msg, callback_data=f"search#{msg}"))
            keyboard.append(row_buttons)

        keyboard.append([
            InlineKeyboardButton("⛔️ Close", callback_data="close_data"),
            InlineKeyboardButton("◀️ Back", callback_data="home")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit(f"<b>Here is the top searches of the day</b>", reply_markup=reply_markup, disable_web_page_preview=True)

    elif query.data.startswith("search#"):
        search = query.data.split("#")[1]
        await query.answer(text=f"Searching for your request :)")
        premium_status = await db.is_premium_status(query.from_user.id)
        if premium_status is True:
            text = await callback_paid_filter(search)
            await query.message.edit(text=f"<b>{text}</b>", disable_web_page_preview=True)
        else:    
            text = await callback_auto_filter(search)
            await query.message.edit(text=f"<b>{text}</b>", disable_web_page_preview=True)
 
    # get download button
    elif query.data.startswith("download#"):
        try:
            file_id = query.data.split("#")[1]
            msg = await client.send_cached_media(
                chat_id=BIN_CHANNEL,
                file_id=file_id)
            await client.send_message(
                text=f"<b>Requested By</b>:\n{query.from_user.mention} <code>{query.from_user.id}</code>\n<b>Link:</b>\n{URL}/watch/{msg.id}",
                chat_id=BIN_CHANNEL,
                disable_web_page_preview=True)
            online = f"{URL}/watch/{msg.id}"
            download = f"{URL}/download/{msg.id}"
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Watch", url=online),
                    InlineKeyboardButton("Download", url=download)
                    ],[
                    InlineKeyboardButton("Close", callback_data='close_data')
                    ]]
            ))
        except Exception as e:
            await query.answer(f"Error:\n{e}", show_alert=True)        


# callback autofilter
async def callback_auto_filter(msg, spoll=False):
    search=msg
    files, _, _ = await get_search_results(search.lower(), offset=0, filter=True)
    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
        file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)
    cap = f"Here is what i found for your query {search}"
    return f"<b>{cap}\n\n{search_results_text}</b>"

# callback autofilter
async def callback_paid_filter(msg, spoll=False):
    search=msg
    files, _, _ = await get_search_results(search.lower(), offset=0, filter=True)
    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}"
        file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)
    cap = f"Here is what i found for your query {search}"
    return f"<b>{cap}\n\n{search_results_text}</b>" 


async def delete_files(query, limit, file_type):
    k = await query.message.edit(text=f"Deleting <b>{file_type.upper()}</b> files...", reply_markup=None)
    files, _, _ = await get_search_results(file_type.lower(), max_results=limit, offset=0)
    deleted = 0

    for file in files:
        file_ids = file.file_id
        result = await Media.collection.delete_one({'_id': file_ids})

        if result.deleted_count:
            logger.info(f'{file_type.capitalize()} File Found! Successfully deleted from database.')

        deleted += 1

    deleted = str(deleted)
    await k.edit_text(text=f"<b>Successfully deleted {deleted} {file_type.upper()} files.</b>")

