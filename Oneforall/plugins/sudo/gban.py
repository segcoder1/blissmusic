import asyncio

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from Oneforall import app
from Oneforall.misc import SUDOERS
from Oneforall.utils import get_readable_time
from Oneforall.utils.database import (
    add_banned_user,
    get_banned_count,
    get_banned_users,
    get_served_chats,
    is_banned_user,
    remove_banned_user,
)
from Oneforall.utils.decorators.language import language
from Oneforall.utils.extraction import extract_user
from config import BANNED_USERS, superban_storage_id


# ─────────────────────────────
# LOG GIF
# ─────────────────────────────
LOG_GIF = "https://files.catbox.moe/qdm48e.gif"


# ─────────────────────────────
# GLOBAL BAN
# ─────────────────────────────
@app.on_message(filters.command(["gban", "globalban"], prefixes=["/", "!", "."]) & SUDOERS)
@language
async def global_ban(client, message: Message, _):
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text(_["general_1"])

    user = await extract_user(message)

    if user.id == message.from_user.id:
        return await message.reply_text(_["gban_1"])
    elif user.id == app.id:
        return await message.reply_text(_["gban_2"])
    elif user.id in SUDOERS:
        return await message.reply_text(_["gban_3"])

    if await is_banned_user(user.id):
        return await message.reply_text(_["gban_4"].format(user.mention))

    if user.id not in BANNED_USERS:
        BANNED_USERS.add(user.id)

    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    time_expected = get_readable_time(len(served_chats))

    mystic = await message.reply_text(_["gban_5"].format(user.mention, time_expected))

    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue

    await add_banned_user(user.id)

    await message.reply_text(
        _["gban_6"].format(
            app.mention,
            message.chat.title,
            message.chat.id,
            user.mention,
            user.id,
            message.from_user.mention,
            number_of_chats,
        )
    )

    # Warning to sudoers
    try:
        await message.reply_text(_["gban_warning"].format(user.mention))
    except:
        pass

    # Send GBAN log to log channel
    try:
        await app.send_animation(
            superban_storage_id,
            LOG_GIF,
            caption=_["gban_log"].format(
                user.mention,
                user.id,
                message.from_user.mention,
                number_of_chats,
            ),
        )
    except:
        pass

    await mystic.delete()


# ─────────────────────────────
# GLOBAL UNBAN
# ─────────────────────────────
@app.on_message(filters.command(["ungban"], prefixes=["/", "!", "."]) & SUDOERS)
@language
async def global_un(client, message: Message, _):
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text(_["general_1"])

    user = await extract_user(message)

    if not await is_banned_user(user.id):
        return await message.reply_text(_["gban_7"].format(user.mention))

    if user.id in BANNED_USERS:
        BANNED_USERS.remove(user.id)

    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    time_expected = get_readable_time(len(served_chats))

    mystic = await message.reply_text(_["gban_8"].format(user.mention, time_expected))

    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue

    await remove_banned_user(user.id)

    await message.reply_text(_["gban_9"].format(user.mention, number_of_chats))

    # Send UNGBAN log to log channel
    try:
        await app.send_animation(
            superban_storage_id,
            LOG_GIF,
            caption=_["ungban_log"].format(
                user.mention,
                user.id,
                message.from_user.mention,
            ),
        )
    except:
        pass

    await mystic.delete()


# ─────────────────────────────
# GBANNED USERS LIST
# ─────────────────────────────
@app.on_message(filters.command(["gbannedusers", "gbanlist"], prefixes=["/", "!", "."]) & SUDOERS)
@language
async def gbanned_list(client, message: Message, _):
    counts = await get_banned_count()
    if counts == 0:
        return await message.reply_text(_["gban_10"])

    mystic = await message.reply_text(_["gban_11"])
    msg = _["gban_12"]
    count = 0

    users = await get_banned_users()
    for user_id in users:
        count += 1
        try:
            user = await app.get_users(user_id)
            user_name = user.mention if user.mention else user.first_name
            msg += f"{count}⌯ {user_name}\n"
        except:
            msg += f"{count}⌯ {user_id}\n"
            continue

    if count == 0:
        return await mystic.edit_text(_["gban_10"])

    return await mystic.edit_text(msg)
