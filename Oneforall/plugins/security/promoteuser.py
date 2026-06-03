import asyncio
from contextlib import suppress

from pyrogram import filters, Client
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    ChatPrivileges,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired, InviteHashExpired
from string import ascii_lowercase
from typing import Dict, Union

from Oneforall import app
from Oneforall.misc import SUDOERS
from Oneforall.core.mongo import mongodb
from Oneforall.utils.errors import capture_err
from Oneforall.utils.keyboard import ikb
from Oneforall.utils.clonedatabase.memorydatabase import save_filter
from Oneforall.utils.functions import (
    extract_user,
    extract_user_and_reason,
    time_converter,
)
from Oneforall.utils.permissions import adminsOnly, member_permissions
from config import BANNED_USERS

warnsdb = mongodb.warns
actionsdb = mongodb.modlog

__MODULE__ = "ꜱᴇᴄᴜʀɪᴛʏ"
__HELP__ = """
ᴋɪᴄᴋ & ʙᴀɴ ᴄᴏᴍᴍᴀɴᴅꜱ:
/sban - ᴅᴇʟᴇᴛᴇ ᴀʟʟ ᴍᴇssᴀɢᴇs ᴀɴᴅ ʙᴀɴ ᴜsᴇʀ
/tban [ᴛɪᴍᴇ] - ʙᴀɴ ғᴏʀ sᴘᴇᴄɪғɪ�� ᴛɪᴍᴇ
/unban - ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ
/kick - ᴋɪᴄᴋ ᴀ ᴜsᴇʀ
/skick - ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs ᴀɴᴅ ᴋɪᴄᴋ

ᴡᴀʀɴ sʏsᴛᴇᴍ:
/warn - ᴡᴀʀɴ ᴀ ᴜsᴇʀ
/swarn - ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs ᴀɴᴅ ᴡᴀʀɴ
/warns - ʜᴇᴄᴋ ᴡᴀʀɴɪɴɢs
/rmwarns - ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴡᴀʀɴɪɴɢs

ᴍᴏᴅᴇʀᴀᴛɪᴏɴ:
/promote - ᴘʀᴏᴍᴏᴛᴇ ᴜsᴇʀ
/fullpromote - ᴘʀᴏᴍᴏᴛᴇ ᴡɪᴛʜ ᴀʟʟ ʀɪɢʜᴛs
/demote - ᴅᴇᴍᴏᴛᴇ ᴜsᴇʀ
/mute - ᴍᴜᴛᴇ ᴜsᴇʀ
/tmute [ᴛɪᴍᴇ] - ᴍᴜᴛᴇ ғᴏʀ ᴛɪᴍᴇ
/unmute - ᴜɴᴍᴜᴛᴇ ᴜsᴇʀ

ᴍᴇssᴀɢᴇ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ:
/pin - ᴘɪɴ ᴍᴇssᴀɢᴇ
/unpin - ᴜɴᴘɪɴ ᴍᴇssᴀɢᴇ
/unpinall - ᴜɴᴘɪɴ ᴀʟʟ
/purge - ᴘᴜʀɢᴇ ᴍᴇssᴀɢᴇs
/del - ᴅᴇʟᴇᴛᴇ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ

ꜱᴘᴇᴄɪᴀʟ:
/banall - ʙᴀɴ ᴀʟʟ ᴍᴇᴍʙᴇʀs (ꜱᴜᴅᴏ ᴏɴʟʏ)
/unbanme [ɢʀᴘᴏᴜᴘ_ɪᴅ] - ᴜɴʙᴀɴ ʏᴏᴜʀsᴇʟғ
/zombies - ʙᴀɴ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs"""


async def int_to_alpha(user_id: int) -> str:
    """Convert user ID to alphabetic representation."""
    alphabet = list(ascii_lowercase)[:10]
    text = ""
    user_id = str(user_id)
    for i in user_id:
        text += alphabet[int(i)]
    return text


