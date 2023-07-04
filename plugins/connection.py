from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.connections_mdb import add_connection, all_connections, if_active, delete_connection
from database.group_api import gdb
from info import ADMINS
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


@Client.on_message((filters.private | filters.group) & filters.command('connect') & filters.user(ADMINS))
async def addconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are an anonymous admin. Use /connect {message.chat.id} in PM")

    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        try:
            cmd, group_id, api = message.text.split(" ", 2)
        except ValueError:
            await message.reply_text(
                "<b>Enter in correct format!</b>\n\n"
                "<code>/connect groupid api</code>\n\n"
                "<i>Get your Group id by adding this bot to your group and use  <code>/id</code></i>",
                quote=True
            )
            return
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id
        api = ""  # Empty string if API is not provided

    try:
        st = await client.get_chat_member(group_id, userid)
        if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and userid not in ADMINS
        ):
            await message.reply_text("You should be an admin in the given group!", quote=True)
            return
    except Exception as e:
        logger.exception(e)
        await message.reply_text(
            "Invalid Group ID!\n\nIf correct, make sure I'm present in your group!!",
            quote=True,
        )
        return

    try:
        st = await client.get_chat_member(group_id, "me")
        if st.status == enums.ChatMemberStatus.ADMINISTRATOR:
            ttl = await client.get_chat(group_id)
            title = ttl.title

            if not api:
                await message.reply_text("Please provide the API when connecting to the group!", quote=True)
                return
            
            if not gdb.is_group_connected(group_id):
                await gdb.add_group(group_id)

            # addcon = await add_connection(str(group_id), str(userid))
            addcon = await gdb.update_api_for_group((group_id), api)          
            if addcon:
                await message.reply_text(
                    f"Successfully connected to **{title}**",
                    quote=True,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
                if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    await client.send_message(
                        userid,
                        f"Connected to **{title}**!",
                        parse_mode=enums.ParseMode.MARKDOWN
                    )
            else:
                await message.reply_text(
                    "You're already connected to this chat!",
                    quote=True
                )
        else:
            await message.reply_text("Add me as an admin in the group", quote=True)
    except Exception as e:
        logger.exception(e)
        await message.reply_text('Some error occurred! Try again later.', quote=True)



@Client.on_message((filters.private | filters.group) & filters.command('disconnect') & filters.user(ADMINS))
async def removeconnection(client, message):
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        try:
            cmd, group_id = message.text.split(" ", 1)
        except ValueError:
            await message.reply_text(
                "<b>Enter in correct format!</b>\n\n"
                "<code>/disconnect groupid</code>",
                quote=True
            )
            return
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

    if await gdb.is_group_connected(str(group_id)):
        await gdb.remove_api_for_group(str(group_id))
        await message.reply_text(
            f"Successfully disconnected from group {group_id}",
            quote=True,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            "You're not connected to this chat!",
            quote=True
        )


@Client.on_message(filters.private & filters.command(["connections"]))
async def connections(client, message):
    userid = message.from_user.id

    groupids = await all_connections(str(userid))
    if groupids is None:
        await message.reply_text(
            "There are no active connections!! Connect to some groups first.",
            quote=True
        )
        return
    buttons = []
    for groupid in groupids:
        try:
            ttl = await client.get_chat(int(groupid))
            title = ttl.title
            active = await if_active(str(userid), str(groupid))
            act = " - ACTIVE" if active else ""
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                    )
                ]
            )
        except:
            pass
    if buttons:
        await message.reply_text(
            "Your connected group details ;\n\n",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    else:
        await message.reply_text(
            "There are no active connections!! Connect to some groups first.",
            quote=True
        )