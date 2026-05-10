import random

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup

import config
from config import BANNED_USERS, lyrical
from Oneforall import YouTube, app
from Oneforall.utils.database import (
    is_autoplay_on,
    get_autoplay_mood,
    set_autoplay,
    set_autoplay_mood,
)
from Oneforall.utils.decorators.language import languageCB
from Oneforall.utils.inline import (
    autoplay_mood_markup,
    autoplay_language_markup,
)
from Oneforall.misc import db


# Store previous tracks per chat
previous_tracks = {}


@app.on_message(filters.command("songconfig") & filters.group & ~BANNED_USERS)
@languageCB
async def songconfig_command(client, message, _):
    """Command to configure autoplay with mood and language"""
    chat_id = message.chat.id
    
    mystic = await message.reply_text(
        "🎵 **Autoplay Configuration**\n\n"
        "Select your preferred mood to enable autoplay:"
    )
    
    buttons = autoplay_mood_markup(_)
    await mystic.edit_text(
        "🎵 **Autoplay Configuration**\n\n"
        "Select your preferred mood to enable autoplay:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@app.on_callback_query(filters.regex("songconfig_mood"))
@languageCB
async def handle_mood_selection(client, CallbackQuery, _):
    """Handle mood selection callback"""
    callback_data = CallbackQuery.data.strip()
    mood = callback_data.split(None, 1)[1]
    
    chat_id = CallbackQuery.message.chat.id
    
    # Store selected mood temporarily
    if chat_id not in lyrical:
        lyrical[chat_id] = {}
    lyrical[chat_id]["autoplay_mood"] = mood
    
    buttons = autoplay_language_markup(_)
    await CallbackQuery.edit_message_text(
        f"🎵 **Mood Selected: {mood}**\n\n"
        "Now select your preferred language:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@app.on_callback_query(filters.regex("songconfig_language"))
@languageCB
async def handle_language_selection(client, CallbackQuery, _):
    """Handle language selection callback"""
    callback_data = CallbackQuery.data.strip()
    language = callback_data.split(None, 1)[1]
    
    chat_id = CallbackQuery.message.chat.id
    
    # Get the mood that was selected
    if chat_id not in lyrical:
        lyrical[chat_id] = {}
    
    mood = lyrical[chat_id].get("autoplay_mood", "Chill")
    
    # Save configuration
    await set_autoplay(chat_id, True)
    await set_autoplay_mood(chat_id, {"mood": mood, "language": language})
    
    await CallbackQuery.edit_message_text(
        f"✅ **Autoplay Enabled!**\n\n"
        f"🎵 Mood: {mood}\n"
        f"🌐 Language: {language}\n\n"
        "Bot will now play songs based on previous tracks in this mood and language.",
    )


@app.on_callback_query(filters.regex("AutoPlay"))
@languageCB
async def toggle_autoplay(client, CallbackQuery, _):
    """Toggle autoplay on/off"""
    callback_data = CallbackQuery.data.strip()
    chat_id = int(callback_data.split("|")[1])
    
    # Check if autoplay is already enabled
    autoplay_status = await is_autoplay_on(chat_id)
    
    if autoplay_status:
        await set_autoplay(chat_id, False)
        await CallbackQuery.answer("🎲 AutoPlay has been disabled", show_alert=True)
    else:
        # Show mood selection
        buttons = autoplay_mood_markup(_)
        await CallbackQuery.edit_message_text(
            "🎵 **Enable Autoplay**\n\n"
            "Select your preferred mood:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


async def get_autoplay_recommendation(chat_id: int, user_id: int):
    """Get autoplay song recommendation based on previous tracks and mood"""
    
    if chat_id not in previous_tracks:
        previous_tracks[chat_id] = []
    
    # Get autoplay mood settings
    mood_data = await get_autoplay_mood(chat_id)
    mood = mood_data.get("mood", "Chill") if mood_data else "Chill"
    language = mood_data.get("language", "English") if mood_data else "English"
    
    # Build search query based on mood and language
    query = f"{mood} songs {language}"
    
    try:
        # Search for similar track
        track_data, track_id = await YouTube.track(query)
        
        # Store this track in previous tracks
        if len(previous_tracks[chat_id]) > 10:
            previous_tracks[chat_id].pop(0)
        
        previous_tracks[chat_id].append({
            "title": track_data.get("title"),
            "vidid": track_id,
            "mood": mood,
        })
        
        return track_data, track_id
    except:
        return None, None