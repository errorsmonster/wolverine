import aiohttp
from pyrogram import Client, filters
from info import ADMINS
from database.users_chats_db import db
import asyncio


ACCESS_KEY = "7W5CDPYOL6VVCN6MP1W9"  # replace with your access key

@Client.on_message(filters.command("licensegen") & filters.user(ADMINS))
async def generate(client, message):
    num_codes = 1  # default value

    # Check if a number is provided
    if len(message.command) > 1:
        try:
            num_codes = int(message.command[1])
            if num_codes <= 0:  # Ensure a positive number
                raise ValueError
        except ValueError:
            await message.reply_text("Please provide a valid number of codes to generate.")
            return

    codes_generated = []
    for _ in range(num_codes):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lisencecodegen.onrender.com/?access_key={ACCESS_KEY}&action=generate&days=30") as resp:
                if resp.status == 200:
                    json_response = await resp.json()
                    license_code = json_response.get('license_code')
                    codes_generated.append(license_code)
                else:
                    await message.reply_text("Error generating license code. Please try again.")
                    return
                
    codes_str = "\n".join(codes_generated)
    await message.reply_text(f"<b>Generated license codes:</b>\n<code>{codes_str}</code>")


@Client.on_message(filters.regex(r"^[A-Z0-9]{10}$") & filters.private)
async def validate_code(client, message):
    code = message.text
    user_id = message.from_user.id
    m = await message.reply_text("Validating redeem code...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://lisencecodegen.onrender.com/?access_key={ACCESS_KEY}&action=validate&code={code}") as resp:
            if resp.status == 200:
                json_response = await resp.json()
                if json_response.get('message') == "Code validated successfully":
                    await m.edit("Redeem code validated successfully.")
                    await db.add_user_as_premium(user_id, 28)
                    await asyncio.sleep(2)
                    await message.reply_text(f"Your subscription has been enabled successfully for 28 days.")
                else:
                    await m.edit(json_response.get('message'))
            else:
                await m.edit("Error validating redeem code. Please try again.")

