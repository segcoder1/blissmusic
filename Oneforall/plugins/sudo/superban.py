import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus

from Oneforall import app
from Oneforall.misc import SUDOERS
from Oneforall.utils import get_readable_time
from Oneforall.utils.database import (
    add_banned_user,
    get_served_chats,
    add_superban_team_member,
    remove_superban_team_member,
    get_superban_team,
    is_superban_team_member,
    add_superban_request,
    get_superban_request,
    update_superban_request_status,
    get_federations,
    get_fed_bans,
    add_fed_ban,
)
from Oneforall.utils.decorators.language import language
from Oneforall.utils.extraction import extract_user
from config import BANNED_USERS, superban_storage_id

LOG_GIF = "https://files.catbox.moe/qdm48e.gif"


# ─────────────────────────────
# SUPERBAN TEAM MANAGEMENT
# ───────���─────────────────────
@app.on_message(filters.command(["steamadd"], prefixes=["/", "!", "."]) & SUDOERS)
@language
async def add_steam_member(client, message: Message, _):
    """Add member to superban team - SUDOERS ONLY"""
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(_["steam_1"])
    
    user = await extract_user(message)
    
    is_member = await is_superban_team_member(user.id)
    if is_member:
        return await message.reply_text(_["steam_2"].format(user.mention))
    
    await add_superban_team_member(user.id)
    
    await message.reply_text(
        _["steam_3"].format(user.mention)
    )


@app.on_message(filters.command(["steamrem"], prefixes=["/", "!", "."]) & SUDOERS)
@language
async def remove_steam_member(client, message: Message, _):
    """Remove member from superban team - SUDOERS ONLY"""
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(_["steam_4"])
    
    user = await extract_user(message)
    
    is_member = await is_superban_team_member(user.id)
    if not is_member:
        return await message.reply_text(_["steam_5"].format(user.mention))
    
    await remove_superban_team_member(user.id)
    
    await message.reply_text(
        _["steam_6"].format(user.mention)
    )


@app.on_message(filters.command(["steamlist"], prefixes=["/", "!", "."]) & SUDOERS)
@language
async def list_steam_members(client, message: Message, _):
    """List all superban team members - SUDOERS ONLY"""
    team_members = await get_superban_team()
    
    if not team_members:
        return await message.reply_text(_["steam_7"])
    
    msg = _["steam_8"]
    count = 0
    
    for user_id in team_members:
        count += 1
        try:
            user = await app.get_users(user_id)
            msg += f"\n{count}. {user.mention} (`{user_id}`)"
        except:
            msg += f"\n{count}. `{user_id}`"
    
    await message.reply_text(msg)


