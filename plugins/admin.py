from pyrogram import Client, filters
from users_chats_db import db
from info import ADMINS


ADD_PAID_TEXT = "Successfully Enabled {}'s Subscription for {} days"
DEL_PAID_TEXT = "Successfully Removed Subscription for {}"



# Add paid user to database 
@Client.on_message(filters.command('add_paid') & filters.user(ADMINS))
async def add_paid(client, message):
    if len(message.command) < 2:
        return await message.reply('Please provide a user id and duration')
    chat = message.command[1]
    try:
        chat = int(chat)
    except ValueError:
        return await message.reply("Invalid user id provided.")
    try:
        k = await client.get_users(chat)
    except IndexError:
        return await message.reply("This might be a channel, make sure it's a user.")
    else:
        name = k.first_name if not k.last_name else k.first_name + " " + k.last_name
        try:
            duration = int(message.command[2])
        except (IndexError, ValueError):
            duration = 30  # Set default duration to 30 days
            
        if duration > 365:
            await message.reply("Duration can't be more than 365 days.")
                
        if not db.is_user_exist(k.id):
            await db.add_user(k.id, name)
                        
        if db.is_premium_status(k.id) is True:
            await message.reply(f"**{name}** is already a premium user.")
        else:
            await db.add_user_as_premium(k.id, duration)
            await message.reply(ADD_PAID_TEXT.format(name, duration))
            await client.send_message(chat, f"Your subscription has been enabled successfully for {duration} days.")
                
       
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