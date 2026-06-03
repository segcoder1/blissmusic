from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta

try:
    from Oneforall import app
    from config import OWNER_ID
    from Oneforall.misc import SUDOERS
except ImportError as e:
    raise ImportError(f"Could not import: {e}")


class VCProtectionManager:
    """Voice Chat protection manager."""
    
    def __init__(self):
        self.active_vcs = {}
        self.vc_warnings = {}
        self.punishment_settings = {}
        self.global_bans = {}
    
    def get_punishment_setting(self, chat_id: int) -> dict:
        if chat_id not in self.punishment_settings:
            self.punishment_settings[chat_id] = {
                'warn_limit': 3,
                'action': 'ban',
                'mute_duration': 3600
            }
        return self.punishment_settings[chat_id]
    
    def set_punishment_setting(self, chat_id: int, warn_limit=None, action=None):
        settings = self.get_punishment_setting(chat_id)
        if warn_limit is not None:
            settings['warn_limit'] = warn_limit
        if action and action in ['warn', 'ban', 'gban', 'mute']:
            settings['action'] = action
    
    def mark_vc_active(self, chat_id: int):
        self.active_vcs[chat_id] = {'status': 'active', 'joined_at': datetime.now()}
    
    def mark_vc_inactive(self, chat_id: int):
        if chat_id in self.active_vcs:
            del self.active_vcs[chat_id]


vc_protection_mgr = VCProtectionManager()

@app.on_message(filters.command("joinvc") & filters.group)
async def handle_joinvc_command(client, message):
    """Command: /joinvc - Bot joins voice chat."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this.")
        return
    
    try:
        await client.join_voice_chat(chat_id)
        vc_protection_mgr.mark_vc_active(chat_id)
        await message.reply_text("✅ **Bot Joined Voice Chat**\n🔒 VC Protection ACTIVE")
        print(f"[VCProtection] Bot joined VC in {chat_id}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app.on_message(filters.command("leavevc") & filters.group)
async def handle_leavevc_command(client, message):
    """Command: /leavevc - Bot leaves voice chat."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        return
    
    try:
        await client.leave_voice_chat(chat_id)
        vc_protection_mgr.mark_vc_inactive(chat_id)
        await message.reply_text("✅ Bot left voice chat")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app.on_message(filters.command("setpunishment"))
async def handle_setpunishment_command(client, message):
    """Command: /setpunishment <limit> <action>"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return
    
    if not is_admin and user_id != OWNER_ID and user_id not in SUDOERS:
        return
    
    args = message.text.split()
    if len(args) < 3:
        current = vc_protection_mgr.get_punishment_setting(chat_id)
        await message.reply_text(f"Current: Limit={current['warn_limit']}, Action={current['action']}")
        return
    
    try:
        limit = int(args[1])
        action = args[2].lower()
        vc_protection_mgr.set_punishment_setting(chat_id, warn_limit=limit, action=action)
        await message.reply_text(f"✅ Settings updated: {limit} warns → {action}")
    except:
        await message.reply_text("❌ Invalid format")


print("[VCProtection] Module loaded!")
