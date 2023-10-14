# Kanged From @TroJanZheX
import asyncio
import re
import ast
import math
import time
from datetime import datetime, timedelta
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, SLOW_MODE_DELAY, FORCESUB_CHANNEL, ONE_LINK_ONE_FILE, ACCESS_GROUPS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, replace_blacklist
from plugins.shortner import get_shortlink
from plugins.paid_filter import paid_filter, freemium_filter
from plugins.free_filter import free_filter
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


@Client.on_message(filters.private & filters.text & filters.incoming)
async def filters_private_handlers(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)


    now = datetime.now()
    tody = int(now.timestamp())
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    user_timestamps = user.get("timestamps")
    files_counts = user.get("files_count")
    premium_status = await db.is_premium_status(user_id)
    last_reset = user.get("last_reset")
    referral = await db.get_refferal_count(user_id)

    if referral is None or referral <= 0:
        await db.update_refferal_count(user_id, 0)

    if referral is not None and referral >= 100:
        await db.update_refferal_count(user_id, referral - 100)
        await db.add_user_as_premium(user_id, 28, tody)
        await message.reply_text(f"**Congratulations! {message.from_user.mention},\nYou Have Received 1 Month Premium Subscription For Inviting 10 Users.**", disable_web_page_preview=True)
        return
        
    today = datetime.now().strftime("%Y-%m-%d")

    if last_reset != today:
        await db.reset_all_files_count()
        return    

    if message.text.startswith("/"):
        return
    
    if 2 < len(message.text) < 100:
        search = message.text
        files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
        if not files:
            await message.reply_text("**I Couldn't Find Any Movie In That Name, Please Check The Spelling Or Release Date And Try Again.**", reply_to_message_id=message.id)
            return
    
    msg = await message.reply_text("Searching For Your Request...")

 
    # optinal function for checking time difference between currrent time and next 12'o clock
    current_datetime = datetime.now()
    next_day = current_datetime + timedelta(days=1)
    next_day_midnight = datetime(next_day.year, next_day.month, next_day.day)
    time_difference = (next_day_midnight - current_datetime).total_seconds() / 3600

    try:
        if premium_status is True:
            is_expired = await db.check_expired_users(user_id)
            
            if is_expired:
                await message.reply_text(f"**Your Premium Subscription Has Been Expired. Please <a href=https://t.me/{temp.U_NAME}?start=upgrade>Renew</a> Your Subscription To Continue Using Premium.**", disable_web_page_preview=True)
                return
            
            if files_counts is not None and files_counts >= 50:
                await message.reply_text(f"Your Account Has Been Terminated Due To Misuse, And It'll Be Unlocked After {time_difference} Hours.")
                return
            
            await paid_filter(client, message)
            return

        else:
            if user_timestamps:
                current_time = int(time.time())
                time_diff = current_time - user_timestamps
                if time_diff < slow_mode:
                    remaining_time = slow_mode - time_diff
                    while remaining_time > 0:
                        await msg.edit(f"Please wait for {remaining_time} seconds before sending another request.")
                        await asyncio.sleep(5)
                        current_time = int(time.time())
                        time_diff = current_time - user_timestamps
                        remaining_time = max(0, slow_mode - time_diff)
                    await message.delete()
                    return
                
            if files_counts is not None and files_counts >= 10:
                await message.reply(
                    f"**You Have Reached Your Daily Limit. Please Try After {time_difference} Hours, or  <a href=https://t.me/{temp.U_NAME}?start=upgrade>Upgrade</a> To Premium For Unlimited Request**",
                    disable_web_page_preview=True)
                return
        
            if ONE_LINK_ONE_FILE:
                if files_counts is not None and files_counts >= 1:
                    await free_filter(client, message)
                    return
                else:
                    await auto_filter(client, message)
                    return
            else:
                await auto_filter(client, message)
                return

    except Exception as e:
        await message.reply_text(f"Error: {e}")

    finally:
        await msg.delete()

