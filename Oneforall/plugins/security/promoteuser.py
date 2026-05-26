from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ChatPermissions
)
from datetime import datetime
from Oneforall import app
from Oneforall.utils.mongo import db
from Oneforall.misc import SUDOERS
import importlib.util

# ─── LOAD CONFIG ───
def load_config():
    """Load OWNER_ID from config.py"""
    try:
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        return getattr(config, "OWNER_ID", None)
    except:
        return None

OWNER_ID = load_config()

# ─── DATABASE KEYS ───
PROMOTIONS_DB = "PROMOTIONS_DATA"

# ─── HELP STRING ───
__HELP__ = """
✦ Promote:

✧ /promote @username - Promote user with standard permissions.
✧ /promote (reply) - Promote replied user with standard permissions.
✧ /promote (user_id) - Promote user by ID with standard permissions.
✧ /fullpromote @username - Promote user with all permissions including add admin.
✧ /fullpromote (reply) - Promote replied user with all permissions.
✧ /fullpromote (user_id) - Promote user by ID with all permissions.
✧ /demote @username - Demote promoted user.
✧ /demote (reply) - Demote replied user.
✧ /demote (user_id) - Demote user by ID.
"""

# ─── PERMISSIONS SETUP ───
STANDARD_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_manage_topics=True,
)

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=True,
    can_delete_messages=True,
    can_edit_messages=True,
    can_restrict_members=True,
    can_promote_members=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_manage_topics=True,
    can_manage_video_chats=True,
)

# ─── UTILS ───
async def is_authorized(user_id: int, chat_id: int):
    """Check if user is authorized to promote/demote"""
    if OWNER_ID and user_id == OWNER_ID:
        return True
    if user_id in SUDOERS:
        return True
    
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except:
        return False

async def can_add_admin(user_id: int, chat_id: int):
    """Check if user has permission to add admins"""
    if OWNER_ID and user_id == OWNER_ID:
        return True
    if user_id in SUDOERS:
        return True
    
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status == "creator":
            return True
        if member.status == "administrator" and member.can_promote_members:
            return True
    except:
        pass
    return False

async def get_promotion_data(chat_id: int, user_id: int):
    """Get promotion data for user"""
    data = await db.get(PROMOTIONS_DB) or {}
    key = f"{chat_id}_{user_id}"
    return data.get(key)

async def set_promotion_data(chat_id: int, user_id: int, promoted_by: int, promotion_type: str, promoted_at: str):
    """Store promotion data"""
    data = await db.get(PROMOTIONS_DB) or {}
    key = f"{chat_id}_{user_id}"
    data[key] = {
        "promoted_by": promoted_by,
        "type": promotion_type,
        "promoted_at": promoted_at
    }
    await db.set(PROMOTIONS_DB, data)

async def remove_promotion_data(chat_id: int, user_id: int):
    """Remove promotion data"""
    data = await db.get(PROMOTIONS_DB) or {}
    key = f"{chat_id}_{user_id}"
    data.pop(key, None)
    await db.set(PROMOTIONS_DB, data)