async def get_warns_count() -> dict:
    """Get total warning statistics."""
    chats_count = 0
    warns_count = 0
    async for chat in warnsdb.find({"chat_id": {"$lt": 0}}):
        for user in chat["warns"]:
            warns_count += chat["warns"][user]["warns"]
        chats_count += 1
    return {"chats_count": chats_count, "warns_count": warns_count}


async def get_warns(chat_id: int) -> Dict[str, int]:
    """Get all warnings for a chat."""
    warns = await warnsdb.find_one({"chat_id": chat_id})
    if not warns:
        return {}
    return warns["warns"]


async def get_warn(chat_id: int, name: str) -> Union[bool, dict]:
    """Get warnings for a specific user."""
    name = name.lower().strip()
    warns = await get_warns(chat_id)
    if name in warns:
        return warns[name]


async def add_warn(chat_id: int, name: str, warn: dict):
    """Add warning to a user."""
    name = name.lower().strip()
    warns = await get_warns(chat_id)
    warns[name] = warn

    await warnsdb.update_one(
        {"chat_id": chat_id}, {"$set": {"warns": warns}}, upsert=True
    )


async def remove_warns(chat_id: int, name: str) -> bool:
    """Remove all warnings for a user."""
    warnsd = await get_warns(chat_id)
    name = name.lower().strip()
    if name in warnsd:
        del warnsd[name]
        await warnsdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"warns": warnsd}},
            upsert=True,
        )
        return True
    return False


async def log_action(chat_id: int, action: str, user_id: int, admin_id: int, reason: str = ""):
    """Log moderation actions."""
    await actionsdb.insert_one({
        "chat_id": chat_id,
        "action": action,
        "user_id": user_id,
        "admin_id": admin_id,
        "reason": reason,
        "timestamp": asyncio.get_event_loop().time()
    })


# ============ KICK & BAN COMMANDS ============

