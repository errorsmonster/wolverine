from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from info import FORCESUB_CHANNEL
from database.users_chats_db import db


@Client.on_chat_join_request(filters.chat(FORCESUB_CHANNEL))
async def private_fsub(client: Client, message: ChatJoinRequest):
    user = message.from_user
    print(user.first_name)
    try:
        await db.update_user_joined(user.id, True)
    except Exception as e:
        print(e)
        pass    

@Client.on_message(filters.private & filters.command("resetforcesub"))
async def reset_forcesub(client, message):
    m = await message.reply_text("Resetting Force Sub...")
    try:
        await db.reset_all_users_joined()
        await m.edit("Resetted Force Sub!")
    except Exception as e:
        await m.edit(f"Error:\n{e}")