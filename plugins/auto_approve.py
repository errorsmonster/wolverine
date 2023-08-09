from pyrogram import Client, filters
from info import AUTH_GROUPS
from pyrogram.errors import FloodWait
from pyrogram.types import ChatJoinRequest

TEXT = "Hello {}, Welcome To {}"
APPROVED = True  # set to True by default

@Client.on_chat_join_request(filters.chat(AUTH_GROUPS))
def auto_approve(client: Client, message: ChatJoinRequest):
    if APPROVED:
        try:
            client.approve_chat_join_request(AUTH_GROUPS, message.user.id)
            client.send_message(
                message.chat.id,
                TEXT.format(message.from_user.first_name, message.chat.title),
            )
        except FloodWait as e:
            print(f"Rate limit exceeded. Retry after {e.x} seconds.")
        except Exception as e:
            print("An error occurred:", e)
