from pyrogram import Client, filters
from info import AUTH_GROUPS as CHAT_IDS
from pyrogram.types import ChatJoinRequest


TEXT = "Hello {}, Welcome To {}"
APPROVED = True  # set to True by default

# auto approve members 
@Client.on_chat_join_request((filters.group | filters.channel) & filters.chat(CHAT_IDS) if CHAT_IDS else (filters.group | filters.channel))
async def autoapprove(client: Client, message: ChatJoinRequest):
    chat=message.chat
    user=message.from_user
    print(f"{user.first_name} Joined")
    if APPROVED:
        await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        await client.send_message(chat_id=chat.id, text=TEXT.format(user.mention, chat.title))