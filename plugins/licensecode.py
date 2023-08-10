import aiohttp
from pyrogram import Client, filters
from info import ADMINS
from database.users_chats_db import db
import asyncio

ACCESS_KEY = "F5DDYDRBVEDTQ0CPZDDX"

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
            async with session.get(f"https://licensegen.onrender.com/?access_key={ACCESS_KEY}&action=generate&days=30") as resp:
                if resp.status == 200:
                    json_response = await resp.json()
                    license_code = json_response.get('license_code')
                    codes_generated.append(license_code)
                else:
                    await message.reply_text("Error generating license code. Please try again.")
                    return
                
    codes_str = "\n".join(codes_generated)
    await message.reply_text(f"<b>Redeem codes:</b>\n\n<code>{codes_str}</code>")


@Client.on_message(filters.regex(r"^[A-Z0-9]{20}$") & filters.private)
async def validate_code(client, message):
    code = message.text
    user_id = message.from_user.id
    if await db.is_premium_status(user_id) is True:
        await message.reply_text("You can't redeem this code because you are already a premium user")
        return
    m = await message.reply_text(f"Please wait, checking your redeem code....")
    await asyncio.sleep(3)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://licensegen.onrender.com/?access_key={ACCESS_KEY}&action=validate&code={code}") as resp:
            if resp.status == 404:
                await m.edit("Invalid code. Please try again.")
            if resp.status == 403:
                respo = await resp.json()
                if respo.get('message') == "This code does not belong to the provided access key":
                    await m.edit("This code does not belong to the provided access key.")
                    return
                if respo.get('message') == "This code is already in use":
                    await m.edit("This redeem code is already in use.")
                    return
                if respo.get('message') == "The code has expired":
                    await m.edit("The redeem code has expired.")
                    return
            if resp.status == 200:
                json_response = await resp.json()
                if json_response.get('message') == "Code validated successfully":
                    s = await m.edit("Redeem code validated successfully.")
                    await db.add_user_as_premium(user_id, 28)
                    await asyncio.sleep(5)
                    await s.edit(f"Your subscription has been enabled successfully for 28 days.")
                else:
                    await m.edit(json_response.get('message'))