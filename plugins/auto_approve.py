from pyrogram import Client, filters
from info import AUTH_GROUPS as CHAT_IDS
from pyrogram.types import ChatJoinRequest

TEXT = "Hello {}, Welcome To {}"
APPROVED = True  # set to True by default

# Define the decorator function to handle chat join requests
@Client.on_chat_join_request(filters.chat(CHAT_IDS))
def auto_approve(client: Client, message: ChatJoinRequest):
    while APPROVED:
        try:
            client.approve_chat_join_request(message.chat.id, message.user.id)
            client.send_message(
                message.chat.id,
                TEXT.format(message.from_user.first_name, message.chat.title),
            )
        except Exception as e:
            print(e)
            break