# ─────────────────────────────
# SUPERBAN REQUEST SYSTEM
# ─────────────────────────────
@app.on_message(filters.command(["superban"], prefixes=["/", "!", "."]))
@language
async def superban_request(client, message: Message, _):
    """Create superban request - AVAILABLE TO ALL USERS"""
    if not superban_storage_id:
        return await message.reply_text(_["sb_1"])
    
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(_["sb_2"])
    
    user = await extract_user(message)
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else "ɴᴏ ʀᴇᴀsᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ"
    
    # Create request ID
    request_id = f"{message.chat.id}_{message.message_id}_{int(datetime.now().timestamp())}"
    
    # Store request in database
    request_data = {
        "request_id": request_id,
        "user_id": user.id,
        "user_mention": user.mention,
        "username": user.username or "ɴ/ᴀ",
        "first_name": user.first_name or "ɴ/ᴀ",
        "requested_by": message.from_user.mention,
        "requester_id": message.from_user.id,
        "chat_id": message.chat.id,
        "chat_title": message.chat.title,
        "message_id": message.message_id,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "status": "ᴘᴇɴᴅɪɴɢ"
    }
    
    await add_superban_request(request_id, request_data)
    
    # Create inline buttons for team
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ ᴀᴄᴄᴇᴘᴛ",
                callback_data=f"sb_accept_{request_id}"
            ),
            InlineKeyboardButton(
                text="❌ ᴅᴇᴄʟɪɴᴇ",
                callback_data=f"sb_decline_{request_id}"
            )
        ]
    ]
    
    # Send to superban log group
    log_msg = (
        f"🔔 **sᴜᴘᴇʀʙᴀɴ ʀᴇqᴜᴇsᴛ**\n\n"
        f"👤 **ᴜsᴇʀ:** {user.mention}\n"
        f"🆔 **ᴜsᴇʀ ɪᴅ:** `{user.id}`\n"
        f"📝 **ᴜsᴇʀɴᴀᴍᴇ:** @{user.username or 'ɴ/ᴀ'}\n"
        f"📌 **ʀᴇᴀsᴏɴ:** {reason}\n"
        f"👨‍💼 **ʀᴇqᴜᴇsᴛᴇᴅ ʙʏ:** {message.from_user.mention}\n"
        f"💬 **ɢʀᴏᴜᴘ:** {message.chat.title}\n"
        f"🔗 **ʟɪɴᴋ:** [ᴠɪᴇᴡ ᴍᴇssᴀɢᴇ](https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id})\n\n"
        f"⏰ **ᴛɪᴍᴇ:** {datetime.now().strftime('%d-%m-%Y %H:%M:%S ᴜᴛᴄ')}"
    )
    
    try:
        await app.send_message(
            superban_storage_id,
            log_msg,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await message.reply_text(f"❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇqᴜᴇsᴛ: {str(e)}")
    
    await message.reply_text(
        _["sb_3"].format(user.mention)
    )


@app.on_callback_query(filters.regex(r"^sb_accept_"))
async def accept_superban(client, callback: CallbackQuery):
    """Accept superban request - SUPERBAN TEAM ONLY"""
    # Check if user is in superban team
    is_member = await is_superban_team_member(callback.from_user.id)
    if not is_member:
        return await callback.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ sᴜᴘᴇʀʙᴀɴ ᴛᴇᴀᴍ!", show_alert=True)
    
    request_id = callback.data.replace("sb_accept_", "")
    
    request = await get_superban_request(request_id)
    if not request:
        return await callback.answer("❌ ʀᴇqᴜᴇsᴛ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)
    
    user_id = request["user_id"]
    
    # Update status
    await update_superban_request_status(request_id, "ᴀᴄᴄᴇᴘᴛᴇᴅ")
    
    # Global ban
    if user_id not in BANNED_USERS:
        BANNED_USERS.add(user_id)
    
    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    number_of_chats = 0
    
    mystic_msg = await callback.message.reply_text("⏳ ᴘʀᴏᴄᴇssɪɴɢ ɢʟᴏʙᴀʟ ʙᴀɴ...")
    
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user_id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
    
    await add_banned_user(user_id)
    
    # Federation ban
    federations = await get_federations()
    total_fed_chats = 0
    
    for federation in federations:
        fed_id = federation["fed_id"]
        fed_chats = federation.get("chats", [])
        total_fed_chats += len(fed_chats)
        
        # Add ban to federation
        await add_fed_ban(fed_id, user_id, request["reason"])
        
        # Ban from all federation chats
        for chat_id in fed_chats:
            try:
                await app.ban_chat_member(chat_id, user_id)
            except:
                continue
    
    # Send detailed log to superban storage with small caps
    log_msg = (
        f"✅ **sᴜᴘᴇʀʙᴀɴ ᴀᴄᴄᴇᴘᴛᴇᴅ**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ᴛᴀʀɢᴇᴛ ᴜsᴇʀ ɪɴғᴏ:**\n"
        f"  • **ɴᴀᴍᴇ:** {request['user_mention']}\n"
        f"  • **ᴜɪᴅ:** `{user_id}`\n"
        f"  • **ᴜsᴇʀɴᴀᴍᴇ:** @{request['username']}\n\n"
        f"📝 **ᴀᴄᴛɪᴏɴ ᴅᴇᴛᴀɪʟs:**\n"
        f"  • **ʀᴇᴀsᴏɴ:** {request['reason']}\n"
        f"  • **ʀᴇqᴜᴇsᴛᴇᴅ ʙʏ:** {request['requested_by']}\n"
        f"  • **ᴀᴄᴄᴇᴘᴛᴇᴅ ʙʏ:** {callback.from_user.mention}\n\n"
        f"💬 **ᴊᴜʀɪsᴅɪᴄᴛɪᴏɴ:**\n"
        f"  • **ᴏʀɪɢɪɴ ɢʀᴏᴜᴘ:** {request['chat_title']}\n"
        f"  • **ɢʟᴏʙᴀʟ ʙᴀɴɴᴇᴅ ғʀᴏᴍ:** {number_of_chats} ᴄʜᴀᴛs\n"
        f"  • **ғᴇᴅᴇʀᴀᴛɪᴏɴ ʙᴀɴɴᴇᴅ ғʀᴏᴍ:** {total_fed_chats} ᴄʜᴀᴛs\n"
        f"  • **ᴛᴏᴛᴀʟ ᴊᴜʀɪsᴅɪᴄᴛɪᴏɴ:** {number_of_chats + total_fed_chats} ᴄʜᴀᴛs\n\n"
        f"⏰ **ᴛɪᴍᴇsᴛᴀᴍᴘ:** {datetime.now().strftime('%d-%m-%Y %H:%M:%S ᴜᴛᴄ')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        await app.send_animation(
            superban_storage_id,
            LOG_GIF,
            caption=log_msg
        )
    except:
        try:
            await app.send_message(superban_storage_id, log_msg)
        except:
            pass
    
    # Edit callback message
    await callback.edit_message_text(
        f"{callback.message.text}\n\n✅ **ᴀᴄᴄᴇᴘᴛᴇᴅ ʙʏ:** {callback.from_user.mention}"
    )
    
    await mystic_msg.delete()
    
    await callback.answer(
        f"✅ sᴜᴘᴇʀʙᴀɴ ᴀᴄᴄᴇᴘᴛᴇᴅ ғᴏʀ {request['user_mention']}\n"
        f"📊 ᴛᴏᴛᴀʟ ᴀғғᴇᴄᴛᴇᴅ: {number_of_chats + total_fed_chats} ᴄʜᴀᴛs",
        show_alert=True
    )


@app.on_callback_query(filters.regex(r"^sb_decline_"))
async def decline_superban(client, callback: CallbackQuery):
    """Decline superban request - SUPERBAN TEAM ONLY"""
    # Check if user is in superban team
    is_member = await is_superban_team_member(callback.from_user.id)
    if not is_member:
        return await callback.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ sᴜᴘᴇʀʙᴀɴ ᴛᴇᴀᴍ!", show_alert=True)
    
    request_id = callback.data.replace("sb_decline_", "")
    
    request = await get_superban_request(request_id)
    if not request:
        return await callback.answer("❌ ʀᴇqᴜᴇsᴛ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)
    
    # Update status
    await update_superban_request_status(request_id, "ᴅᴇᴄʟɪɴᴇᴅ")
    
    # Send log
    log_msg = (
        f"❌ **sᴜᴘᴇʀʙᴀɴ ᴅᴇᴄʟɪɴᴇᴅ**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ᴛᴀʀɢᴇᴛ ᴜsᴇʀ:**\n"
        f"  • **ɴᴀᴍᴇ:** {request['user_mention']}\n"
        f"  • **ᴜɪᴅ:** `{request['user_id']}`\n\n"
        f"📝 **ᴅᴇᴄʟɪɴᴇ ɪɴғᴏ:**\n"
        f"  • **ʀᴇᴀsᴏɴ:** {request['reason']}\n"
        f"  • **ʀᴇqᴜᴇsᴛᴇᴅ ʙʏ:** {request['requested_by']}\n"
        f"  • **ᴅᴇᴄʟɪɴᴇᴅ ʙʏ:** {callback.from_user.mention}\n"
        f"  • **ɢʀᴏᴜᴘ:** {request['chat_title']}\n\n"
        f"⏰ **ᴛɪᴍᴇsᴛᴀᴍᴘ:** {datetime.now().strftime('%d-%m-%Y %H:%M:%S ᴜᴛᴄ')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        await app.send_message(superban_storage_id, log_msg)
    except:
        pass
    
    # Edit callback message
    await callback.edit_message_text(
        f"{callback.message.text}\n\n❌ **ᴅᴇᴄʟɪɴᴇᴅ ʙʏ:** {callback.from_user.mention}"
    )
    
    await callback.answer("❌ sᴜᴘᴇʀʙᴀɴ ʀᴇqᴜᴇsᴛ ᴅᴇᴄʟɪɴᴇᴅ", show_alert=True)
