from pyrogram import Client, filters
from database.users_chats_db import db
from info import ADMINS
import asyncio
from Script import script
from info import LOG_CHANNEL
from utils import temp
import re
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from database.ia_filterdb import get_search_results

ADD_PAID_TEXT = "Successfully Enabled {}'s Subscription for {} days"
DEL_PAID_TEXT = "Successfully Removed Subscription for {}"

PATTERN_DOWNLOAD = re.compile(r"\b(how to (?:download|find|search|get)|send me|download link)\b", re.IGNORECASE)

@Client.on_message(filters.regex(PATTERN_DOWNLOAD))
async def how2download(_, message):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("How To Download", url="https://t.me/QuickAnnounce/5")]])
    response_text = "<b>Please watch this video to know how to download movies and series from this bot.</b>"
    await message.reply_text(response_text, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_message(filters.private & filters.regex(r"\b(hi+|hello|hey)\b", re.IGNORECASE))
async def echo(_, message):
    response_text = f"<b>Hello</b>, {message.from_user.mention}!\n<b>I can help you find movies and series. Just send me the name of what you're looking for.</b>"
    await message.reply_text(response_text, disable_web_page_preview=True)

@Client.on_message(filters.media & filters.private & ~filters.user(ADMINS)) 
async def mediasv_filter(client, message):
    m=await message.reply_text("<b>Please don't send any files in my PM. It will be deleted in 60 seconds.</b>", reply_to_message_id=message.id)
    await asyncio.sleep(60)
    await message.delete()
    await m.delete()
    
@Client.on_edited_message(filters.private)
async def editmsg_filter(client, message):
    m = await message.reply_text(text="<b>Instead of editing messages, please send a new one.</b>", reply_to_message_id=message.id)
    await asyncio.sleep(10)
    await m.delete()
    await message.delete()


# Add paid user to database and send message
@Client.on_message(filters.command('add_paid') & filters.user(ADMINS))
async def add_paid(client, message):
    try:
        if len(message.command) < 2:
            raise ValueError

        user_id = int(message.command[1])

        if len(message.command) > 2:
            duration = int(message.command[2])
            if not (1 <= duration <= 365):
                return await message.reply("Duration should be between 1 and 365 days.")
        else:
            duration = 30

        if len(message.command) > 3:
            date_str = message.command[3]
            provided_date = datetime.strptime(date_str, '%d/%m/%Y')
        else:
            provided_date = datetime.now()

        subscription_date= int(provided_date.timestamp())

        user = await client.get_users(user_id)
        name = user.first_name if not user.last_name else f"{user.first_name} {user.last_name}"

        if await db.is_premium_status(user_id):
            return await message.reply(f"**{name}** is already a premium user.")

        await db.add_user_as_premium(user_id, duration, subscription_date)
        await message.reply(f"Premium subscription added for **{name}** for {duration} days.")
        await client.send_message(user_id, f"Your subscription has been enabled for {duration} days.")
    except (ValueError, IndexError, ValueError):
        await message.reply("Invalid input. Please provide a valid user id, optionally a duration (1-365), and optionally a subscription date (dd/mm/yyyy).")

                
# remove paid user from database
@Client.on_message(filters.command('remove_paid') & filters.user(ADMINS))
async def remove_paid(client, message):
    if len(message.command) == 1:
        return await message.reply('Please provide a user id / username')
    chat = message.command[1]
    try:
        chat = int(chat)
    except ValueError:
        pass
    try:
        k = await client.get_users(chat)
    except IndexError:
        return await message.reply("This might be a channel, make sure it's a user.")
    else:
        await db.remove_user_premium(k.id)
        await message.reply(DEL_PAID_TEXT.format(k.first_name))
        
        
#request command 
@Client.on_message(filters.command("request") & filters.private)
async def request(client, message):
    # Strip the command and normalize the movie name
    movie_name = message.text.replace("/request", "").replace("/Request", "").strip()
    files, offset, total_results = await get_search_results(movie_name.lower(), offset=0, filter=True)

    if not movie_name:
        await message.reply_text(script.REQM, disable_web_page_preview=True)
        return
    
    if files:
        await message.reply_text(f"**This movie is already available in our database. Please send movie name directly.**", reply_to_message_id=message.id, disable_web_page_preview=True)

    else:
        await message.reply_text(script.REQ_REPLY.format(movie_name), disable_web_page_preview=True)
        log_message = script.REQ_TEXT.format(temp.B_NAME, message.from_user.mention, message.from_user.id, movie_name)
        await client.send_message(LOG_CHANNEL, log_message, disable_web_page_preview=True)


# reset daily files count        
@Client.on_message(filters.command("resetdaily") & filters.user(ADMINS))
async def resetdaily(client, message):
    m = await message.reply_text("Resetting daily files count...")
    await db.reset_all_files_count()
    await m.edit("Successfully reset daily files count!")

# remove all premium user from database
@Client.on_message(filters.command("remove_all_premium") & filters.user(ADMINS))
async def remove_all_premium(client, message):
    m = await message.reply_text("Removing all premium users...")
    await db.remove_all_premium_users()
    await m.edit("Successfully removed all premium users!")

# list down all premium user from database
@Client.on_message(filters.command("premiumlist") & filters.user(ADMINS))
async def list_premium(client, message):
    m = await message.reply_text("Listing all premium users...")
    count = await db.total_premium_users_count()
    out = f"**List of Premium Users: - {count}**\n\n"
    users = await db.get_all_premium_users()
    async for user in users:
        user_id = user.get("id")
        userx = await client.get_users(user_id)
        user_name = userx.first_name if not userx.last_name else f"{userx.first_name} {userx.last_name}"
        duration = user.get("premium_expiry")
        purchase_date_unix = user.get("purchase_date")
        purchase_date = datetime.fromtimestamp(purchase_date_unix)
        purchase_date_str = purchase_date.strftime("%d/%m/%Y")
        out += f"**User ID:** `{user_id}`\n**Name**: {user_name}\n**Purchase Date:**\n`{purchase_date_str}`\n**Duration:** `{duration} days`\n\n"
    try:
        await m.edit(out, disable_web_page_preview=True)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption=f"List Of Users - Total {count} Users")