@app.on_message(filters.command(["kick", "skick"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def kickFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴋɪᴄᴋ ᴍʏsᴇʟғ, ɪ ᴄᴀɴ ʟᴇᴀᴠᴇ ɪғ ʏᴏᴜ ᴡᴀɴᴛ.")
    if user_id in SUDOERS:
        return await message.reply_text("ʏᴏᴜ ᴡᴀɴɴᴀ ᴋɪᴄᴋ ᴛʜᴇ ᴇʟᴇᴠᴀᴛᴇᴅ ᴏɴᴇ ?")
    if user_id in [
        member.user.id
        async for member in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]:
        return await message.reply_text(
            "ɪ ᴄᴀɴ'ᴛ ᴋɪᴄᴋ ᴀɴ ᴀᴅᴍɪɴ, ʏᴏᴜ ᴋɴᴏᴡ ᴛʜᴇ ʀᴜʟᴇs"
        )
    mention = (await app.get_users(user_id)).mention
    msg = f"""
**ᴋɪᴄᴋᴇᴅ ᴜsᴇʀ:** {mention}
**ᴋɪᴄᴋᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜs'}
**ʀᴇᴀsᴏɴ:** {reason or 'ɴᴏ ʀᴇᴀsᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ'}"""
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✖ ʀᴇᴠᴏᴋᴇ", callback_data=f"revoke_kick_{user_id}")]])
    
    await message.chat.ban_member(user_id)
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg, reply_markup=keyboard)
    await asyncio.sleep(1)
    await message.chat.unban_member(user_id)
    
    if message.command[0][0] == "s":
        await message.reply_to_message.delete()
        await app.delete_user_history(message.chat.id, user_id)
    
    await log_action(message.chat.id, "KICK", user_id, message.from_user.id, reason)


# ============ BAN COMMANDS ============

@app.on_message(filters.command(["sban", "tban"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def banFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message, sender_chat=True)

    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ʙᴀɴ ᴍʏsᴇʟғ")
    if user_id in SUDOERS:
        return await message.reply_text("ʏᴏᴜ ᴄᴀɴ'ᴛ ʙᴀɴ ᴇʟᴇᴠᴀᴛᴇᴅ ᴜsᴇʀs!")
    if user_id in [
        member.user.id
        async for member in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ʙᴀɴ ᴀᴅᴍɪɴs")

    try:
        mention = (await app.get_users(user_id)).mention
    except IndexError:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message
            else "ᴀɴᴏɴʏᴍᴏᴜs"
        )

    msg = (
        f"**ʙᴀɴɴᴇᴅ ᴜsᴇʀ:** {mention}\n"
        f"**ʙᴀɴɴᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜs'}\n"
    )
    
    if message.command[0][0] == "s":
        await message.reply_to_message.delete()
        await app.delete_user_history(message.chat.id, user_id)
    
    if message.command[0] == "tban":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_ban = await time_converter(message, time_value)
        msg += f"**ʙᴀɴɴᴇᴅ ғᴏʀ:** {time_value}\n"
        if temp_reason:
            msg += f"**ʀᴇᴀsᴏɴ:** {temp_reason}"
        with suppress(AttributeError):
            if len(time_value[:-1]) < 3:
                await message.chat.ban_member(user_id, until_date=temp_ban)
                replied_message = message.reply_to_message
                if replied_message:
                    message = replied_message
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✖ ᴜɴʙᴀɴ", callback_data=f"unban_{user_id}")]])
                await message.reply_text(msg, reply_markup=keyboard)
                await log_action(message.chat.id, "TBAN", user_id, message.from_user.id, temp_reason)
            else:
                await message.reply_text("ᴛɪᴍᴇ ᴠᴀʟᴜᴇ ᴛᴏᴏ ʟᴀʀɢᴇ")
        return
    
    if reason:
        msg += f"**ʀᴇᴀsᴏɴ:** {reason}"
    
    await message.chat.ban_member(user_id)
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✖ ᴜɴʙᴀɴ", callback_data=f"unban_{user_id}")]])
    await message.reply_text(msg, reply_markup=keyboard)
    await log_action(message.chat.id, "BAN", user_id, message.from_user.id, reason)


# ============ UNBAN COMMANDS ============

@app.on_message(filters.command("unban") & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def unban_func(_, message: Message):
    reply = message.reply_to_message
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")

    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        return await message.reply_text("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴜɴʙᴀɴ ᴄʜᴀɴɴᴇʟs")

    await message.chat.unban_member(user_id)
    umention = (await app.get_users(user_id)).mention
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩ ʀᴇʙᴀɴ", callback_data=f"reban_{user_id}")]])
    await message.reply_text(f"✓ ᴜɴʙᴀɴɴᴇᴅ {umention}", reply_markup=keyboard)
    await log_action(message.chat.id, "UNBAN", user_id, message.from_user.id)


@app.on_callback_query(filters.regex(r"^(unban|reban)_\d+"))
async def ban_callbacks(_, query: CallbackQuery):
    try:
        action = query.data.split("_")[0]
        user_id = int(query.data.split("_")[1])
        
        if action == "unban":
            await query.message.chat.unban_member(user_id)
            await query.answer("ᴜɴʙᴀɴɴᴇᴅ!", show_alert=False)
        elif action == "reban":
            await query.message.chat.ban_member(user_id)
            await query.answer("ʀᴇʙᴀɴɴᴇᴅ!", show_alert=False)
    except Exception as e:
        await query.answer(f"ᴇʀʀᴏʀ: {str(e)}", show_alert=True)


# ============ PROMOTE & DEMOTE ============

@app.on_message(filters.command(["promote", "fullpromote"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_promote_members")
async def promoteFunc(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")

    bot = (await app.get_chat_member(message.chat.id, app.id)).privileges
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴘʀᴏᴍᴏᴛᴇ ᴍʏsᴇʟғ")
    if not bot:
        return await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ")
    if not bot.can_promote_members:
        return await message.reply_text("ɪ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴs")

    umention = (await app.get_users(user_id)).mention

    if message.command[0][0] == "f":
        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=bot.can_change_info,
                can_invite_users=bot.can_invite_users,
                can_delete_messages=bot.can_delete_messages,
                can_restrict_members=bot.can_restrict_members,
                can_pin_messages=bot.can_pin_messages,
                can_promote_members=bot.can_promote_members,
                can_manage_chat=bot.can_manage_chat,
                can_manage_video_chats=bot.can_manage_video_chats,
            ),
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩ ᴅᴇᴍᴏᴛᴇ", callback_data=f"demote_{user_id}")]])
        await message.reply_text(f"✓ ғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ {umention}", reply_markup=keyboard)
        await log_action(message.chat.id, "FULLPROMOTE", user_id, message.from_user.id)
        return

    await message.chat.promote_member(
        user_id=user_id,
        privileges=ChatPrivileges(
            can_change_info=False,
            can_invite_users=bot.can_invite_users,
            can_delete_messages=bot.can_delete_messages,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=bot.can_manage_chat,
            can_manage_video_chats=bot.can_manage_video_chats,
        ),
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩ ᴅᴇᴍᴏᴛᴇ", callback_data=f"demote_{user_id}")]])
    await message.reply_text(f"✓ ᴘʀᴏᴍᴏᴛᴇᴅ {umention}", reply_markup=keyboard)
    await log_action(message.chat.id, "PROMOTE", user_id, message.from_user.id)


@app.on_message(filters.command("demote") & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_promote_members")
async def demote(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴅᴇᴍᴏᴛᴇ ᴍʏsᴇʟғ")
    if user_id in SUDOERS:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴅᴇᴍᴏᴛᴇ sᴜᴅᴏ ᴜsᴇʀs!")
    try:
        member = await app.get_chat_member(message.chat.id, user_id)
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            await message.chat.promote_member(
                user_id=user_id,
                privileges=ChatPrivileges(
                    can_change_info=False,
                    can_invite_users=False,
                    can_delete_messages=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    can_manage_chat=False,
                    can_manage_video_chats=False,
                ),
            )
            umention = (await app.get_users(user_id)).mention
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩ ᴘʀᴏᴍᴏᴛᴇ", callback_data=f"repromote_{user_id}")]])
            await message.reply_text(f"✓ ᴅᴇᴍᴏᴛᴇᴅ {umention}", reply_markup=keyboard)
            await log_action(message.chat.id, "DEMOTE", user_id, message.from_user.id)
        else:
            await message.reply_text("ᴛʜɪs ᴜsᴇʀ ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ")
    except Exception as e:
        await message.reply_text(f"ᴇʀʀᴏʀ: {str(e)}")


@app.on_callback_query(filters.regex(r"^(demote|repromote)_\d+"))
async def promote_callbacks(_, query: CallbackQuery):
    try:
        action = query.data.split("_")[0]
        user_id = int(query.data.split("_")[1])
        bot = (await query.message.chat.get_member(app.id)).privileges
        
        if action == "demote" and bot.can_promote_members:
            await query.message.chat.promote_member(
                user_id=user_id,
                privileges=ChatPrivileges(
                    can_change_info=False,
                    can_invite_users=False,
                    can_delete_messages=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    can_manage_chat=False,
                    can_manage_video_chats=False,
                ),
            )
            await query.answer("ᴅᴇᴍᴏᴛᴇᴅ!", show_alert=False)
        elif action == "repromote" and bot.can_promote_members:
            await query.message.chat.promote_member(
                user_id=user_id,
                privileges=ChatPrivileges(
                    can_change_info=False,
                    can_invite_users=True,
                    can_delete_messages=True,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    can_manage_chat=True,
                    can_manage_video_chats=True,
                ),
            )
            await query.answer("ʀᴇᴘʀᴏᴍᴏᴛᴇᴅ!", show_alert=False)
    except Exception as e:
        await query.answer(f"ᴇʀʀᴏʀ: {str(e)}", show_alert=True)


# ============ MESSAGE MANAGEMENT ============

@app.on_message(filters.command("purge") & ~filters.private)
@adminsOnly("can_delete_messages")
async def purgeFunc(_, message: Message):
    repliedmsg = message.reply_to_message
    await message.delete()

    if not repliedmsg:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘᴜʀɢᴇ")

    cmd = message.command
    if len(cmd) > 1 and cmd[1].isdigit():
        purge_to = repliedmsg.id + int(cmd[1])
        if purge_to > message.id:
            purge_to = message.id
    else:
        purge_to = message.id

    chat_id = message.chat.id
    message_ids = []

    for message_id in range(repliedmsg.id, purge_to):
        message_ids.append(message_id)

        if len(message_ids) == 100:
            await app.delete_messages(chat_id=chat_id, message_ids=message_ids, revoke=True)
            message_ids = []

    if len(message_ids) > 0:
        await app.delete_messages(chat_id=chat_id, message_ids=message_ids, revoke=True)


@app.on_message(filters.command("del") & ~filters.private)
@adminsOnly("can_delete_messages")
async def deleteFunc(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ")
    await message.reply_to_message.delete()
    await message.delete()


# ============ PIN & UNPIN ============

@app.on_message(filters.command(["unpinall"]) & filters.group & ~BANNED_USERS)
@adminsOnly("can_pin_messages")
async def pin(_, message: Message):
    if message.command[0] == "unpinall":
        return await message.reply_text(
            "ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="✓ ʏᴇs", callback_data="unpin_yes"),
                        InlineKeyboardButton(text="✕ ɴᴏ", callback_data="unpin_no"),
                    ],
                ]
            ),
        )


@app.on_callback_query(filters.regex(r"unpin_(yes|no)"))
async def callback_query_handler(_, query: CallbackQuery):
    if query.data == "unpin_yes":
        await app.unpin_all_chat_messages(query.message.chat.id)
        return await query.message.edit_text("✓ ᴀʟʟ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇs ʜᴀᴠᴇ ʙᴇᴇɴ ᴜɴᴘɪɴɴᴇᴅ")
    elif query.data == "unpin_no":
        return await query.message.edit_text("✕ ᴜɴᴘɪɴ ᴄᴀɴᴄᴇʟʟᴇᴅ")


@app.on_message(filters.command(["pin", "unpin"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_pin_messages")
async def pin_message(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘɪɴ/ᴜɴᴘɪɴ")
    r = message.reply_to_message
    if message.command[0][0] == "u":
        await r.unpin()
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 ᴠɪᴇᴡ", url=r.link)]])
        return await message.reply_text("✓ ᴍᴇssᴀɢᴇ ᴜɴᴘɪɴɴᴇᴅ", reply_markup=keyboard)
    
    await r.pin(disable_notification=True)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 ᴊᴜᴍᴘ ᴛᴏ ᴘɪɴ", url=r.link)]])
    await message.reply_text("✓ ᴍᴇssᴀɢᴇ ᴘɪɴɴᴇᴅ", reply_markup=keyboard)
    await log_action(message.chat.id, "PIN", r.from_user.id if r.from_user else 0, message.from_user.id)


# ============ MUTE & UNMUTE ============

@app.on_message(filters.command(["mute", "tmute"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def mute(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴍᴜᴛᴇ ᴍʏsᴇʟғ")
    if user_id in SUDOERS:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴍᴜᴛᴇ sᴜᴅᴏ ᴜsᴇʀs!")
    if user_id in [
        member.user.id
        async for member in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴍᴜᴛᴇ ᴀᴅᴍɪɴs")
    
    mention = (await app.get_users(user_id)).mention
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 ᴜɴᴍᴜᴛᴇ", callback_data=f"unmute_{user_id}")]])
    msg = (
        f"**ᴍᴜᴛᴇᴅ ᴜsᴇʀ:** {mention}\n"
        f"**ᴍᴜᴛᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜs'}\n"
    )
    
    if message.command[0] == "tmute":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_mute = await time_converter(message, time_value)
        msg += f"**ᴍᴜᴛᴇᴅ ғᴏʀ:** {time_value}\n"
        if temp_reason:
            msg += f"**ʀᴇᴀsᴏɴ:** {temp_reason}"
        try:
            if len(time_value[:-1]) < 3:
                await message.chat.restrict_member(
                    user_id,
                    permissions=ChatPermissions(),
                    until_date=temp_mute,
                )
                replied_message = message.reply_to_message
                if replied_message:
                    message = replied_message
                await message.reply_text(msg, reply_markup=keyboard)
                await log_action(message.chat.id, "TMUTE", user_id, message.from_user.id, temp_reason)
            else:
                await message.reply_text("ᴛɪᴍᴇ ᴠᴀʟᴜᴇ ᴛᴏᴏ ʟᴀʀɢᴇ")
        except AttributeError:
            pass
        return
    
    if reason:
        msg += f"**ʀᴇᴀsᴏɴ:** {reason}"
    
    await message.chat.restrict_member(user_id, permissions=ChatPermissions())
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg, reply_markup=keyboard)
    await log_action(message.chat.id, "MUTE", user_id, message.from_user.id, reason)


@app.on_message(filters.command("unmute") & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def unmute(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    await message.chat.unban_member(user_id)
    umention = (await app.get_users(user_id)).mention
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔇 ʀᴇᴍᴜᴛᴇ", callback_data=f"remute_{user_id}")]])
    await message.reply_text(f"✓ ᴜɴᴍᴜᴛᴇᴅ {umention}", reply_markup=keyboard)
    await log_action(message.chat.id, "UNMUTE", user_id, message.from_user.id)


@app.on_callback_query(filters.regex(r"^(unmute|remute)_\d+"))
async def mute_callbacks(_, query: CallbackQuery):
    try:
        action = query.data.split("_")[0]
        user_id = int(query.data.split("_")[1])
        
        if action == "unmute":
            await query.message.chat.unban_member(user_id)
            await query.answer("ᴜɴᴍᴜᴛᴇᴅ!", show_alert=False)
        elif action == "remute":
            await query.message.chat.restrict_member(user_id, permissions=ChatPermissions())
            await query.answer("ʀᴇᴍᴜᴛᴇᴅ!", show_alert=False)
    except Exception as e:
        await query.answer(f"ᴇʀʀᴏʀ: {str(e)}", show_alert=True)


# ============ WARN SYSTEM ============

@app.on_message(filters.command(["warn", "swarn"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def warn_user(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    chat_id = message.chat.id
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴡᴀʀɴ ᴍʏsᴇʟғ")
    if user_id in SUDOERS:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴡᴀʀɴ sᴜᴅᴏ ᴜsᴇʀs!")
    if user_id in [
        member.user.id
        async for member in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴡᴀʀɴ ᴀᴅᴍɪɴs")
    
    user, warns = await asyncio.gather(
        app.get_users(user_id),
        get_warn(chat_id, await int_to_alpha(user_id)),
    )
    mention = user.mention
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✕ ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ", callback_data=f"unwarn_{user_id}")]])
    if warns:
        warns = warns["warns"]
    else:
        warns = 0
    
    if message.command[0][0] == "s":
        await message.reply_to_message.delete()
        await app.delete_user_history(message.chat.id, user_id)
    
    if warns >= 2:
        await message.chat.ban_member(user_id)
        await message.reply_text(f"⚠️ {mention} ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ (ᴡᴀʀɴs ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ)")
        await remove_warns(chat_id, await int_to_alpha(user_id))
        await log_action(chat_id, "WARN_BAN", user_id, message.from_user.id, reason)
    else:
        warn = {"warns": warns + 1}
        msg = f"""
**ᴡᴀʀɴᴇᴅ ᴜsᴇʀ:** {mention}
**ᴡᴀʀɴᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜs'}
**ʀᴇᴀsᴏɴ:** {reason or 'ɴᴏ ʀᴇᴀsᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ'}
**ᴡᴀʀɴs:** {warns + 1}/3"""
        replied_message = message.reply_to_message
        if replied_message:
            message = replied_message
        await message.reply_text(msg, reply_markup=keyboard)
        await add_warn(chat_id, await int_to_alpha(user_id), warn)
        await log_action(chat_id, "WARN", user_id, message.from_user.id, reason)


@app.on_callback_query(filters.regex("unwarn_") & ~BANNED_USERS)
async def remove_warning(_, cq: CallbackQuery):
    from_user = cq.from_user
    chat_id = cq.message.chat.id
    permissions = await member_permissions(chat_id, from_user.id)
    permission = "can_restrict_members"
    if permission not in permissions:
        return await cq.answer(
            f"ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴘᴇʀᴍɪssɪᴏɴs\nɴᴇᴇᴅᴇᴅ: {permission}",
            show_alert=True,
        )
    user_id = cq.data.split("_")[1]
    warns = await get_warn(chat_id, await int_to_alpha(user_id))
    if warns:
        warns = warns["warns"]
    if not warns or warns == 0:
        return await cq.answer("ᴜsᴇʀ ʜᴀs ɴᴏ ᴡᴀʀɴɪɴɢs", show_alert=True)
    warn = {"warns": warns - 1}
    await add_warn(chat_id, await int_to_alpha(user_id), warn)
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n✓ ᴡᴀʀɴ ʀᴇᴍᴏᴠᴇᴅ ʙʏ {from_user.mention}"
    await cq.message.edit(text)
    await cq.answer("ᴡᴀʀɴ ʀᴇᴍᴏᴠᴇᴅ!", show_alert=False)


@app.on_message(filters.command("rmwarns") & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def remove_warnings(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    mention = (await app.get_users(user_id)).mention
    chat_id = message.chat.id
    warns = await get_warn(chat_id, await int_to_alpha(user_id))
    if warns:
        warns = warns["warns"]
    if warns == 0 or not warns:
        await message.reply_text(f"{mention} ʜᴀs ɴᴏ ᴡᴀʀɴɪɴɢs")
    else:
        await remove_warns(chat_id, await int_to_alpha(user_id))
        await message.reply_text(f"✓ ʀᴇᴍᴏᴠᴇᴅ ᴀʟʟ ᴡᴀʀɴs ᴏғ {mention}")
        await log_action(chat_id, "RMWARNS", user_id, message.from_user.id)


@app.on_message(filters.command("warns") & ~filters.private & ~BANNED_USERS)
@capture_err
async def check_warns(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    warns = await get_warn(message.chat.id, await int_to_alpha(user_id))
    mention = (await app.get_users(user_id)).mention
    if warns:
        warns = warns["warns"]
    else:
        return await message.reply_text(f"{mention} ʜᴀs ɴᴏ ᴡᴀʀɴɪɴɢs")
    return await message.reply_text(f"{mention} ʜᴀs **{warns}/3** ᴡᴀʀɴɪɴɢs")


# ============ SPECIAL COMMANDS ============

BOT_ID = app.id


async def ban_members(chat_id, user_id, bot_permission, total_members, msg):
    """Ban all members in a chat."""
    banned_count = 0
    failed_count = 0
    ok = await msg.reply_text(
        f"ᴛᴏᴛᴀʟ ᴍᴇᴍʙᴇʀs: {total_members}\n**sᴛᴀʀᴛɪɴɢ ʙᴀɴ ᴘʀᴏᴄᴇss...**"
    )

    while failed_count <= 30:
        async for member in app.get_chat_members(chat_id):
            if failed_count > 30:
                break

            try:
                if member.user.id != user_id and member.user.id not in SUDOERS:
                    await app.ban_chat_member(chat_id, member.user.id)
                    banned_count += 1

                    if banned_count % 5 == 0:
                        try:
                            await ok.edit_text(
                                f"ʙᴀɴɴᴇᴅ: {banned_count}/{total_members}"
                            )
                        except Exception:
                            pass

            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception:
                failed_count += 1

        if failed_count <= 30:
            await asyncio.sleep(5)

    await ok.edit_text(
        f"✓ ᴛᴏᴛᴀʟ ʙᴀɴɴᴇᴅ: {banned_count}\n✕ ғᴀɪʟᴇᴅ: {failed_count}\n**ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ**"
    )


@app.on_message(filters.command("banall") & filters.user(SUDOERS))
async def ban_all(_, msg):
    """Ban all members in chat (SUDO ONLY)."""
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    bot = await app.get_chat_member(chat_id, BOT_ID)
    bot_permission = bot.privileges.can_restrict_members

    if bot_permission:
        total_members = 0
        async for _ in app.get_chat_members(chat_id):
            total_members += 1

        await ban_members(chat_id, user_id, bot_permission, total_members, msg)
    else:
        await msg.reply_text("ɪ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ʙᴀɴ ᴍᴇᴍʙᴇʀs")


@app.on_message(filters.command("unbanme"))
async def unbanme(client, message):
    """Unban yourself from a group."""
    try:
        if len(message.command) < 2:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("ℹ️ ʜᴇʟᴘ", callback_data="unbanme_help")]])
            return await message.reply_text("ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ", reply_markup=keyboard)

        group_id = message.command[1]

        try:
            await client.unban_chat_member(group_id, message.from_user.id)

            try:
                member = await client.get_chat_member(group_id, message.from_user.id)
                if member.status == "member":
                    group_link = await get_group_link(client, group_id)
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=group_link)]])
                    return await message.reply_text("✓ ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴜɴʙᴀɴɴᴇᴅ", reply_markup=keyboard)
            except UserNotParticipant:
                pass

            try:
                group_link = await get_group_link(client, group_id)
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=group_link)]])
                await message.reply_text("✓ ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ", reply_markup=keyboard)
            except InviteHashExpired:
                await message.reply_text("✓ ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ (ᴄᴀɴɴᴏᴛ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ)")
        except ChatAdminRequired:
            await message.reply_text("✕ ɪ ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ɢʀᴏᴜᴘ")
    except Exception as e:
        await message.reply_text(f"✕ ᴇʀʀᴏʀ: {str(e)}")


async def get_group_link(client, group_id):
    """Get group link or username."""
    chat = await client.get_chat(group_id)
    if chat.username:
        return f"https://t.me/{chat.username}"
    else:
        invite_link = await client.export_chat_invite_link(group_id)
        return invite_link


@app.on_callback_query(filters.regex("unbanme_help"))
async def unbanme_help(_, query: CallbackQuery):
    """Help for unbanme command."""
    help_text = """
**ʜᴏᴡ ᴛᴏ ᴜsᴇ /unbanme:**

1. ɢᴇᴛ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ
2. sᴇɴᴅ: `/unbanme [ɢʀᴏᴜᴘ_ɪᴅ]`

**ᴇxᴀᴍᴘʟᴇ:**
`/unbanme -1001234567890`
"""
    await query.message.edit_text(help_text)
    await query.answer("ℹ️ ʜᴇʟᴘ", show_alert=False)


@app.on_message(filters.command("modlog") & ~filters.private)
@adminsOnly("can_restrict_members")
async def modlog(_, message: Message):
    """View recent moderation logs."""
    chat_id = message.chat.id
    limit = 5

    if len(message.command) > 1 and message.command[1].isdigit():
        limit = min(int(message.command[1]), 20)

    logs = await actionsdb.find({"chat_id": chat_id}).sort("timestamp", -1).limit(limit).to_list(None)

    if not logs:
        return await message.reply_text("ɴᴏ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ ʟᴏɢs ғᴏᴜɴᴅ")

    log_text = "**ᴍᴏᴅᴇʀᴀᴛɪᴏɴ ʟᴏɢs:**\n\n"
    for log in logs:
        try:
            user = await app.get_users(log["user_id"])
            admin = await app.get_users(log["admin_id"]) if log["admin_id"] else None
            log_text += f"**ᴀᴄᴛɪᴏɴ:** {log['action']}\n"
            log_text += f"**ᴜsᴇʀ:** {user.mention}\n"
            log_text += f"**ᴀᴅᴍɪɴ:** {admin.mention if admin else 'ᴜɴᴋɴᴏᴡɴ'}\n"
            if log.get("reason"):
                log_text += f"**ʀᴇᴀsᴏɴ:** {log['reason']}\n"
            log_text += "─" * 20 + "\n"
        except Exception:
            continue

    await message.reply_text(log_text)
