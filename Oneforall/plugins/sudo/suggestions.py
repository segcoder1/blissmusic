import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from Oneforall import app
from Oneforall.utils.decorators.language import language
from config import LOGGER_ID


# ─────────────────────────────
# SUGGESTION SYSTEM
# ─────────────────────────────
@app.on_message(filters.command(["suggestion", "suggest"], prefixes=["/", "!", "."]))
@language
async def handle_suggestion(client, message: Message, _):
    """
    Handle user suggestions and forward them to logger channel
    Usage: /suggestion <your suggestion text>
    Available in: Personal DM and Group Chats
    """
    
    if not LOGGER_ID:
        return await message.reply_text(
            "❌ **Logger channel not configured!**\n"
            "Please set LOGGER_ID in config.py"
        )
    
    # Check if suggestion text is provided
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "📝 **Usage:** `/suggestion <your suggestion>`\n\n"
            "Example: `/suggestion Add dark mode to the bot`"
        )
    
    # Get suggestion text
    if message.reply_to_message:
        suggestion_text = message.reply_to_message.text or message.reply_to_message.caption
        if not suggestion_text:
            return await message.reply_text("❌ No text found in replied message!")
    else:
        suggestion_text = " ".join(message.command[1:])
    
    # Prepare suggestion data
    user = message.from_user
    chat = message.chat
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S UTC")
    
    # Determine chat type
    if message.chat.type.name == "PRIVATE":
        chat_info = f"**Personal DM** from {user.mention}"
        chat_link = f"[View Profile](tg://user?id={user.id})"
    else:
        chat_info = f"**Group:** {chat.title}"
        if message.message_id:
            chat_link = f"[View Message](https://t.me/c/{str(chat.id)[4:]}/{message.message_id})"
        else:
            chat_link = "N/A"
    
    # Create formatted log message
    log_message = (
        f"📬 **NEW SUGGESTION**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **From:** {user.mention}\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"📝 **Username:** @{user.username or 'N/A'}\n\n"
        f"💬 **Chat:** {chat_info}\n"
        f"🔗 **Link:** {chat_link}\n\n"
        f"✍️ **Suggestion:**\n"
        f"```\n{suggestion_text}\n```\n\n"
        f"⏰ **Time:** {timestamp}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    # Send to logger channel
    try:
        await app.send_message(
            LOGGER_ID,
            log_message,
            parse_mode="markdown"
        )
        
        # Confirm to user
        await message.reply_text(
            "✅ **Suggestion received!**\n\n"
            "Thank you for your feedback! Your suggestion has been logged and will be reviewed by the team.",
            quote=True
        )
        
    except FloodWait as fw:
        await asyncio.sleep(int(fw.value))
        try:
            await app.send_message(LOGGER_ID, log_message, parse_mode="markdown")
            await message.reply_text(
                "✅ **Suggestion received!**\n\n"
                "Thank you for your feedback! Your suggestion has been logged and will be reviewed by the team.",
                quote=True
            )
        except Exception as e:
            await message.reply_text(
                f"⚠️ **Error sending suggestion!**\n\n"
                f"Error: `{str(e)}`\n"
                f"Please try again later.",
                quote=True
            )
    
    except Exception as e:
        await message.reply_text(
            f"❌ **Failed to send suggestion!**\n\n"
            f"Error: `{str(e)}`",
            quote=True
        )


# ─────────────────────────────
# SUGGESTION STATISTICS (BONUS)
# ─────────────────────────────
@app.on_message(filters.command(["suggestions"], prefixes=["/", "!", "."]))
@language
async def suggestion_info(client, message: Message, _):
    """
    Show information about the suggestion system
    """
    
    info_message = (
        "📬 **Suggestion System Information**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**📝 How to use:**\n"
        "1. Send `/suggestion <your text>` to submit a suggestion\n"
        "2. You can also reply to a message with `/suggestion`\n"
        "3. Your suggestion will be logged and reviewed\n\n"
        
        "**✨ Features:**\n"
        "• Works in personal DM and group chats\n"
        "• Tracks user info and timestamp\n"
        "• Organized logging system\n"
        "• Direct link to message source\n\n"
        
        "**📊 Logger Channel:**\n"
        f"• Logger ID: `{LOGGER_ID}`\n"
        "• All suggestions are sent here\n"
        "• Accessible to bot administrators only\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Questions?** Contact the bot administrators."
    )
    
    await message.reply_text(info_message, quote=True)
