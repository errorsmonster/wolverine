from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup
from database.top_msg import mdb  # Assuming you've kept the same file structure

MAX_MESSAGE_LENGTH = 30  # Define a max length for messages

@Client.on_message(filters.command('top'))
async def top(client, message):
    top_messages = await mdb.get_top_messages(20)

    # Truncate messages that are too long
    truncated_messages = []
    for msg in top_messages:
        if len(msg) > MAX_MESSAGE_LENGTH:
            truncated_messages.append(msg[:MAX_MESSAGE_LENGTH - 3] + "...")
        else:
            truncated_messages.append(msg)

    # Create a keyboard with two messages per row
    keyboard = []
    for i in range(0, len(truncated_messages), 2):
        row = truncated_messages[i:i+2]
        keyboard.append(row)
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await message.reply_text("Top Searches", reply_markup=reply_markup)