async def get_target_user(message: Message):
    """Get target user from message"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    elif len(message.command) < 2:
        return None
    
    try:
        arg = message.command[1]
        if arg.isdigit():
            return await app.get_users(int(arg))
        else:
            return await app.get_users(arg)
    except:
        return None

# ─── PROMOTE COMMAND ───
@app.on_message(filters.command("promote") & filters.group)
async def promote_cmd(_, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    
    # Check authorization
    if not await is_authorized(user.id, chat_id):
        return await message.reply("❌ you don't have permission to promote users.")
    
    # Check if can add admin
    if not await can_add_admin(user.id, chat_id):
        return await message.reply("❌ you don't have permission to add admins.")
    
    # Get target user
    target = await get_target_user(message)
    if not target:
        return await message.reply("❌ give username, user id, or reply to user.")
    
    if user.id == target.id:
        return await message.reply("💀 you can't promote yourself.")
    
    try:
        # Promote user with standard permissions
        await app.promote_chat_member(
            chat_id,
            target.id,
            privileges=STANDARD_PERMISSIONS
        )
        
        # Store promotion data
        await set_promotion_data(chat_id, target.id, user.id, "standard", datetime.utcnow().isoformat())
        
        # Create callback buttons
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ demote", callback_data=f"demote|{chat_id}|{target.id}"),
                InlineKeyboardButton("✕ close", callback_data="close")
            ]
        ])
        
        # Send promotion message
        text = (
            f"✨ user promoted!\n\n"
            f"👤 user: {target.mention}\n"
            f"🔑 rights: standard permissions\n"
            f"📍 promoted by: {user.mention}\n"
            f"⏰ time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        
        await message.reply_photo(
            photo="https://img.freepik.com/premium-photo/gold-luxury-crown-with-diamonds-isolated-dark-background_566556-221.jpg",
            caption=text,
            reply_markup=buttons
        )
        
    except Exception as e:
        await message.reply(f"❌ error promoting user: {str(e)}")

# ─── FULLPROMOTE COMMAND ───
@app.on_message(filters.command("fullpromote") & filters.group)
async def fullpromote_cmd(_, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    
    # Check authorization
    if not await is_authorized(user.id, chat_id):
        return await message.reply("❌ you don't have permission to promote users.")
    
    # Check if can add admin
    if not await can_add_admin(user.id, chat_id):
        return await message.reply("❌ you don't have permission to add admins.")
    
    # Get target user
    target = await get_target_user(message)
    if not target:
        return await message.reply("❌ give username, user id, or reply to user.")
    
    if user.id == target.id:
        return await message.reply("💀 you can't promote yourself.")
    
    try:
        # Promote user with full permissions
        await app.promote_chat_member(
            chat_id,
            target.id,
            privileges=FULL_PERMISSIONS
        )
        
        # Store promotion data
        await set_promotion_data(chat_id, target.id, user.id, "full", datetime.utcnow().isoformat())
        
        # Create callback buttons
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ demote", callback_data=f"demote|{chat_id}|{target.id}"),
                InlineKeyboardButton("✕ close", callback_data="close")
            ]
        ])
        
        # Send promotion message
        text = (
            f"✨ user promoted!\n\n"
            f"👤 user: {target.mention}\n"
            f"🔑 rights: all permissions (with add admin)\n"
            f"📍 promoted by: {user.mention}\n"
            f"⏰ time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        
        await message.reply_photo(
            photo="https://img.freepik.com/premium-photo/royal-gold-crown-with-gemstones-white-background_566556-3873.jpg",
            caption=text,
            reply_markup=buttons
        )
        
    except Exception as e:
        await message.reply(f"❌ error promoting user: {str(e)}")

# ─── DEMOTE COMMAND ───
@app.on_message(filters.command("demote") & filters.group)
async def demote_cmd(_, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    
    # Check authorization
    if not await is_authorized(user.id, chat_id):
        return await message.reply("❌ you don't have permission to demote users.")
    
    # Get target user
    target = await get_target_user(message)
    if not target:
        return await message.reply("❌ give username, user id, or reply to user.")
    
    try:
        # Check if user was promoted by this bot
        promotion_data = await get_promotion_data(chat_id, target.id)
        if not promotion_data:
            return await message.reply(f"❌ user {target.mention} was not promoted by bot.")
        
        # Demote user
        await app.promote_chat_member(
            chat_id,
            target.id,
            privileges=ChatPermissions()
        )
        
        # Remove promotion data
        await remove_promotion_data(chat_id, target.id)
        
        # Create callback buttons
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✕ close", callback_data="close")
            ]
        ])
        
        # Send demotion message
        text = (
            f"💔 user demoted!\n\n"
            f"👤 user: {target.mention}\n"
            f"🔑 rights: removed\n"
            f"📍 demoted by: {user.mention}\n"
            f"⏰ time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        
        await message.reply_photo(
            photo="https://img.freepik.com/premium-photo/broken-crown-dark-background_505814-58589.jpg",
            caption=text,
            reply_markup=buttons
        )
        
    except Exception as e:
        await message.reply(f"❌ error demoting user: {str(e)}")

# ─── CALLBACKS ───
@app.on_callback_query(filters.regex("^demote\\|"))
async def demote_callback(_, query: CallbackQuery):
    """Handle demote callback button"""
    user = query.from_user
    data = query.data.split("|")
    chat_id, target_id = int(data[1]), int(data[2])
    
    # Check authorization
    if not await is_authorized(user.id, chat_id):
        return await query.answer("you don't have permission!", show_alert=True)
    
    try:
        target = await app.get_users(target_id)
        
        # Check if user was promoted
        promotion_data = await get_promotion_data(chat_id, target_id)
        if not promotion_data:
            return await query.answer("user was not promoted!", show_alert=True)
        
        # Demote user
        await app.promote_chat_member(
            chat_id,
            target_id,
            privileges=ChatPermissions()
        )
        
        # Remove promotion data
        await remove_promotion_data(chat_id, target_id)
        
        # Update message
        text = (
            f"💔 user demoted!\n\n"
            f"👤 user: {target.mention}\n"
            f"🔑 rights: removed\n"
            f"📍 demoted by: {user.mention}\n"
            f"⏰ time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        
        await query.message.edit_caption(caption=text)
        await query.answer("user demoted!", show_alert=False)
        
    except Exception as e:
        await query.answer(f"error: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("^close$"))
async def close_callback(_, query: CallbackQuery):
    """Handle close callback button"""
    await query.message.delete()
