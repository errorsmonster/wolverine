from pyrogram import Client, filters
from utils import encode_to_base64, temp


@Client.on_message(filters.command("linkgen") & ~filters.edited)
async def genetare_file_link(client, message):
    msg = message.reply_to_message

    if not msg:
        await message.reply_text("Reply to a media to generate link")
        return
    
    media = msg.document or msg.video or msg.audio or msg.voice
    if not media:
        await message.reply_text("Only media files are supported")
        return
    
    if media:
        user_id = message.from_user.id
        media_id = media.file_id
        link = f"{user_id}_{media_id}"
        encod = await encode_to_base64(link)
        await message.reply_text(f"<b>Here Is Your Link</b>\n\nhttps://telegram.me/{temp.U_NAME}?start=encrypt-{encod}\n\n(You Can Only Access This)", disable_web_page_preview=True)