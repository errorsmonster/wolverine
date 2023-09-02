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
        
        
@Client.on_message(filters.private & filters.command("add_api") & filters.user(ADMINS))
async def update_api_command(client, message):
    # Extract the group ID and API from the command message
    command_parts = message.text.split(" ")
    if len(command_parts) < 3:
        await message.reply_text("Invalid command format. Please use /update_api <group_id> <api>")
        return
    group_id = command_parts[1]
    api = command_parts[2]

    # Update the API for the group in the database
    await db.update_api_for_group(group_id, api)
    await message.reply_text("API updated successfully!")


@Client.on_message(filters.private & filters.command("remove_api") & filters.user(ADMINS))
async def remove_api_command(client, message):
    # Extract the group ID from the command message
    command_parts = message.text.split(" ")
    if len(command_parts) < 2:
        await message.reply_text("Invalid command format. Please use /remove_api <group_id>")
        return
    group_id = command_parts[1]

    # Remove the API for the group from the database
    await db.remove_api_for_group(group_id)
    await message.reply_text("API removed successfully!")
    
    
#request command 
@Client.on_message(filters.command("request") & filters.private)
async def request(client, message):
    # Strip the command and normalize the movie name
    movie_name = message.text.replace("/request", "").strip().lower()
    
    # If the message only contains the command, send a default response
    if not movie_name:
        await message.reply_text(script.REQM, disable_web_page_preview=True)
        return

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

@Client.on_message(filters.command("userinfo"))
async def userinfo(client, message):

    if len(message.command) < 2:
        await message.reply_text("Please provide a user id with the command.")
        return

    user_id = message.command[1]
    user = await client.get_users(user_id)
    name = user.first_name if not user.last_name else f"{user.first_name} {user.last_name}"
    link = f"<a href='tg://user?id={user_id}'>{name}</a>"
    total_files_sent_today = await db.get_files_count(user_id)
    private_joined = await db.is_user_joined(user_id)

    if await db.is_premium_status(user_id):
        status = "Premium Member"
        purchase_date_unix = await db.get_purchased_date(user_id)
        purchase_date = datetime.fromtimestamp(purchase_date_unix).strftime("%d/%m/%Y")
        expiry_date = datetime.fromtimestamp(purchase_date_unix + 2592000).strftime("%d/%m/%Y")
        days_left = (datetime.fromtimestamp(purchase_date_unix + 2592000) - datetime.now()).days
        
    else:
        status = "Free User"
        purchase_date = "N/A"
        expiry_date = "N/A"
        days_left = "N/A"

    await message.reply_text(
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Name:</b> {link}\n"
        f"<b>Joined Channel:</b> {private_joined}\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Purchase Date:</b> <code>{purchase_date}</code>\n"
        f"<b>Expiry Date:</b> <code>{expiry_date}</code>\n"
        f"<b>Days Left:</b> <code>{days_left}</code>\n"
        f"<b>Files Sent Today:</b> <code>{total_files_sent_today}</code>\n"    
        disable_web_page_preview=True
    )