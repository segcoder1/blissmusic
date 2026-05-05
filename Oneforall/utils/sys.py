import time
import psutil
import os
import shutil

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from Oneforall import app
from Oneforall.misc import _boot_
from Oneforall.utils.formatters import get_readable_time

async def bot_sys_stats():
    bot_uptime = int(time.time() - _boot_)
    UP = f"{get_readable_time(bot_uptime)}"
    CPU = f"{psutil.cpu_percent(interval=0.5)}%"
    RAM = f"{psutil.virtual_memory().percent}%"
    DISK = f"{psutil.disk_usage('/').percent}%"
    return UP, CPU, RAM, DISK

# updated prefixes with fixes by @itrjuna01
CACHE_DIR = "downloads"  
IMAGE_URL = "https://graph.org/file/25bb7015045251c18f8cb-34b7f869e90b9ed784.jpg"


def get_folder_size(path):
    total = 0
    if not os.path.exists(path):
        return 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def human_size(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

@app.on_message(filters.command("diskusage"))
async def disk_usage_handler(_, message: Message):
    UP, CPU, RAM, DISK = await bot_sys_stats()
    CACHE = human_size(get_folder_size(CACHE_DIR))

    text = f"""
•── ⋅ ⋅  ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•
✦ 📊 ꜱʏꜱᴛєᴍ ꜱᴛᴧᴛꜱ

⊚ ⏱ ᴜᴘᴛɪᴍє : {UP}  
⊚ 🧠 ᴄᴘᴜ : {CPU}  
⊚ 💾 ʀᴧᴍ : {RAM}  
⊚ 🗄 ᴅɪꜱᴋ : {DISK}  

✦ 🎵 ꜱᴛσʀᴧɢє

⊚ 📦 ᴄᴧᴄʜє : {CACHE}  
⊚ 📁 ᴘᴧᴛʜ : `{CACHE_DIR}`
•── ⋅ ⋅  ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•
"""

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧹 ᴄʟєᴧʀ ꜱᴛσʀᴧɢє", callback_data="clear_cache"),
            InlineKeyboardButton(" ᴄʟσꜱє", callback_data="close_disk")
        ]
    ])

    await message.reply_photo(
        photo=IMAGE_URL,
        caption=text,
        reply_markup=buttons
    )

@app.on_callback_query(filters.regex("clear_cache"))
async def clear_cache_handler(_, query: CallbackQuery):
    try:
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR, exist_ok=True)

        UP, CPU, RAM, DISK = await bot_sys_stats()
        CACHE = human_size(get_folder_size(CACHE_DIR))

        text = f"""
✦ ꜱᴛσʀᴧɢє ᴄʟєᴧʀєᴅ ✅

•── ⋅ ⋅  ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•
✦ 📊 ᴜᴘᴅᴧᴛєᴅ ꜱᴛᴧᴛꜱ

⊚ ⏱ ᴜᴘᴛɪᴍє : {UP}  
⊚ 🧠 ᴄᴘᴜ : {CPU}  
⊚ 💾 ʀᴧᴍ : {RAM}  
⊚ 🗄 ᴅɪꜱᴋ : {DISK}  

⊚ 📦 ᴄᴧᴄʜє : {CACHE}
•── ⋅ ⋅  ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•
"""

        await query.message.edit_caption(text)
        await query.answer("Storage Cleared", show_alert=True)

    except Exception as e:
        await query.answer(f"Error: {e}", show_alert=True)

@app.on_callback_query(filters.regex("close_disk"))
async def close_disk_handler(_, query: CallbackQuery):
    await query.message.delete()
