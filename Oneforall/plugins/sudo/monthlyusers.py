from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

import asyncio

from Oneforall import app
from config import OWNER_ID


# store unique monthly users
monthly_users = set()


# track users from private/group messages
@app.on_message(filters.incoming & ~filters.service)
async def track_users(_, message: Message):
    try:
        if message.from_user:
            monthly_users.add(message.from_user.id)
    except Exception:
        pass


# command to show monthly users
@app.on_message(filters.command("monthlymembers") & filters.user(OWNER_ID))
async def monthly_members(_, message: Message):
    total_users = len(monthly_users)

    text = (
        f"<b>📊 ᴍᴏɴᴛʜʟʏ ʙᴏᴛ sᴛᴀᴛᴜs</b>"
        f"👥 ᴍᴏɴᴛʜʟʏ ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs: <code>{total_users}</code>"
        f"🤖 ʙᴏᴛ sᴛᴀᴛᴜs : <b>active</b>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "༎ຶ ᴅᴇʟᴇᴛᴇ ༎ຶ",
                    callback_data="close"
                )
            ]
        ]
    )

    image = "https://graph.org/file/622508d6b9a9ec919d358-51f18c3b31bf6a7465.jpg" 

    await message.reply_photo(
        photo=image,
        caption=text,
        reply_markup=buttons
    )


# close callback
@app.on_callback_query(filters.regex("^close$"))
async def close_button(_, query):
    try:
        await query.message.delete()
    except Exception:
        await query.answer("unable to close", show_alert=True)
