from pyrogram import filters
from pyrogram.types import Message

from config import OWNER_ID
from Oneforall import app


@app.on_message(filters.command("setname") & filters.private)
async def set_name(client, message: Message):

    if message.from_user.id != OWNER_ID:
        return await message.reply_text("not authorized.")

    if len(message.command) < 2:
        return await message.reply_text(
            "usage:\n/setname new name"
        )

    new_name = message.text.split(None, 1)[1]

    try:
        await client.update_profile(
            first_name=new_name
        )

        await message.reply_text(
            f"name changed to:\n{new_name}"
        )

    except Exception as e:
        await message.reply_text(f"error:\n{e}")
