from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from info import AUTO_APPROVE, AUTH_GROUPS


TEXT = "Hello {}, Welcome To {}"

# auto approve members 
@Client.on_chat_join_request((filters.group | filters.channel) & filters.chat(AUTH_GROUPS) if AUTH_GROUPS else (filters.group | filters.channel))
async def autoapprove(client: Client, message: ChatJoinRequest):
    chat=message.chat
    user=message.from_user
    print(f"{user.first_name} Joined")
    if AUTO_APPROVE:
        await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        await client.send_message(chat_id=chat.id, text=TEXT.format(user.mention, chat.title))