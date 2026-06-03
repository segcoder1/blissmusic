from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta

try:
    from Oneforall import app, userbot
    from config import OWNER_ID
    from Oneforall.misc import SUDOERS
    from Oneforall.core.userbot import assistantids
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


def get_assistant_client():
    """Get the first available assistant client from userbot."""
    try:
        if hasattr(userbot, 'one') and userbot.one:
            return userbot.one
        elif hasattr(userbot, 'two') and userbot.two:
            return userbot.two
        elif hasattr(userbot, 'three') and userbot.three:
            return userbot.three
        elif hasattr(userbot, 'four') and userbot.four:
            return userbot.four
        elif hasattr(userbot, 'five') and userbot.five:
            return userbot.five
    except:
        pass
    return None


@app.on_message(filters.command("joinvc") & filters.group)
async def handle_joinvc_command(client, message):
    """Command: /joinvc - Assistant joins voice chat (not the bot)."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        await message.reply_text("❌ Could not verify your permissions.")
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this command.")
        return
    
    # Get assistant client
    assistant_client = get_assistant_client()
    if not assistant_client:
        await message.reply_text("❌ No assistant account available. Configure STRING1-STRING5 in config.")
        return
    
    try:
        await assistant_client.join_voice_chat(chat_id)
        vc_protection_mgr.mark_vc_active(chat_id)
        
        # Get assistant info
        try:
            assistant_info = await assistant_client.get_me()
            assistant_name = assistant_info.first_name or "Assistant"
        except:
            assistant_name = "Assistant"
        
        await message.reply_text(
            f"✅ **Assistant Joined Voice Chat**\n"
            f"👤 **Assistant:** `{assistant_name}`\n"
            f"🔒 **VC Protection ACTIVE**"
        )
        print(f"[VCProtection] Assistant joined VC in chat {chat_id}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
        print(f"[VCProtection] Failed to join VC: {e}")


@app.on_message(filters.command("leavevc") & filters.group)
async def handle_leavevc_command(client, message):
    """Command: /leavevc - Assistant leaves voice chat."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        await message.reply_text("❌ Could not verify your permissions.")
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this command.")
        return
    
    # Get assistant client
    assistant_client = get_assistant_client()
    if not assistant_client:
        await message.reply_text("❌ No assistant account available.")
        return
    
    try:
        await assistant_client.leave_voice_chat(chat_id)
        vc_protection_mgr.mark_vc_inactive(chat_id)
        await message.reply_text("✅ **Assistant Left Voice Chat**")
        print(f"[VCProtection] Assistant left VC in chat {chat_id}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
        print(f"[VCProtection] Failed to leave VC: {e}")


@app.on_message(filters.command("vcprotect") & filters.group)
async def handle_vcprotect_command(client, message):
    """Command: /vcprotect - Show VC protection status and settings."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        await message.reply_text("❌ Could not verify your permissions.")
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this command.")
        return
    
    settings = vc_protection_mgr.get_punishment_setting(chat_id)
    vc_status = "✅ ACTIVE" if chat_id in vc_protection_mgr.active_vcs else "❌ INACTIVE"
    
    response = (
        "🛡️ **Voice Chat Protection Settings**\n\n"
        f"**Status:** {vc_status}\n"
        f"**Warn Limit:** {settings['warn_limit']}\n"
        f"**Action:** {settings['action'].upper()}\n"
        f"**Mute Duration:** {settings['mute_duration']}s\n\n"
        "**Commands:**\n"
        "• `/joinvc` - Assistant joins voice chat\n"
        "• `/leavevc` - Assistant leaves voice chat\n"
        "• `/vcprotect` - Show this menu"
    )
    
    await message.reply_text(response)
    print(f"[VCProtection] /vcprotect command used by {user_id} in chat {chat_id}")


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
