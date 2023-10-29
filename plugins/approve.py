from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from info import AUTH_GROUPS


TEXT = "Hello {}, Welcome To {}"
APPROVE = True

# auto approve members 
@Client.on_chat_join_request((filters.group | filters.channel) & filters.chat(AUTH_GROUPS) if AUTH_GROUPS else (filters.group | filters.channel))
async def autoapprove(client: Client, message: ChatJoinRequest):
    chat=message.chat
    user=message.from_user
    try:
        if APPROVE == True:
            await client.approve_chat_join_request(chat.id, user.id)
            await client.send_message(chat_id=chat.id, text=TEXT.format(user.mention, chat.title))
    except Exception as e:
        print(e)