@Client.on_message(filters.group & filters.text & filters.incoming)
async def public_group_filter(client, message):
    group_id = message.chat.id
    title = message.chat.title
    member_count = message.chat.members_count
    chat = await db.get_chat(group_id)
    
    # add user to db if not exists
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    # Ignore commands starting with "/"
    if message.text.startswith("/"):
        return
    
    if group_id in AUTH_GROUPS:
        k = await manual_filters(client, message)
        if k is False:
            await auto_filter(client, message)
            return

    if group_id in ACCESS_GROUPS:
        await auto_filter(client, message)
        return      

    if member_count is not None and member_count > 500:
        if chat:
            await auto_filter(client, message)
        else:
            await db.add_chat(group_id, title)
    else:
        return



@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
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
            shortlink = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
            file_link = f"🎬 [{get_size(file.file_size)} ~ {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
            search_results_text.append(file_link)

        search_results_text = "\n\n".join(search_results_text)

    btn = []    
    btn.append = ([InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5"),])
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
            text=search_results_text,
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
                    caption=f"<code>{await replace_blacklist(f_caption, blacklist)}</code>\n<code>Uploaded By</code>: <a href=https://t.me/iPrimeHub>PrimeHub</a>",
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('Check PM, I have sent files in pm', show_alert=True)
                del_msg = await client.send_message(
                    text="Files Will Be Deleted Within 10 Mins..\n__Please Make Sure That You Forward These Files To Your Saved Message or Friends.__",
                    chat_id=query.from_user.id)
                await asyncio.sleep(600)
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
            await query.answer("Please Join My Channel Then Try Again 😒", show_alert=True)
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
            caption=f"<code>{await replace_blacklist(f_caption, blacklist)}</code>\n<code>Uploaded By</code>: <a href=https://t.me/iPrimeHub>PrimeHub</a>",
            protect_content=True if ident == 'checksubp' else False
        )
        del_msg = await client.send_message(
            text=f"<b>File will be deleted in 10 mins. Save or forward immediately.<b>",
            chat_id=query.from_user.id,
            reply_to_message_id=md_id.id
            )
        await asyncio.sleep(600)
        await md_id.delete()
        await del_msg.edit("__⊘ This message was deleted__")
    elif query.data == "pages":
        await query.answer('Share & Support Us♥️')
    elif query.data == "home":
        buttons = [[
                    InlineKeyboardButton('💡 How To Download', url=f"https://t.me/QuickAnnounce/5")
                    ],[
                    InlineKeyboardButton('📎 Refer & Get Premium', callback_data="refer"),
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
            text=f"<b>Here is your refferal link:\n\n{refferal_link}\n\nShare this link with your friends, each time they join, Both of you will get 10 refferal points and after 100 points you will get 1 month premium subscription.</b>",
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
            file_link = f"🎬 [{get_size(file.file_size)} ~ {await replace_blacklist(file.file_name, blacklist)}]({shortlink})"
            search_results_text.append(file_link)

        search_results_text = "\n\n".join(search_results_text)

    btn = []  
    btn.append = (
        [
            InlineKeyboardButton("Upgrade", url=f"https://t.me/{temp.U_NAME}?start=upgrade"),
            InlineKeyboardButton("Refer", url=f"https://t.me/{temp.U_NAME}?start=refer")
        ],)
    
    btn.append = ([InlineKeyboardButton("🔴 𝐇𝐎𝐖 𝐓𝐎 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🔴", url="https://t.me/QuickAnnounce/5"),])
    

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
    await message.reply_text(text=f"**{cap}**\n\n{search_results_text}", reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    await db.update_timestamps(message.from_user.id, int(time.time()))
    if spoll:
        await msg.message.delete()


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
        k = await msg.reply("I couldn't find anything related to that. Check your spelling")
        await asyncio.sleep(8)
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
    await msg.reply("I couldn't find anything related to that\nDid you mean any one of these?",
                    reply_markup=InlineKeyboardMarkup(btn))

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
