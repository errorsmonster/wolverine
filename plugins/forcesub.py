from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from info import FORCESUB_CHANNEL
from database.users_chats_db import db


@Client.on_chat_join_request(filters.chat(FORCESUB_CHANNEL))
async def private_fsub(client: Client, message: ChatJoinRequest):
    user = message.from_user
    print(user.first_name)
    if user is None:
        return
    try:
        await db.update_user_joined(user.id, True)
    except Exception as e:
        print(e)
        pass    
