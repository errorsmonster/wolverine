import asyncio
import re
import aiohttp
import ast
from urllib.parse import quote
from Script import script
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, AUTH_GROUPS, SLOW_MODE_DELAY, FORCESUB_CHANNEL, ACCESS_GROUPS, WAIT_TIME, BIN_CHANNEL, URL, ACCESS_KEY
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from database.config_panel import mdb
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, replace_blacklist, fetch_quote_content
from database.ia_filterdb import Media, get_file_details, get_search_results
from plugins.pm_filter import callback_auto_filter, callback_paid_filter
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging
import base64


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}




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
                    caption=f"<code>{await replace_blacklist(f_caption, script.BLACKLIST)}</code>\n<a href=https://t.me/iPrimeHub>©PrimeHub™</a>",
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('Check PM, I have sent files in pm', show_alert=True)
                del_msg = await client.send_message(
                    text=f"<b>File will be deleted in 10 mins. Save or forward immediately.<b>",
                    chat_id=query.from_user.id,
                    reply_to_message_id=media_id.id
                    )
                await asyncio.sleep(WAIT_TIME or 600)
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
            caption=f"<code>{await replace_blacklist(f_caption, script.BLACKLIST)}</code>\n<a href=https://t.me/iPrimeHub>©PrimeHub™</a>",
            protect_content=True if ident == 'checksubp' else False
        )
        del_msg = await client.send_message(
            text=f"<b>File will be deleted in 10 mins. Save or forward immediately.<b>",
            chat_id=query.from_user.id,
            reply_to_message_id=md_id.id
            )
        await asyncio.sleep(WAIT_TIME or 600)
        await md_id.delete()
        await del_msg.edit("__⊘ This message was deleted__")

    elif query.data == "pages":
        qoute = await fetch_quote_content()
        await query.answer(f"**{qoute}**", show_alert=True)
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
        if not await db.is_user_exist(query.from_user.id):
            await db.add_user(
                query.from_user.id,
                query.from_user.first_name
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

    # generate redeem code
    elif query.data.startswith("redeem"):
        buttons = [[
            InlineKeyboardButton("1 Month", callback_data="Reedem#1")
            ],[
            InlineKeyboardButton("3 Months", callback_data="Reedem#3")
            ],[
            InlineKeyboardButton("6 Months", callback_data="Reedem#6")
            ]]
        await query.message.edit(
            f"<b>Choose the duration</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    elif query.data.startswith("Reedem#"):
        duration = query.data.split("#")[1:]
        buttons = [[
            InlineKeyboardButton("1 Redeem Code", callback_data=f"license#{duration}#1")
            ],[
            InlineKeyboardButton("5 Redeem Codes", callback_data=f"license#{duration}#5")
            ],[
            InlineKeyboardButton("10 Redeem Codes", callback_data=f"license#{duration}#10")
            ]]  
        await query.message.edit(f"<b>How many redeem codes you want?</b>", 
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )    
    elif query.data.startswith("license#"):
        duration, count = query.data.split("#")[1:]
        encoded_duration = base64.b64encode(str(duration).zfill(3).encode()).decode('utf-8').rstrip('=')

        codes_generated = []
        for _ in range(int(count)):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://licensegen.onrender.com/?access_key={ACCESS_KEY}&action=generate&days=90") as resp:
                    if resp.status == 200:
                        json_response = await resp.json()
                        license_code = f"{json_response.get('license_code')[:10]}{encoded_duration}{json_response.get('license_code')[10:]}"
                        codes_generated.append(license_code)
                    else:
                        await query.answer(f"Error generating license code.{resp.status}", show_alert=True)
                        return
                
        codes_str = "\n".join(f"`{code}`" for code in codes_generated)
        await query.message.edit(f"<b>Redeem codes:</b>\n\n{codes_str}")


     #maintainance
    elif query.data == "maintenance":
        config = await mdb.get_configuration_value("maintenance_mode")
        print(f"Maintainance Mode: {config}")
        if config is True:
            await mdb.update_configuration("maintenance_mode", False)
            await query.message.edit(f"<b>Maintenance mode disabled.</b>", reply_markup=None)
        else:
            await mdb.update_configuration("maintenance_mode", True)
            await query.message.edit(f"<b>Maintenance mode enabled.</b>", reply_markup=None)

    elif query.data == "1link1file":
        config = await mdb.get_configuration_value("one_link")
        print(f"One Link: {config}")
        if config is True:
            await mdb.update_configuration("one_link", False)
            await query.message.edit(f"<b>One link One file disabled.</b>", reply_markup=None)
        else:
            await mdb.update_configuration("one_link", True)
            await query.message.edit(f"<b>One link One file enabled.</b>", reply_markup=None)

    elif query.data == "autoapprove":
        config = await mdb.get_configuration_value("auto_accept")
        print(f"Auto Approve: {config}")
        if config is True:
            await mdb.update_configuration("auto_accept", False)
            await query.message.edit(f"<b>Auto approve disabled.</b>", reply_markup=None)
        else:
            await mdb.update_configuration("auto_accept", True)
            await query.message.edit(f"<b>Auto approve enabled.</b>", reply_markup=None)

    elif query.data == "private_filter":
        config = await mdb.get_configuration_value("private_filter")
        print(f"Private Filter: {config}")
        if config is True:
            await mdb.update_configuration("private_filter", False)
            await query.message.edit(f"<b>Private filter disabled.</b>", reply_markup=None)
        else:
            await mdb.update_configuration("private_filter", True)
            await query.message.edit(f"<b>Private filter enabled.</b>", reply_markup=None)              

                
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