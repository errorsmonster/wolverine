import os
import logging
import asyncio
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from database.top_msg import mdb 
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, FORCESUB_CHANNEL, WAIT_TIME
from utils import get_settings, get_size, is_subscribed, temp, replace_blacklist, encode_to_base64, decode_from_base64
from database.connections_mdb import active_connection
from database.ia_filterdb import get_search_results
import re
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}
blacklist = script.BLACKLIST
waitime = WAIT_TIME

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [
            [
                InlineKeyboardButton('Channel', url=f"https://t.me/iPrimeHub"),
                InlineKeyboardButton('Group', url=f"https://t.me/PrimeHubReq")
            ]
            ]

        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup, disable_web_page_preview=True)
        await asyncio.sleep(2)
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return
    
    if not await db.is_user_exist(message.from_user.id) and len(message.command) != 2:
        button = [
            [InlineKeyboardButton("📜 Read Terms", callback_data="terms")],
            [InlineKeyboardButton("✅ Accept", callback_data="home")]
            
        ]
        reply_markup = InlineKeyboardMarkup(button)
        await message.reply(
            f"<b>Welcome to our {temp.B_NAME} Bot! Before using our service, you agree to these Terms & Conditions.Please read them carefully.</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return

    if len(message.command) != 2:
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
        await message.reply_text(
            text=script.START_TXT.format(message.from_user.mention, temp.B_NAME),
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return
    data = message.command[1]
    if not data.split("-", 1)[0] == "ReferID" and FORCESUB_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(FORCESUB_CHANNEL), creates_join_request=True)
        except Exception as e:
            logger.error(e)
        btn = [
            [
                InlineKeyboardButton(
                    "Join", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton("Try Again", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton("Try Again", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Only Channel Subscriber Can Use This Bot**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
            )
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "upgrade", "help"]:
        buttons = [[
                InlineKeyboardButton('💫 Confirm', callback_data="confirm"),
                InlineKeyboardButton('◀️ Back', callback_data="home")
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=script.REMADS_TEXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    if message.command[1] == "topsearch":
        m = await message.reply_text(f"<b>Please Wait, Fetching Top Searches...</b>")
        top_messages = await mdb.get_top_messages(30)

        truncated_messages = []
        for msg in top_messages:
            files, _, _ = await get_search_results(msg.lower(), offset=0, filter=True)
            if files:
                if len(msg) > 30:
                    truncated_messages.append(msg[:30 - 3] + "...")
                else:
                    truncated_messages.append(msg)

        keyboard = []
        for i in range(0, len(truncated_messages), 2):
            row = truncated_messages[i:i+2]
            keyboard.append(row)
    
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, placeholder="Most searches of the day")
        await message.reply_text(f"<b>Here Is The Top Searches Of The Day</b>", reply_markup=reply_markup)
        await m.delete()
        return
    
    # Refer
    if message.command[1] == "refer":
        m = await message.reply_text(f"<b>Generating Your Refferal Link...</b>")
        user_id = message.from_user.id
        referral_points = await db.get_refferal_count(user_id)
        refferal_link = f"https://t.me/{temp.U_NAME}?start=ReferID-{user_id}"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Invite Your Friends", url=f"https://telegram.me/share/url?url={refferal_link}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83")]])
        await m.edit(f"<b>Here is your refferal link:\n\n{refferal_link}\n\nShare this link with your friends, Each time they join, Both of you will be rewarded 10 refferal points and after 50 points you will get 1 month premium subscription.\n\n Referral Points: {referral_points}</b>",
                     reply_markup=keyboard,
                     disable_web_page_preview=True
        )
        return
    

    data = message.command[1].strip()
    if data.startswith("encrypt-"):
        _, rest_of_data = data.split('-', 1)
        userid, file_id = rest_of_data.split('_', 1)
        files_ = await get_file_details(file_id)

        if not files_:
            return await message.reply(f"<b>No such file exists.</b>")

        if userid != str(message.from_user.id):
            return await message.reply(f"<b>You can't access someone else's request, request your own.</b>")
        
        files = files_[0]
        premium_status = await db.is_premium_status(message.from_user.id)
        button = [[
            InlineKeyboardButton("Support", url=f"https://t.me/iPrimehub"),
            InlineKeyboardButton('Request', url=f"https://Telegram.me/PrimeHubReq")
            ]]
        if premium_status is True:
            button.append([InlineKeyboardButton("Watch & Download", callback_data=f"download#{file_id}")])

        media_id = await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f"<code>{await replace_blacklist(files.caption or files.file_name, blacklist)}</code>\n<a href=https://t.me/iPrimeHub>©PrimeHub™</a>",
            reply_markup=InlineKeyboardMarkup(button)
            )
    
        # for counting each files for user
        files_counts = await db.get_files_count(message.from_user.id)
        lifetime_files = await db.get_lifetime_files(message.from_user.id)
        await db.update_files_count(message.from_user.id, files_counts + 1)
        await db.update_lifetime_files(message.from_user.id, lifetime_files + 1)

        del_msg = await client.send_message(
            text=f"<b>File will be deleted in 10 mins. Save or forward immediately.</b>",
            chat_id=message.from_user.id,
            reply_to_message_id=media_id.id)
    
        await asyncio.sleep(waitime or 600)
        await media_id.delete()
        await del_msg.edit("__⊘ This message was deleted__")


    # Referral sysytem
    elif data.split("-", 1)[0] == "ReferID":
        invite_id = int(data.split("-", 1)[1])

        try:
            invited_user = await client.get_users(invite_id)
        except Exception as e:
            print(e)
            return

        if str(invite_id) == str(message.from_user.id):
            inv_link = f"https://t.me/{temp.U_NAME}?start=ReferID-{message.from_user.id}"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Invite Your Friends", url=f"https://telegram.me/share/url?url={inv_link}&text=%F0%9D%90%87%F0%9D%90%9E%F0%9D%90%A5%F0%9D%90%A5%F0%9D%90%A8!%20%F0%9D%90%84%F0%9D%90%B1%F0%9D%90%A9%F0%9D%90%9E%F0%9D%90%AB%F0%9D%90%A2%F0%9D%90%9E%F0%9D%90%A7%F0%9D%90%9C%F0%9D%90%9E%20%F0%9D%90%9A%20%F0%9D%90%9B%F0%9D%90%A8%F0%9D%90%AD%20%F0%9D%90%AD%F0%9D%90%A1%F0%9D%90%9A%F0%9D%90%AD%20%F0%9D%90%A8%F0%9D%90%9F%F0%9D%90%9F%F0%9D%90%9E%F0%9D%90%AB%F0%9D%90%AC%20%F0%9D%90%9A%20%F0%9D%90%AF%F0%9D%90%9A%F0%9D%90%AC%F0%9D%90%AD%20%F0%9D%90%A5%F0%9D%90%A2%F0%9D%90%9B%F0%9D%90%AB%F0%9D%90%9A%F0%9D%90%AB%F0%9D%90%B2%20%F0%9D%90%A8%F0%9D%90%9F%20%F0%9D%90%AE%F0%9D%90%A7%F0%9D%90%A5%F0%9D%90%A2%F0%9D%90%A6%F0%9D%90%A2%F0%9D%90%AD%F0%9D%90%9E%F0%9D%90%9D%20%F0%9D%90%A6%F0%9D%90%A8%F0%9D%90%AF%F0%9D%90%A2%F0%9D%90%9E%F0%9D%90%AC%20%F0%9D%90%9A%F0%9D%90%A7%F0%9D%90%9D%20%F0%9D%90%AC%F0%9D%90%9E%F0%9D%90%AB%F0%9D%90%A2%F0%9D%90%9E%F0%9D%90%AC.")]])
            await message.reply_text(f"<b>You Can't Invite Yourself, Send This Invite Link To Your Friends\n\nInvite Link</b> - \n<code>{inv_link}</code>",
                                    reply_markup=keyboard,
                                    disable_web_page_preview=True)
            return

        if not await db.is_user_exist(message.from_user.id):
            try:
                await db.add_user(message.from_user.id, message.from_user.first_name)
                await asyncio.sleep(1)
                referral = await db.get_refferal_count(invite_id)  # Fetch the current referral count
                await db.update_refferal_count(invite_id, referral + 10)  # Update the referral count
                await asyncio.sleep(1)
                referral_count = await db.get_refferal_count(message.from_user.id)
                await db.update_refferal_count(message.from_user.id, referral_count + 10) # Update the referral count to invted user
                await client.send_message(text=f"You have successfully Invited {message.from_user.mention}", chat_id=invite_id)
                await message.reply_text(f"You have been successfully invited by {invited_user.first_name}", disable_web_page_preview=True)
            except Exception as e:
                print(e)
        else:
            await message.reply_text("You already Invited or Joined")
        return
        

    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("utf-16")).split("_", 1)
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                )
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            f_caption = f"<code>{title}</code>"
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('No such file exist.')
    files = files_[0]
    title = files.file_name
    f_caption=files.caption
    if f_caption is None:
        f_caption = f"{files.file_name}"

    premium_status = await db.is_premium_status(message.from_user.id)
    button = [[
        InlineKeyboardButton("Support", url=f"https://t.me/iPrimehub"),
        InlineKeyboardButton('Request', url=f"https://Telegram.me/PrimeHubReq")
        ]]
    if premium_status is True:
        button.append([InlineKeyboardButton("Watch & Download", callback_data=f"download#{file_id}")])

    media_id = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        protect_content=True if pre == 'filep' else False,
        caption=f"<code>{await replace_blacklist(f_caption, blacklist)}</code>\n<a href=https://t.me/iPrimeHub>©PrimeHub™</a>",
        reply_markup=InlineKeyboardMarkup(button)
        )
    
    # for counting each files for user
    files_counts = await db.get_files_count(message.from_user.id)
    lifetime_files = await db.get_lifetime_files(message.from_user.id)
    await db.update_files_count(message.from_user.id, files_counts + 1)
    await db.update_lifetime_files(message.from_user.id, lifetime_files + 1)
    print(f"File sent {files_counts + 1} to {message.from_user.first_name} - {message.from_user.id}")

    del_msg = await client.send_message(
        text=f"<b>File will be deleted in 10 mins. Save or forward immediately.</b>",
        chat_id=message.from_user.id,
        reply_to_message_id=media_id.id)
    
    await asyncio.sleep(waitime or 600)
    await media_id.delete()
    await del_msg.edit("__⊘ This message was deleted__")

                    
@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('File is successfully deleted from database')
        else:
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('File is successfully deleted from database')
            else:
                await msg.edit('File not found in database')


@Client.on_message(filters.command('deleteallfiles') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Hell No", callback_data="close_data"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Yes", callback_data="autofilter_delete"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def delete_multiple_files(bot, message):
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

    await message.reply_text(
        text="<b>Select The Type Of Files You Want To Delete..?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        quote=True
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('Share & Support Us♥️')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')


@Client.on_message(filters.command('settings') & filters.user(ADMINS))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    settings = await get_settings(grp_id)

    if settings is not None:
        buttons = [
            [
                InlineKeyboardButton(
                    'File Secure',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["file_secure"] else '❌ No',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Spell Check',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["spell_check"] else '❌ No',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_text(
            text=f"<b>Change Your Settings for {title} As Your Wish ⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )

