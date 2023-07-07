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

# enable/disable auto approve feature
@Client.on_message(filters.command("autoapprove") & filters.private)
async def toggle_autoapprove(client, message):
    chat = message.chat
    user_id = message.from_user.id
    member = await client.get_chat_member(chat_id=chat.id, user_id=user_id)
    if member.can_manage_chat:
        global APPROVED
        if len(message.command) > 1:
            action = message.command[1].lower()
            if action == "on":
                APPROVED = True
                await message.reply("Auto approve is now enabled.")
            elif action == "off":
                APPROVED = False
                await message.reply("Auto approve is now disabled.")
            else:
                await message.reply("Invalid argument. Use 'on' or 'off'.")
        else:
            await message.reply(f"Auto approve is currently {'enabled' if APPROVED else 'disabled'}. Use 'on' or 'off' to toggle.")
    else:
        await message.reply("Only group admins can enable or disable auto approve.")