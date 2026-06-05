"""
Channel Detection System with Logging
Detects participants joined via channel and logs everything to a designated channel
"""

from pyrogram import Client
from pyrogram.types import Chat, User, ChatMember
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChannelDetector:
    def __init__(self, assistant: Client, log_channel_id: int = None):
        """
        Initialize with assistant client from config string session
        
        Args:
            assistant: Client instance initialized with STRING_SESSION from config
            log_channel_id: Channel ID where logs will be sent (from config)
        """
        self.assistant = assistant
        self.log_channel_id = log_channel_id
        self.cache = {}
    
    async def send_log(self, message: str, log_type: str = "INFO"):
        """
        Send log message to the configured log channel
        
        Args:
            message: Log message content
            log_type: Type of log (INFO, WARNING, ERROR, DETECTION)
        """
        if not self.log_channel_id:
            logger.warning("Log channel ID not configured")
            return
        
        try:
            # Create formatted log message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_text = f"📊 **[{log_type}]** `{timestamp}`\n\n{message}"
            
            await self.assistant.send_message(
                chat_id=self.log_channel_id,
                text=log_text,
                parse_mode="markdown"
            )
            
        except Exception as e:
            logger.error(f"Error sending log to channel: {e}")
    
    async def get_channel_owner(self, chat_id: int) -> Optional[User]:
        """Get channel/group owner information"""
        try:
            chat: Chat = await self.assistant.get_chat(chat_id)
            
            if chat.is_channel:
                creator_id = chat.creator_id if hasattr(chat, 'creator_id') else None
                if creator_id:
                    owner = await self.assistant.get_users(creator_id)
                    return owner
            
            if hasattr(chat, 'owner_id'):
                owner = await self.assistant.get_users(chat.owner_id)
                return owner
            
            async for admin in self.assistant.get_chat_members(chat_id, filter="administrators"):
                if admin.status in ["creator", "administrator"]:
                    if admin.privileges and admin.privileges.is_admin:
                        return admin.user
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel owner for {chat_id}: {e}")
            await self.send_log(f"❌ Error getting owner for chat `{chat_id}`: {str(e)}", "ERROR")
            return None
    
    async def detect_channel_joined_participants(self, chat_id: int, send_log: bool = True) -> Dict:
        """
        Detect which participants joined via channel
        
        Args:
            chat_id: The chat/channel ID to monitor
            send_log: Whether to send detection log to channel
            
        Returns:
            Dictionary containing participant and channel information
        """
        try:
            chat: Chat = await self.assistant.get_chat(chat_id)
            
            # Get channel owner
            owner = await self.get_channel_owner(chat_id)
            owner_id = owner.id if owner else None
            
            # Get voice chat participants
            participants_list = []
            async for member in self.assistant.get_chat_members(chat_id):
                joined_via = await self._determine_join_source(chat_id, member)
                
                participants_list.append({
                    "user_id": member.user.id,
                    "user": member.user,
                    "first_name": member.user.first_name,
                    "last_name": member.user.last_name,
                    "username": member.user.username,
                    "joined_via": joined_via,
                    "join_date": member.joined_date if hasattr(member, 'joined_date') else None,
                    "is_bot": member.user.is_bot,
                    "status": member.status,
                })
            
            detection_result = {
                "chat_id": chat_id,
                "chat_title": chat.title,
                "is_channel": chat.is_channel,
                "is_supergroup": chat.is_supergroup,
                "is_group": chat.is_group,
                "owner": owner,
                "owner_id": owner_id,
                "owner_username": owner.username if owner else None,
                "total_members": chat.members_count if hasattr(chat, 'members_count') else len(participants_list),
                "total_participants": len(participants_list),
                "participants": participants_list,
                "channel_joined_count": sum(1 for p in participants_list if p["joined_via"] == "channel"),
            }
            
            # Send detection log
            if send_log:
                await self._send_detection_log(detection_result)
            
            # Cache the result
            self.cache[chat_id] = detection_result
            
            return detection_result
            
        except Exception as e:
            logger.error(f"Error detecting participants for {chat_id}: {e}")
            await self.send_log(f"❌ Detection failed for chat `{chat_id}`: {str(e)}", "ERROR")
            return {
                "chat_id": chat_id,
                "error": str(e),
                "participants": []
            }
    
    async def _send_detection_log(self, detection_result: Dict):
        """Send detailed detection log to channel"""
        try:
            if "error" in detection_result:
                log_text = f"❌ **Detection Error**\nChat ID: `{detection_result['chat_id']}`\nError: `{detection_result['error']}`"
                await self.send_log(log_text, "ERROR")
                return
            
            # Build detailed log
            owner_info = f"👤 {detection_result['owner_username'] or detection_result['owner_id']}" if detection_result['owner'] else "❌ Unknown"
            chat_type = "📢 Channel" if detection_result['is_channel'] else "👥 Group"
            
            log_text = f"""
🔍 **Channel Detection Report**

{chat_type}
📌 Title: `{detection_result['chat_title']}`
🆔 Chat ID: `{detection_result['chat_id']}`
👑 Owner: {owner_info}

📊 **Statistics**
├─ Total Members: `{detection_result['total_members']}`
├─ Total Participants: `{detection_result['total_participants']}`
└─ Joined via Channel: `{detection_result['channel_joined_count']}`

"""
            
            await self.send_log(log_text.strip(), "DETECTION")
            
            # Send participant list if not too large
            if detection_result['total_participants'] > 0 and detection_result['total_participants'] <= 50:
                await self._send_participants_log(detection_result['participants'])
            elif detection_result['total_participants'] > 50:
                await self.send_log(f"⚠️ Too many participants (`{detection_result['total_participants']}`). Showing summary only.", "WARNING")
                await self._send_participants_summary(detection_result['participants'])
            
        except Exception as e:
            logger.error(f"Error sending detection log: {e}")
    
    async def _send_participants_log(self, participants: List[Dict]):
        """Send detailed participants list"""
        try:
            # Group by join source
            channel_joined = [p for p in participants if p["joined_via"] == "channel"]
            direct_joined = [p for p in participants if p["joined_via"] == "direct"]
            bots = [p for p in participants if p["is_bot"]]
            
            log_text = "👥 **Participants Details**\n\n"
            
            # Channel joined participants
            if channel_joined:
                log_text += f"**📊 Joined via Channel ({len(channel_joined)})**\n"
                for p in channel_joined[:20]:  # Limit to 20
                    username = f"@{p['username']}" if p['username'] else f"`{p['user_id']}`"
                    status_emoji = "👤" if not p['is_bot'] else "🤖"
                    log_text += f"{status_emoji} {username}\n"
                if len(channel_joined) > 20:
                    log_text += f"... and `{len(channel_joined) - 20}` more\n"
                log_text += "\n"
            
            # Direct joined participants
            if direct_joined:
                log_text += f"**✉️ Direct Invites ({len(direct_joined)})**\n"
                for p in direct_joined[:10]:
                    username = f"@{p['username']}" if p['username'] else f"`{p['user_id']}`"
                    log_text += f"➕ {username}\n"
                if len(direct_joined) > 10:
                    log_text += f"... and `{len(direct_joined) - 10}` more\n"
                log_text += "\n"
            
            # Bots
            if bots:
                log_text += f"**🤖 Bots ({len(bots)})**\n"
                for p in bots:
                    username = f"@{p['username']}" if p['username'] else f"`{p['user_id']}`"
                    log_text += f"🔧 {username}\n"
            
            await self.send_log(log_text.strip(), "PARTICIPANTS")
            
        except Exception as e:
            logger.error(f"Error sending participants log: {e}")
    
    async def _send_participants_summary(self, participants: List[Dict]):
        """Send participants summary for large groups"""
        try:
            channel_joined = sum(1 for p in participants if p["joined_via"] == "channel")
            direct_joined = sum(1 for p in participants if p["joined_via"] == "direct")
            bots = sum(1 for p in participants if p["is_bot"])
            
            log_text = f"""
📊 **Participants Summary**
├─ Channel Joined: `{channel_joined}`
├─ Direct Invites: `{direct_joined}`
└─ Bots: `{bots}`
"""
            
            await self.send_log(log_text.strip(), "SUMMARY")
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
    
    async def _determine_join_source(self, chat_id: int, member: ChatMember) -> str:
        """Determine if participant joined via channel or direct invite"""
        try:
            if member.user.is_bot:
                return "bot"
            
            if member.status == "member":
                return "channel"
            
            if member.status in ["administrator", "creator"]:
                return "direct"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error determining join source: {e}")
            return "unknown"
    
    async def filter_channel_joined_only(self, chat_id: int) -> List[Dict]:
        """Get only participants who joined via channel"""
        try:
            detection = await self.detect_channel_joined_participants(chat_id, send_log=False)
            
            if "error" in detection:
                return []
            
            channel_joined = [
                p for p in detection["participants"] 
                if p["joined_via"] == "channel"
            ]
            
            return channel_joined
            
        except Exception as e:
            logger.error(f"Error filtering participants: {e}")
            return []
    
    async def get_admin_and_owner_info(self, chat_id: int) -> Dict:
        """Get detailed info about channel owner and admins with logging"""
        try:
            owner = await self.get_channel_owner(chat_id)
            
            admins = []
            async for admin in self.assistant.get_chat_members(chat_id, filter="administrators"):
                admins.append({
                    "user_id": admin.user.id,
                    "user": admin.user,
                    "username": admin.user.username,
                    "first_name": admin.user.first_name,
                    "status": admin.status,
                })
            
            result = {
                "owner": owner,
                "owner_id": owner.id if owner else None,
                "owner_username": owner.username if owner else None,
                "total_admins": len(admins),
                "admins": admins,
            }
            
            # Send admin info log
            log_text = f"👑 **Owner & Admins**\n"
            if owner:
                log_text += f"Owner: @{owner.username or owner.id}\n"
            log_text += f"Total Admins: `{len(admins)}`"
            
            await self.send_log(log_text, "ADMIN_INFO")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting admin info: {e}")
            await self.send_log(f"❌ Error fetching admin info: {str(e)}", "ERROR")
            return {
                "owner": None,
                "owner_id": None,
                "total_admins": 0,
                "admins": [],
                "error": str(e)
            }
    
    def get_cached_result(self, chat_id: int) -> Optional[Dict]:
        """Get cached detection result"""
        return self.cache.get(chat_id)


# Usage Integration
async def setup_channel_detector(assistant: Client, log_channel_id: int):
    """
    Setup channel detector with logging
    
    Args:
        assistant: Assistant client from config
        log_channel_id: Channel ID for logs (from config)
    
    Returns:
        ChannelDetector instance
    """
    detector = ChannelDetector(assistant, log_channel_id)
    
    # Send startup log
    await detector.send_log("✅ Channel Detector initialized and ready!", "INFO")
    
    return detector
