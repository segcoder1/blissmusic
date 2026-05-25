import asyncio
import math
import random
import os
import aiohttp

from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.errors import FloodWait, MessageDeleteForbidden

from Oneforall import app

# ─────────────────────────────
# 🎥 VIDEO URL
# ─────────────────────────────
VIDEO_URL = "https://graph.org/file/9f9cb0ab87e4f7b6c061a-3544c3bdcf44adbe03.mp4"

# ─────────────────────────────
# 🔑 SEARCH API
# ─────────────────────────────
API_KEY = os.getenv("GOOGLE_API_KEY")
CX_ID = "ec8db9e1f9e41e65e"

# ─────────────────────────────
# 🎭 ANIME QUOTES
# ─────────────────────────────
ANIME_QUOTES = [
    "⚡ 'i summon you to the battlefield of melodies!'",
    "🔮 'through the gates of the astral plane, you have been called!'",
    "🔥 'your squad awaits your arrival in the arena!'",
    "🌌 'the stars aligned for this very moment!'",
    "🎭 'a new arc has begun and you are the mc now!'",
]

# ─────────────────────────────
# 🎙️ VC START
# ─────────────────────────────
@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    try:
        await message.reply_text(
            "<b>┃ 🎙️ ᴠᴄ ɪs ɴᴏᴡ ʟɪᴠᴇ</b>\n\n"
            "❯ sᴛᴀɢᴇ ʀᴇᴀᴅʏ ⚡\n"
            "❯ ᴊᴏɪɴ ᴛʜᴇ ᴠɪʙᴇ 🎧"
        )
    except Exception:
        pass

# ─────────────────────────────
# 📴 VC END
# ─────────────────────────────
@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    try:
        await message.reply_text(
            "<b>┃ 🕊️ ᴠᴄ ᴇɴᴅᴇᴅ</b>\n\n"
            "❯ sɪʟᴇɴᴄᴇ ʀᴇᴛᴜʀɴs 🎶\n"
            "❯ sᴇᴇ ʏᴏᴜ sᴏᴏɴ ⚡"
        )
    except Exception:
        pass

# ─────────────────────────────
# 👥 VC INVITE
# ─────────────────────────────
@app.on_message(filters.video_chat_members_invited)
async def vc_invited(_, message: Message):
    try:
        # Fallback agar user anonymous channel se invoke kare
        inviter = message.from_user
        inviter_mention = inviter.mention if inviter else "ᴀɴᴏɴʏᴍᴏᴜs"
        
        invited_users = message.video_chat_members_invited.users
        if not invited_users:
            return

        invited_mentions = ", ".join(
            user.mention for user in invited_users if user
        )

        quote = random.choice(ANIME_QUOTES)

        text = (
            "<b>┃ 💌 sᴜᴍᴍᴏɴɪɴɢ ᴀʟᴇʀᴛ</b>\n\n"
            f"❯ {inviter_mention} ʜᴀs sᴜᴍᴍᴏɴᴇᴅ {invited_mentions} ✨\n\n"
            f"💬 <i>{quote}</i>\n\n"
            "<b>┃ ᴊᴏɪɴ ᴛʜᴇ ᴠɪʙᴇ ɴᴏᴡ ⚡</b>"
        )

        sent = await message.reply_video(
            video=VIDEO_URL,
            caption=text,
            supports_streaming=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ",
                            url="https://t.me/theinfinitynetwork",
                        )
                    ]
                ]
            ),
        )

        await asyncio.sleep(15)

        try:
            await sent.delete()
        except MessageDeleteForbidden:
            pass  # Admin rights nahi hain bot ke paas delete karne ke liye
        except Exception:
            pass

    except FloodWait as fw:
        await asyncio.sleep(fw.value)
    except Exception as e:
        print(f"[vc_invited_error] {e}")

# ─────────────────────────────
# 🧮 MATH COMMAND
# ─────────────────────────────
@app.on_message(filters.command("math"))
async def calculate_math(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>┃ ⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ᴇxᴘʀᴇssɪᴏɴ</b>"
        )

    expression = message.text.split(maxsplit=1)[1]

    # Math module functions setup
    allowed_names = {
        k: v for k, v in math.__dict__.items()
        if not k.startswith("_")
    }

    # Strict Sandbox bypass checks
    blocked_words = [
        "__", "eval", "exec", "open", "import", "os", "sys", 
        "subprocess", "globals", "locals", "getattr", "setattr"
    ]

    if any(word in expression.lower() for word in blocked_words):
        return await message.reply_text(
            "<b>┃ ❌ ɪɴᴠᴀʟɪᴅ ᴏʀ sᴇᴄᴜʀɪᴛʏ ʀɪsᴋ ᴇxᴘʀᴇssɪᴏɴ</b>"
        )

    try:
        # Safe eval parsing without builtins access
        result = eval(
            expression,
            {"__builtins__": None},
            allowed_names,
        )

        await message.reply_text(
            f"<b>┃ 🧠 ʀᴇsᴜʟᴛ</b>\n\n"
            f"❯ <code>{result}</code>"
        )

    except Exception:
        await message.reply_text(
            "<b>┃ ⚠️ ɪɴᴠᴀʟɪᴅ ᴇxᴘʀᴇssɪᴏɴ</b>"
        )

# ─────────────────────────────
# 🔍 SEARCH COMMAND
# ─────────────────────────────
@app.on_message(filters.command("spg", prefixes=["/", "!", "."]))
async def search(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>┃ ❗ ɢɪᴠᴇ sᴇᴀʀᴄʜ ǫᴜᴇʀʏ</b>"
        )

    if not API_KEY:
        return await message.reply_text(
            "<b>┃ ⚠️ sᴇᴀʀᴄʜ ᴀᴘɪ ᴋᴇʏ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ</b>"
        )

    query = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text("🔎 sᴇᴀʀᴄʜɪɴɢ...")

    url = (
        "https://content-customsearch.googleapis.com/customsearch/v1"
        f"?cx={CX_ID}&q={query}&key={API_KEY}"
    )

    try:
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await msg.edit("❌ sᴇᴀʀᴄʜ sᴇʀᴠɪᴄᴇ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ")
                data = await response.json()

        items = data.get("items")
        if not items:
            return await msg.edit("❌ ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

        result = "<b>┃ 🌐 sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs</b>\n\n"

        for item in items[:5]:
            title = item.get("title", "unknown")
            link = item.get("link", "no link")
            # Cleaning track IDs and query elements from search links if any
            clean_link = link.split("?")[0]
            result += f"❯ <b>{title}</b>\n{clean_link}\n\n"

        await msg.edit(
            result,
            disable_web_page_preview=True,
        )

    except aiohttp.ClientError:
        await msg.edit("❌ ɴᴇᴛᴡᴏʀᴋ ᴇʀʀᴏʀ")
    except asyncio.TimeoutError:
        await msg.edit("❌ ʀᴇǫᴜᴇsᴛ ᴛɪᴍᴇᴅ ᴏᴜᴛ")
    except Exception as e:
        print(f"[search_error] {e}")
        await msg.edit("❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ")
