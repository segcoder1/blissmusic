import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta

try:
    from Oneforall import app
    from config import OWNER_ID
    from Oneforall.misc import SUDOERS
except ImportError as e:
    raise ImportError(f"Could not import: {e}")


class AbusiveWordDetector:
    """Detects and handles abusive language."""
    
    def __init__(self):
        self.abusive_words = [
            "ass", "bitch", "bullshit", "crap", "damn", "fuck", "hell",
            "piss", "shit", "bastard", "motherfucker", "asshole", "dick"
        ]
        self.spam_patterns = [
            r"(.)\1{9,}",
            r"[A-Z]{5,}",
        ]
        self.abuse_warnings = {}
        self.abuse_settings = {}
    
    def get_abuse_settings(self, chat_id: int) -> dict:
        if chat_id not in self.abuse_settings:
            self.abuse_settings[chat_id] = {
                'enabled': True,
                'action': 'warn',
                'warn_limit': 3,
                'mute_duration': 3600
            }
        return self.abuse_settings[chat_id]
    
    def set_abuse_settings(self, chat_id: int, **kwargs):
        settings = self.get_abuse_settings(chat_id)
        for key, value in kwargs.items():
            if key in settings:
                settings[key] = value
    
    def contains_abusive_content(self, text: str) -> tuple:
        text_lower = text.lower()
        for word in self.abusive_words:
            if word in text_lower:
                return True, word
        for pattern in self.spam_patterns:
            if re.search(pattern, text):
                return True, "spam"
        return False, None
    
    def add_warning(self, chat_id: int, user_id: int) -> int:
        if chat_id not in self.abuse_warnings:
            self.abuse_warnings[chat_id] = {}
        if user_id not in self.abuse_warnings[chat_id]:
            self.abuse_warnings[chat_id][user_id] = []
        
        self.abuse_warnings[chat_id][user_id].append(datetime.now())
        cutoff = datetime.now() - timedelta(hours=24)
        self.abuse_warnings[chat_id][user_id] = [
            ts for ts in self.abuse_warnings[chat_id][user_id] if ts > cutoff
        ]
        return len(self.abuse_warnings[chat_id][user_id])


abuse_detector = AbusiveWordDetector()

@app.on_message(filters.group & ~filters.bot)
async def handle_abusive_content(client: Client, message: Message):
    """Monitor messages for abusive content."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    settings = abuse_detector.get_abuse_settings(chat_id)
    if not settings['enabled']:
        return
    
    is_abusive, detected = abuse_detector.contains_abusive_content(message.text or "")
    if not is_abusive:
        return
    
    try:
        await message.delete()
    except:
        pass
    
    warning_count = abuse_detector.add_warning(chat_id, user_id)
    warn_limit = settings['warn_limit']
    
    if warning_count >= warn_limit:
        if settings['action'] == 'ban':
            try:
                await client.ban_chat_member(chat_id, user_id)
                await message.reply_text(f"🚫 **User Banned** - Abusive language")
            except:
                pass
    else:
        await message.reply_text(
            f"⚠️ **Warning** - {message.from_user.mention}\n"
            f"Detected: `{detected}`\n"
            f"Warning: {warning_count}/{warn_limit}"
        )


print("[AntiAbuse] Module loaded!")
