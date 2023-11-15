import asyncio
import re
import ast
import math
import time
from datetime import datetime, timedelta
from urllib.parse import quote
from Script import script
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, BIN_CHANNEL, URL, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, AUTH_GROUPS, SLOW_MODE_DELAY, FORCESUB_CHANNEL, ONE_LINK_ONE_FILE, ACCESS_GROUPS, WAIT_TIME, MAINTAINENCE_MODE, PROFANITY_FILTER
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from database.top_msg import mdb
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, replace_blacklist
from plugins.shortner import get_shortlink
from plugins.paid_filter import paid_filter
from plugins.free_filter import free_filter
from profanity import profanity
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST
slow_mode = SLOW_MODE_DELAY
waitime = WAIT_TIME


@Client.on_message(filters.private & filters.text & filters.incoming)
async def filters_private_handlers(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    if message.text.startswith("/"):
        return
  
    await mdb.update_top_messages(message.from_user.id, message.text)    

    now = datetime.now()
    tody = int(now.timestamp())
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    user_timestamps = user.get("timestamps")
    files_counts = user.get("files_count")
    premium_status = await db.is_premium_status(user_id)
    last_reset = user.get("last_reset")
    referral = await db.get_refferal_count(user_id)
    duration = user.get("premium_expiry")

    # optinal function for checking time difference between currrent time and next 12'o clock
    current_datetime = datetime.now()
    next_day = current_datetime + timedelta(days=1)
    next_day_midnight = datetime(next_day.year, next_day.month, next_day.day)
    time_difference = (next_day_midnight - current_datetime).total_seconds() / 3600
    time_difference = round(time_difference)
 
    # Todays Date
    today = datetime.now().strftime("%Y-%m-%d")

    if referral is None or referral <= 0:
        await db.update_refferal_count(user_id, 0)

    if referral is not None and referral >= 100:
        await db.update_refferal_count(user_id, referral - 100)
        await db.add_user_as_premium(user_id, 28, tody)
        await message.reply_text(f"**Congratulations! {message.from_user.mention},\nYou Have Received 1 Month Premium Subscription For Inviting 10 Users.**", disable_web_page_preview=True)
        return
        
    if last_reset != today:
        await db.reset_all_files_count()
        await mdb.delete_all_messages()
        return 
    
    if MAINTAINENCE_MODE == True:
        await message.reply_text(f"<b>Sorry For The Inconvenience, We Are Under Maintenance. Please Try Again Later, or Try This Bot Instead <a href=https://t.me/flimrobot>R O S I E</a></b>", disable_web_page_preview=True)
        return
 
    msg = await message.reply_text(f"<b>Searching For Your Request...</b>", reply_to_message_id=message.id)
    
    if 2 < len(message.text) < 100:
        search = message.text.lower()
        encoded_search = quote(search)
    
        files, offset, total_results = await get_search_results(search, offset=0, filter=True)
        if not files:
            google = "https://google.com/search?q="
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Check Your Spelling", url=f"{google}{encoded_search}%20movie")],
                [InlineKeyboardButton("🗓 Check Release Date", url=f"{google}{encoded_search}%20release%20date")]
            ])
            await msg.edit(
                text="<b>I couldn't find a movie in my database. Please check the spelling or the release date and try again.</b>",
                reply_markup=reply_markup,
            )
            return
    try:
        if premium_status is True:
            is_expired = await db.check_expired_users(user_id)
            
            if is_expired:
                await msg.edit(f"<b>Your Premium Subscription Has Been Expired. Please <a href=https://t.me/{temp.U_NAME}?start=upgrade>Renew</a> Your Subscription To Continue Using Premium.</b>", disable_web_page_preview=True)
                return
            
            if files_counts is not None and files_counts >= 50:
                await msg.edit(f"<b>Your Account Has Been Terminated Due To Misuse, And It'll Be Unlocked After {time_difference} Hours.</b>")
                return
            
            if duration == 29:
                if files_counts is not None and files_counts >= 20:
                    await msg.edit(f"<b>You Can Only Get 20 Files a Day, Please Wait For {time_difference} Hours To Request Again</b>")
                    return
                
            # call auto filter
            text, markup = await paid_filter(client, message)
            m = await msg.edit(text=text, reply_markup=markup, disable_web_page_preview=True)

        else:
            if user_timestamps:
                current_time = int(time.time())
                time_diff = current_time - user_timestamps
                if time_diff < slow_mode:
                    remaining_time = slow_mode - time_diff
                    while remaining_time > 0:
                        await msg.edit(f"<b>Please Wait For {remaining_time} Seconds Before Sending Another Request.</b>")
                        await asyncio.sleep(2)
                        current_time = int(time.time())
                        time_diff = current_time - user_timestamps
                        remaining_time = max(0, slow_mode - time_diff)
                    await message.delete()
                    await msg.delete()
                    return
                
            if files_counts is not None and files_counts >= 10:
                await message.reply(
                    f"<b>You Have Reached Your Daily Limit. Please Try After {time_difference} Hours, or  <a href=https://t.me/{temp.U_NAME}?start=upgrade>Upgrade</a> To Premium For Unlimited Request</b>",
                    disable_web_page_preview=True)
                return
        
            auto, keyboard = await auto_filter(client, message)
            free, button = await free_filter(client, message)
            if ONE_LINK_ONE_FILE:
                if files_counts is not None and files_counts >= 1:
                    m = await msg.edit(text=free, reply_markup=button, disable_web_page_preview=True)
                else:
                    m = await msg.edit(text=auto, reply_markup=keyboard, disable_web_page_preview=True)
            else:
                m = await msg.edit(text=auto, reply_markup=keyboard, disable_web_page_preview=True)
 
    except Exception as e:
        print(e)
        await msg.edit(f"<b>Opps! Something Went Wrong.</b>")

    finally:
        if waitime is not None:
            await asyncio.sleep(waitime)
            await m.delete()


