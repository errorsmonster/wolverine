from pyrogram import Client, filters
from info import AUTH_GROUPS as CHAT_IDS
from pyrogram.types import ChatJoinRequest

TEXT = "Hello {}, Welcome To {}"
APPROVED = True  # set to True by default

# Define the decorator function to handle chat join requests
@Client.on_chat_join_request(filters.group | filters.channel & filters.chat(CHAT_IDS))
async def autoapprove(client: Client, request: ChatJoinRequest):
    chat = request.chat
    user = request.from_user
    print(f"{user.first_name} joined {chat.title}")

    if APPROVED:
        await request.approve()
        await client.send_message(chat.id, TEXT.format(user.mention(), chat.title))