@Client.on_message(filters.command(['user', 'info', 'plan']))
async def userinfo(client, message):

    if len(message.command) < 2:
        user_id = message.from_user.id
    else:    
        user_id = int(message.command[1])

    try:
        user = await client.get_users(user_id)
    except ValueError:
        await message.reply_text("Invalid user ID provided.")
        return

    user_name = user.first_name if not user.last_name else f"{user.first_name} {user.last_name}"
    user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"

    private_joined = await db.is_user_joined(user_id)
    premium= await db.is_premium_status(user_id)
    users = await db.get_user(user_id)
    total_files_sent = users.get("lifetime_files") or "N/A"
    dc_id = user.dc_id or "Invalid DP"
    today_files_sent = users.get("files_count") or "N/A"

    if premium:
        duration = users.get("premium_expiry")
        purchase_date_unix = users.get("purchase_date")
        status = "Premium"
        purchase_date = datetime.fromtimestamp(purchase_date_unix)
        expiry_date = purchase_date + timedelta(days=duration)
        purchase_date_str = purchase_date.strftime("%d/%m/%Y")
        expiry_date_str = expiry_date.strftime("%d/%m/%Y")
        days_left = (expiry_date - datetime.now()).days
    else:
        status = "Free"
        purchase_date_str = "N/A"
        expiry_date_str = "N/A"
        days_left = "N/A"
        duration = "N/A"

    # Create the message with the information and keyboard.
    message_text = (
        f"<b>➲User ID:</b> <code>{user_id}</code>\n"
        f"<b>➲Name:</b> {user_link}\n"
        f"<b>➲DC ID:</b> {dc_id}\n"
        f"<b>➲Subscribed:</b> {private_joined}\n"
        f"<b>➲Status:</b> {status}\n"
        f"<b>➲Purchase Date:</b> <code>{purchase_date_str}</code>\n"
        f"<b>➲Expiry Date:</b> <code>{expiry_date_str}</code>\n"
        f"<b>➲Days Left:</b> <code>{days_left}/{duration}</code> days\n"
        f"<b>➲Files Recieved:</b> <code>{total_files_sent}</code>\n"
    )

    await message.reply_text(
        text=message_text,
        disable_web_page_preview=True
    )


@Client.on_message(filters.command(['upgrade', 'premium']))
async def upgrademsg(client, message):
    buttons = [[
                InlineKeyboardButton('💫 Confirm', callback_data="confirm"),
                InlineKeyboardButton('◀️ Back', callback_data="home")
            ]]
    await message.reply(
        text=script.REMADS_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
        )

# optional command to list all commands
@Client.on_message(filters.command("commands") & filters.user(ADMINS))
async def allcommands(client, message):
    await message.reply_text(
        f"<b>Commands:</b>\n"
        f"<b>➲/stats</b> - To get bot stats\n"
        f"<b>➲/user</b> - To get user info\n"
        f"<b>➲/list_premium</b> - To list all premium users\n"
        f"<b>➲/resetdaily</b> - To reset daily files count\n"
        f"<b>➲/add_paid</b> - To add a user as premium\n"
        f"<b>➲/remove_paid</b> - To remove a user from premium\n"
        f"<b>➲/deleteallfiles</b> - To delete all files from database\n"
        f"<b>➲/channel</b> - To get channel info\n"
        f"<b>➲/broadcast</b> - To broadcast a message to all users\n"
        f"<b>➲/id</b> - To get chat id\n"
        f"<b>➲/info</b> - To get user info\n"
        f"<b>➲/license</b> - To get redeem code\n"
        f"<b>➲/revoke</b> - To revoke redeem code\n"
        f"<b>➲/leave</b> - To leave a chat\n"
        f"<b>➲/disable</b> - To disable a chat\n"
        f"<b>➲/enable</b> - To enable a chat\n"
        f"<b>➲/invite</b> - To get invite link of a chat\n"
        f"<b>➲/ban</b> - To ban a user\n"
        f"<b>➲/unban</b> - To unban a user\n"
        f"<b>➲/chats</b> - To get all chats\n"
        )