@Client.on_message(filters.group & filters.text & filters.incoming)
async def public_group_filter(client, message):
    group_id = message.chat.id
    title = message.chat.title
    member_count = message.chat.members_count

    # Check if the chat and user exist in the database
    chat_exists = await db.get_chat(group_id)
    user_exists = await db.is_user_exist(message.from_user.id)

    # Add chat or user if they don't exist in the database
    if not chat_exists:
        await db.add_chat(group_id, title)
    if not user_exists:
        await db.add_user(message.from_user.id, message.from_user.first_name)

    # Ignore commands starting with "/"
    if message.text.startswith("/"):
        return 
    
    # Check if the user's message contains any inappropriate words
    if PROFANITY_FILTER:
        if profanity.contains_profanity(message.text):
            await message.delete()        
    
    await mdb.update_top_messages(message.from_user.id, message.text) 
    
    text, markup = await auto_filter(client, message)
    try:
        # Filtering logic
        if group_id in AUTH_GROUPS:
            k = await manual_filters(client, message)
            if not k:
                m = await message.reply(text=text, reply_markup=markup, disable_web_page_preview=True)

        elif group_id in ACCESS_GROUPS or (member_count and member_count > 500):
            m = await message.reply(text=text, reply_markup=markup, disable_web_page_preview=True)
        
    except Exception as e:
        print(e)

    finally:
        if waitime is not None:
            await asyncio.sleep(waitime)
            await message.delete()
            await m.delete()


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    # get user name in query.answer
    m = int(req)
    k = await bot.get_users(m)
    name = k.first_name if not k.last_name else k.first_name + " " + k.last_name
    if not name:
        name = "Anonymous"
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(f"{name}\ncan only access this query", show_alert=True)
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
            shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
            file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
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
            [InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
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
    

@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("Not for you!")
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('Checking for Movie in database...')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            k = await query.message.edit('This Movie Not Found In DataBase')
            await asyncio.sleep(10)
            await k.delete()

async def delete_files(query, file_type):
    k = await query.message.edit(text=f"Deleting <b>{file_type.upper()}</b> files...", reply_markup=None)
    files, _, _ = await get_search_results(file_type.lower(), max_results=100, offset=0)
    deleted = 0

    for file in files:
        file_ids = file.file_id
        result = await Media.collection.delete_one({'_id': file_ids})

        if result.deleted_count:
            logger.info(f'{file_type.capitalize()} File Found! Successfully deleted from database.')

        deleted += 1

    deleted = str(deleted)
    await k.edit_text(text=f"<b>Successfully deleted {deleted} {file_type.upper()} files.</b>")

    

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Share & Support Us♥️')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Share & Support Us♥️')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Share & Support Us♥️')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Share & Support Us♥️')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('Share & Support Us♥️')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Share & Support Us♥️')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Share & Support Us♥️')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Share & Support Us♥️')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                media_id=await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f"<code>{await replace_blacklist(f_caption, blacklist)}</code>\n<a href=https://t.me/iPrimeHub>©PrimeHub™</a>",
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('Check PM, I have sent files in pm', show_alert=True)
                del_msg = await client.send_message(
                    text=f"<b>File will be deleted in 10 mins. Save or forward immediately.<b>",
                    chat_id=query.from_user.id,
                    reply_to_message_id=media_id.id
                    )
                await asyncio.sleep(waitime or 600)
                await media_id.delete()
                await del_msg.edit("__⊘ This message was deleted__")

        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if FORCESUB_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Please Join My Channel Then Click Try Again 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        md_id=await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f"<code>{await replace_blacklist(f_caption, blacklist)}</code>\n<a href=https://t.me/iPrimeHub>©PrimeHub™</a>",
            protect_content=True if ident == 'checksubp' else False
        )
        del_msg = await client.send_message(
            text=f"<b>File will be deleted in 10 mins. Save or forward immediately.<b>",
            chat_id=query.from_user.id,
            reply_to_message_id=md_id.id
            )
        await asyncio.sleep(waitime or 600)
        await md_id.delete()
        await del_msg.edit("__⊘ This message was deleted__")

    elif query.data == "pages":
        await query.answer('Share & Support Us♥️')
    elif query.data == "home":
        buttons = [[
                    InlineKeyboardButton('💡 How To Download', url=f"https://t.me/QuickAnnounce/5")
                    ],[
                    InlineKeyboardButton('📎 Refer', callback_data="refer"),
                    InlineKeyboardButton('🔥 Top Search', callback_data="topsearch")
                    ],[
                    InlineKeyboardButton('🎟️ Upgrade ', callback_data="remads"),
                    InlineKeyboardButton('🗣️ Request', callback_data="request")
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit(
        text=script.START_TXT.format(query.from_user.mention, temp.B_NAME),
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        )
    elif query.data == "close_data":
        await query.message.delete()
    elif query.data == "request":
        buttons = [[
                    InlineKeyboardButton('📽️ Request Group', url="https://t.me/PrimehubReq"),
                    InlineKeyboardButton('◀️ Back', callback_data="home")
                ]]
        await query.message.edit(
        text=script.REQM,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
        )                    
    elif query.data == "remads":
        buttons = [[
                    InlineKeyboardButton('💫 Confirm', callback_data="confirm"),
                    InlineKeyboardButton('◀️ Back', callback_data="home")
                ]]
        await query.message.edit(
        text=script.REMADS_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
        )
    elif query.data == "confirm":
        buttons = [[
                    InlineKeyboardButton('📣 Help', url="https://t.me/lemx4"),
                    InlineKeyboardButton('◀️ Back', callback_data="remads"),
                ]]
        await query.message.edit(
        text=script.CNFRM_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
        )

    elif query.data == "refer":
        user_id = query.from_user.id
        referral_points = await db.get_refferal_count(user_id)
        refferal_link = f"https://t.me/{temp.U_NAME}?start=ReferID-{user_id}"
        buttons = [[
                    InlineKeyboardButton('🎐 Invite', url=f"https://telegram.me/share/url?url={refferal_link}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83"),
                    InlineKeyboardButton(f"🟢 {referral_points}", callback_data="refer_point"),
                    InlineKeyboardButton('◀️ Back', callback_data="home")
                ]]
        await query.message.edit(
            text=f"<b>Here is your refferal link:\n\n{refferal_link}\n\nShare this link with your friends, Each time they join, Both of you will get 10 refferal points and after 100 points you will get 1 month premium subscription.</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )

    elif query.data == "refer_point":
        user_id = query.from_user.id
        referral_points = await db.get_refferal_count(user_id)
        await query.answer(f"You have {referral_points} refferal points.", show_alert=True
        )
                                         
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('Share & Support Us♥️')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)

    # Function to delete unwanted files
    elif query.data == "delback":
        keyboard_buttons = [
            ["PreDVD", "PreDVDRip"],
            ["HDTS", "HDTC"],
            ["HDCam", "HD-Cams"],
            ["CamRip", "S-Print"]
        ]

        btn = [
            [InlineKeyboardButton(button, callback_data=button.lower().replace("-", "")) for button in row]
            for row in keyboard_buttons
        ]
        btn.append(
            [InlineKeyboardButton("Close", callback_data="close_data")]
            )

        await query.message.edit(
            text="<b>Select The Type Of Files You Want To Delete..?</b>",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        
    elif query.data in ["predvd", "camrip", "predvdrip", "hdcam", "hdcams", "sprint", "hdts", "hq", "hdtc"]:
        buttons = [[
            InlineKeyboardButton('Hell No', callback_data=f"confirm_no")
            ],[           
            InlineKeyboardButton('Yes, Delete', callback_data=f"confirm_yes#{query.data}")
            ],[
            InlineKeyboardButton('⛔️ Close', callback_data="close_data"),
            InlineKeyboardButton('◀️ Back', callback_data="delback")
        ]]
        await query.message.edit(
            text=f"<b>Are You Sure To Delete {query.data.upper()} Files?</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    elif query.data.startswith("confirm_yes#"):
        file_type = query.data.split("#")[1]
        await delete_files(query, file_type)
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
            text, markup = await callback_paid_filter(query, search)
            await query.message.edit(text=f"<b>{text}</b>", reply_markup=markup, disable_web_page_preview=True)
        else:    
            text, markup = await callback_auto_filter(query, search)
            await query.message.edit(text=f"<b>{text}</b>", reply_markup=markup, disable_web_page_preview=True)
 
    # get download button
    elif query.data.startswith("download#"):
        file_id = query.data.split("#")[1]
        msg = await client.send_cached_media(
            chat_id=BIN_CHANNEL,
            file_id=file_id)
        await client.send_message(
            text=f"<b>Requested By</b>:{query.from_user.mention}  <code>{query.from_user.id}</code>",
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

    await query.answer('Share & Support Us♥️')

    
async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
    if settings["button"]:
        # Construct a text message with hyperlinks
        search_results_text = []
        for file in files:
            shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
            file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
            search_results_text.append(file_link)

        search_results_text = "\n\n".join(search_results_text)

    btn = []   
    btn.append([
            InlineKeyboardButton("🪙 Upgrade", url=f"https://t.me/{temp.U_NAME}?start=upgrade"),
            InlineKeyboardButton("🔗 Refer", url=f"https://t.me/{temp.U_NAME}?start=refer")
        ])
    
    btn.append([InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5")])
    
    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    cap = f"Here is what i found for your query {search}"
    # add timestamp to database for floodwait
    await db.update_timestamps(message.from_user.id, int(time.time()))
    return f"<b>{cap}\n\n{search_results_text}</b>", InlineKeyboardMarkup(btn)

# callback autofilter
async def callback_auto_filter(query, msg, spoll=False):
    search=msg
    files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
        file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []   
    if offset != "":
        message = query.message
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = query.from_user.id if query.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"free_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    cap = f"Here is what i found for your query {search}"
    return f"<b>{cap}\n\n{search_results_text}</b>", InlineKeyboardMarkup(btn)

# callback autofilter
async def callback_paid_filter(query, msg, spoll=False):
    search=msg
    files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
    # Construct a text message with hyperlinks
    search_results_text = []
    for file in files:
        shortlink = f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}"
        file_link = f"🎬 [{get_size(file.file_size)} | {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
        search_results_text.append(file_link)

    search_results_text = "\n\n".join(search_results_text)

    btn = []
    if offset != "":
        message = query.message
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = query.from_user.id if query.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"free_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    cap = f"Here is what i found for your query {search}"
    return f"<b>{cap}\n\n{search_results_text}</b>", InlineKeyboardMarkup(btn)


async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("I couldn't find any movie in that name.")
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        k = await msg.reply("**I couldn't find anything related to that. Check your spelling**")
        await asyncio.sleep(15)
        await k.delete()
        return
    SPELL_CHECK[msg.id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    m = await msg.reply("I couldn't find anything related to that\nDid you mean any one of these?",
                    reply_markup=InlineKeyboardMarkup(btn))
    if waitime is not None:
        await asyncio.sleep(waitime)
        await m.delete()
    
async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False