from pyrogram import filters
from pyrogram.types import Message

from config import OWNER_ID
from Oneforall import app


@app.on_message(filters.command("setpfp") & filters.private)
async def set_pfp(client, message: Message):

    user_id = message.from_user.id

    # owner check
    if user_id != OWNER_ID:
        return await message.reply_text("you are not allowed to use this command.")

    # check replied photo
    if not message.reply_to_message:
        return await message.reply_text("reply to a photo.")

    if not message.reply_to_message.photo:
        return await message.reply_text("reply to a valid photo.")

    try:
        # download photo
        photo_path = await message.reply_to_message.download()

        # change bot pfp
        await client.set_profile_photo(photo=photo_path)

        await message.reply_text("bot profile photo updated successfully.")

    except Exception as e:
        await message.reply_text(f"error:\n\n{e}")
