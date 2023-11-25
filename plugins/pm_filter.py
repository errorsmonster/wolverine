import asyncio
import re
import math
import time
from datetime import datetime, timedelta
from urllib.parse import quote
from Script import script
from info import AUTH_GROUPS, SLOW_MODE_DELAY, ACCESS_GROUPS, WAIT_TIME
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from database.config_panel import mdb
from pyrogram.errors import MessageNotModified
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, replace_blacklist
from plugins.shortner import get_shortlink
from plugins.paid_filter import paid_filter
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
waitime = WAIT_TIME
maintenance_mode = False


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

    maintenance_mode = await mdb.get_configuration_value("maintenance_mode")
    one_file_one_link = await mdb.get_configuration_value("one_link")
    private_filter = await mdb.get_configuration_value("private_filter")

    # Todays Date
    today = datetime.now().strftime("%Y-%m-%d")

    if referral is None or referral <= 0:
        await db.update_refferal_count(user_id, 0)

    if referral is not None and referral >= 50:
        await db.update_refferal_count(user_id, referral - 50)
        await db.add_user_as_premium(user_id, 28, tody)
        await message.reply_text(f"**Congratulations! {message.from_user.mention},\nYou Have Received 1 Month Premium Subscription For Inviting 5 Users.**", disable_web_page_preview=True)
        return
        
    if last_reset != today:
        await db.reset_all_files_count()
        await mdb.delete_all_messages()
        return 
    
    if maintenance_mode is True:
        await message.reply_text(f"<b>Sorry For The Inconvenience, We Are Under Maintenance. Please Try Again Later</b>", disable_web_page_preview=True)
        return
    
    if private_filter is not None and private_filter is False:
        return
 
    msg = await message.reply_text(f"<b>Searching For Your Request...</b>", reply_to_message_id=message.id)
    
    if 1 < len(message.text) < 100:
        search = message.text.lower()
        encoded_search = quote(search)
    
        files, _, _ = await get_search_results(search, offset=0, filter=True)
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
            if one_file_one_link is not None and one_file_one_link is True:
                if files_counts is not None and files_counts >= 1:
                    m = await msg.edit(text=free, reply_markup=button, disable_web_page_preview=True)
                else:
                    m = await msg.edit(text=auto, reply_markup=keyboard, disable_web_page_preview=True)
            else:
                m = await msg.edit(text=auto, reply_markup=keyboard, disable_web_page_preview=True)
 
    except Exception as e:
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
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(f"**{name}**\nonly can access this query", show_alert=True)
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