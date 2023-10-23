from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from info import AUTH_GROUPS, APPROVE


TEXT = "Hello {}, Welcome To {}"

# auto approve members 
@Client.on_chat_join_request(filters.chat(AUTH_GROUPS) if AUTH_GROUPS else filters.group)
async def autoapprove(client: Client, message: ChatJoinRequest):
    chat=message.chat
    user=message.from_user
    if APPROVE:
        await client.approve_chat_join_request(chat.id, user.id)
        await client.send_message(chat_id=chat.id, text=TEXT.format(user.mention, chat.title))