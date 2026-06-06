import random
import asyncio
import time
from datetime import datetime

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

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
from Oneforall.utils.spotify_image import (
    create_spotify_thumbnail_with_yt_image,
    save_image_to_bytes,
    format_time,
)

# Store previous tracks per chat
previous_tracks = {}
# Store current playing track info per chat
current_autoplay_track = {}
# Store autoplay queues per chat
autoplay_queue = {}
# Store message IDs for progress bar updates
progress_messages = {}
# Track update tasks
update_tasks = {}
# Track start time for each song
track_start_times = {}

# Support group links
SUPPORT_GROUP = "https://t.me/theinfinitynetwork"
BUG_REPORT_GROUP = "https://t.me/theinfinity_support"


def get_action_buttons(chat_id):
    """Get action buttons with skip, queue, support and bug report"""
    
    buttons = [
        [
            InlineKeyboardButton(
                "⏭️ sᴋɪᴘ",
                callback_data="askip",
            ),
            InlineKeyboardButton(
                "📋 Qᴜᴇᴜᴇ",
                callback_data=f"aqueue|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "💬 sᴜᴘᴘᴏʀᴛ",
                url=SUPPORT_GROUP,
            ),
            InlineKeyboardButton(
                "🐛 ʙᴜɢ ʀᴇᴘᴏʀᴛ",
                url=BUG_REPORT_GROUP,
            ),
        ],
        [
            InlineKeyboardButton(
                "🌙 ᴄʟᴏsᴇ",
                callback_data="close",
            ),
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)


@app.on_message(filters.command("mconfig") & filters.group & ~BANNED_USERS)
@languageCB
async def songconfig_command(client, message, _):

    await message.reply_text(
        "<blockquote>🎵 **ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:</blockquote>",
        reply_markup=autoplay_mood_markup(),
    )


@app.on_callback_query(filters.regex(r"^songconfig_mood:"))
@languageCB
async def handle_mood_selection(client, CallbackQuery, _):

    chat_id = CallbackQuery.message.chat.id

    try:
        mood = CallbackQuery.data.split(":", 1)[1]
    except Exception:
        return await CallbackQuery.answer(
            "ɪɴᴠᴀʟɪᴅ ᴍᴏᴏᴅ sᴇʟᴇᴄᴛɪᴏɴ",
            show_alert=True,
        )

    if chat_id not in lyrical:
        lyrical[chat_id] = {}

    lyrical[chat_id]["autoplay_mood"] = mood

    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass

    await CallbackQuery.answer(
        f"🎵 ᴍᴏᴏᴅ: {mood.title()}",
        show_alert=False,
    )

    await CallbackQuery.message.reply_text(
        "<blockquote>🌐 **sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ʟᴀɴɢᴜᴀɢᴇ:**</blockquote>",
        reply_markup=autoplay_language_markup(),
    )


@app.on_callback_query(filters.regex(r"^songconfig_language:"))
@languageCB
async def handle_language_selection(client, CallbackQuery, _):

    chat_id = CallbackQuery.message.chat.id

    try:
        language = CallbackQuery.data.split(":", 1)[1]
    except Exception:
        return await CallbackQuery.answer(
            "ɪɴᴠᴀʟɪᴅ ʟᴀɴɢᴜᴀɢᴇ sᴇʟᴇᴄᴛɪᴏɴ",
            show_alert=True,
        )

    if chat_id not in lyrical:
        lyrical[chat_id] = {}

    mood = lyrical[chat_id].get("autoplay_mood", "chill")

    await set_autoplay(chat_id, True)

    await set_autoplay_mood(
        chat_id,
        {
            "mood": mood,
            "language": language,
        },
    )

    lyrical[chat_id].pop("autoplay_mood", None)

    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass

    await CallbackQuery.answer(
        f"✅ ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ\n🎵 {mood.title()}\n🌐 {language.title()}",
        show_alert=True,
    )

    await CallbackQuery.message.reply_text(
        "<blockquote>✅ **ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ**\n\n"
        f"🎵 ᴍᴏᴏᴅ: `{mood.title()}`\n"
        f"🌐 ʟᴀɴɢᴜᴀɢᴇ: `{language.title()}`</blockquote>"
    )


@app.on_callback_query(filters.regex(r"^AutoPlay"))
@languageCB
async def toggle_autoplay(client, CallbackQuery, _):

    callback_data = CallbackQuery.data.strip()

    try:
        chat_id = int(callback_data.split("|")[1])
    except Exception:
        return await CallbackQuery.answer(
            "ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ",
            show_alert=True,
        )

    autoplay_status = await is_autoplay_on(chat_id)

    if autoplay_status:
        await set_autoplay(chat_id, False)

        try:
            await CallbackQuery.message.edit_reply_markup(None)
        except:
            pass

        return await CallbackQuery.answer(
            "❌ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ",
            show_alert=True,
        )

    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass

    await CallbackQuery.answer()

    await CallbackQuery.message.reply_text(
        "<blockquote>🎵 **ᴇɴᴀʙʟᴇ ᴀᴜᴛᴏᴘʟᴀʏ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:</blockquote>",
        reply_markup=autoplay_mood_markup(),
    )


@app.on_message(filters.command("askip") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_skip_command(client, message, _):

    chat_id = message.chat.id

    await process_autoplay_skip(chat_id, message)


@app.on_callback_query(filters.regex("^askip$"))
@languageCB
async def autoplay_skip_callback(client, CallbackQuery, _):

    chat_id = CallbackQuery.message.chat.id

    await CallbackQuery.answer("⏭️ sᴋɪᴘᴘɪɴɢ...")

    await process_autoplay_skip(chat_id, CallbackQuery.message)


@app.on_message(filters.command("aseek") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_seek_command(client, message, _):
    """Seek to a specific time in the autoplay song"""
    
    chat_id = message.chat.id
    
    autoplay_status = await is_autoplay_on(chat_id)
    
    if not autoplay_status:
        return await message.reply_text(
            "<blockquote>❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**</blockquote>"
        )
    
    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) < 2:
            return await message.reply_text(
                "<blockquote>📍 **ᴜsᴀɢᴇ:** /aseek <minutes> <seconds>\n"
                "ᴇxᴀᴍᴘʟᴇ: /aseek 1 30</blockquote>"
            )
        
        try:
            minutes = int(cmd_parts[1])
            seconds = int(cmd_parts[2]) if len(cmd_parts) > 2 else 0
        except (ValueError, IndexError):
            return await message.reply_text(
                "<blockquote>❌ **ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ғᴏʀᴍᴀᴛ**\n"
                "ᴜsᴇ: /aseek <minutes> <seconds>\n"
                "ᴇxᴀᴍᴘʟᴇ: /aseek 1 30</blockquote>"
            )
        
        total_seconds = minutes * 60 + seconds
        
        from Oneforall.core.call import Hotty
        
        if chat_id in current_autoplay_track:
            await Hotty.seek_stream(chat_id, total_seconds)
            
            if chat_id in track_start_times:
                track_start_times[chat_id] = time.time() - total_seconds
            
            await message.reply_text(
                f"<blockquote>📍 **sᴇᴇᴋɪɴɢ ᴛᴏ:** {format_time(total_seconds)}</blockquote>"
            )
        else:
            await message.reply_text(
                "<blockquote>❌ **ɴᴏ sᴏɴɢ ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ**</blockquote>"
            )
    
    except Exception as e:
        print(f"Seek Error: {e}")
        await message.reply_text(
            "<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴇᴋ sᴏɴɢ**</blockquote>"
        )


@app.on_message(filters.command("aqueue") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_queue_command(client, message, _):
    """Show the autoplay queue"""
    
    chat_id = message.chat.id
    
    autoplay_status = await is_autoplay_on(chat_id)
    
    if not autoplay_status:
        return await message.reply_text(
            "<blockquote>❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**</blockquote>"
        )
    
    if chat_id not in previous_tracks or not previous_tracks[chat_id]:
        return await message.reply_text(
            "<blockquote>📭 **qᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ**</blockquote>"
        )
    
    queue_text = "<blockquote>📋 **ᴀᴜᴛᴏᴘʟᴀʏ qᴜᴇᴜᴇ**\n\n"
    
    if chat_id in current_autoplay_track:
        current = current_autoplay_track[chat_id]
        queue_text += f"▶️ **ɴᴏᴡ ᴘʟᴀʏɪɴɢ:**\n"
        queue_text += f"🎵 {current.get('title', 'Unknown')[:50]}\n"
        queue_text += f"🕐 {current.get('duration', 'Unknown')}\n\n"
    
    queue_text += f"**ᴜᴘᴄᴏᴍɪɴɢ ᴛʀᴀᴄᴋs ({len(previous_tracks[chat_id])}):**\n\n"
    
    for idx, track in enumerate(previous_tracks[chat_id][:10], 1):
        title = track.get("title", "Unknown")[:45]
        queue_text += f"{idx}. {title}\n"
    
    if len(previous_tracks[chat_id]) > 10:
        queue_text += f"\n... ᴀɴᴅ {len(previous_tracks[chat_id]) - 10} ᴍᴏʀᴇ\n"
    
    queue_text += "</blockquote>"
    
    await message.reply_text(queue_text)


@app.on_callback_query(filters.regex("^aqueue\\|"))
@languageCB
async def autoplay_queue_callback(client, CallbackQuery, _):
    """Show autoplay queue"""

    chat_id = int(CallbackQuery.data.split("|")[1])

    autoplay_status = await is_autoplay_on(chat_id)

    if not autoplay_status:
        return await CallbackQuery.answer(
            "❌ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ",
            show_alert=True,
        )

    if chat_id not in previous_tracks or not previous_tracks[chat_id]:
        return await CallbackQuery.answer(
            "📭 qᴜᴇᴜᴇ ᴇᴍᴘᴛʏ",
            show_alert=True,
        )

    queue_text = "📋 **ᴀᴜᴛᴏᴘʟᴀʏ qᴜᴇᴜᴇ**\n\n"

    if chat_id in current_autoplay_track:
        current = current_autoplay_track[chat_id]
        queue_text += (
            f"▶️ **ɴᴏᴡ ᴘʟᴀʏɪɴɢ**\n"
            f"{current.get('title', 'Unknown')[:60]}\n\n"
        )

    queue_text += "**ᴜᴘᴄᴏᴍɪɴɢ ᴛʀᴀᴄᴋs:**\n\n"

    shown = 0

    for idx, track in enumerate(previous_tracks[chat_id], start=1):

        title = track.get("title", "Unknown")

        if len(title) > 60:
            title = title[:57] + "..."

        line = f"`{idx}.` {title}\n"

        if len(queue_text + line) > 3500:
            remaining = len(previous_tracks[chat_id]) - shown

            if remaining > 0:
                queue_text += f"\n➕ **{remaining} ᴍᴏʀᴇ ᴛʀᴀᴄᴋs ɴᴏᴛ sʜᴏᴡɴ**"
            break

        queue_text += line
        shown += 1

    try:
        await CallbackQuery.message.edit_text(
            queue_text,
            disable_web_page_preview=True,
        )

        await CallbackQuery.answer()

    except Exception as e:
        print(f"Queue Error: {e}")

        await CallbackQuery.answer(
            "❌ ғᴀɪʟᴇᴅ ᴛᴏ sʜᴏᴡ qᴜᴇᴜᴇ",
            show_alert=True,
        )


# Global close button handler
@app.on_callback_query(filters.regex("^close$"))
async def close_button_handler(client, CallbackQuery):
    """Handle close button globally"""
    try:
        await CallbackQuery.answer()
        await CallbackQuery.message.delete()
    except Exception as e:
        print(f"Close button error: {e}")
        try:
            await CallbackQuery.answer("Unable to close message", show_alert=False)
        except:
            pass


async def process_autoplay_skip(chat_id, message):

    from Oneforall.core.call import Hotty

    autoplay_status = await is_autoplay_on(chat_id)

    if not autoplay_status:
        return await message.reply_text(
            "<blockquote>❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**</blockquote>"
        )

    try:
        track_data, track_id = await get_autoplay_recommendation(chat_id)

        if not track_data or not track_id:
            return await message.reply_text(
                "<blockquote>🦋 **ɴᴏ ɴᴇxᴛ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ ғᴏᴜɴᴅ**</blockquote>"
            )

        title = track_data.get("title", "Unknown")
        duration_str = track_data.get("duration", "Unknown")
        thumbnail_url = track_data.get("thumb", "")
        artist = track_data.get("artist", "")

        # Parse duration to seconds
        try:
            duration_parts = str(duration_str).split(":")
            if len(duration_parts) == 2:
                duration_sec = int(duration_parts[0]) * 60 + int(duration_parts[1])
            else:
                duration_sec = int(duration_parts[0])
        except:
            duration_sec = 0

        try:
            file_path, direct = await YouTube.download(
                track_id,
                None,
                videoid=True,
                video=False,
            )
            
            if not file_path:
                print(f"Download returned empty file_path for track_id: {track_id}")
                raise ValueError(f"Download failed: empty file_path for {track_id}")
                
        except Exception as e:
            print(f"Download Error: {e}")
            await message.reply_text(
                f"<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ sᴏɴɢ**: {str(e)[:50]}</blockquote>"
            )
            return

        if not file_path or file_path is None:
            return await message.reply_text(
                "<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ sᴏɴɢ**</blockquote>"
            )

        try:
            if not isinstance(file_path, (str, bytes)):
                file_path = str(file_path) if file_path else None
                if not file_path:
                    raise ValueError("Invalid file path for streaming")
            
            await Hotty.skip_stream(
                chat_id,
                file_path,
                video=False,
            )

        except Exception as e:
            print(f"Change Stream Error: {e}")
            return await message.reply_text(
                f"<blockquote>😭 **ғᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ sᴛʀᴇᴀᴍ**: {str(e)[:60]}</blockquote>"
            )

        try:
            # Get mood for Spotify thumbnail
            mood_data = await get_autoplay_mood(chat_id)
            mood = "chill"
            if isinstance(mood_data, dict):
                mood = mood_data.get("mood", "chill")
            
            # Generate Spotify-styled thumbnail with YouTube image
            spotify_img = create_spotify_thumbnail_with_yt_image(
                thumbnail_url,
                title,
                duration_str,
                0,
                duration_sec,
                mood,
                artist
            )
            
            if spotify_img:
                img_bytes = save_image_to_bytes(spotify_img)
                
                sent_message = await app.send_photo(
                    chat_id=chat_id,
                    photo=img_bytes,
                    caption=(
                        f"<blockquote>🎵 **{title}**\n"
                        f"🎤 {artist}\n"
                        f"⏱️ {duration_str}</blockquote>"
                    ),
                    reply_markup=get_action_buttons(chat_id),
                )
            else:
                # Fallback
                sent_message = await app.send_photo(
                    chat_id=chat_id,
                    photo=thumbnail_url if thumbnail_url else config.YOUTUBE_IMG_URL,
                    caption=(
                        f"<blockquote>🎵 **{title}**\n"
                        f"🎤 {artist}\n"
                        f"⏱️ {duration_str}</blockquote>"
                    ),
                    reply_markup=get_action_buttons(chat_id),
                )

            # Store current track info
            current_autoplay_track[chat_id] = {
                "title": title,
                "duration": duration_str,
                "duration_sec": duration_sec,
                "current_sec": 0,
                "vidid": track_id,
                "thumb": thumbnail_url,
            }
            
            progress_messages[chat_id] = sent_message.id
            
            # Cancel previous update task if exists
            if chat_id in update_tasks:
                try:
                    update_tasks[chat_id].cancel()
                except:
                    pass

        except Exception as e:
            print(f"Thumbnail Send Error: {e}")

    except Exception as e:
        print(f"Askip Error: {e}")

        return await message.reply_text(
            "<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ sᴋɪᴘ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ**</blockquote>"
        )


async def get_autoplay_recommendation(chat_id: int):
    """Get high-quality song recommendations with improved search quality"""

    if chat_id not in previous_tracks:
        previous_tracks[chat_id] = []

    mood_data = await get_autoplay_mood(chat_id)

    mood = "chill"
    language = "english"

    if isinstance(mood_data, dict):
        mood = mood_data.get("mood", "chill")
        language = mood_data.get("language", "english")

    used_ids = [x["vidid"] for x in previous_tracks[chat_id]]

    # ✅ IMPROVED: Better quality search keywords with artist preferences
    search_templates = {
        "english": {
            "chill": [
                "{} chill mix lofi hip hop 2024",
                "{} ambient relaxation sleep music official",
                "{} indie bedroom pop 2024",
                "{} lo-fi beats study focus 2024",
                "{} aesthetic chill vibes no copyright",
            ],
            "energetic": [
                "{} edm dance electronic 2024 official",
                "{} hip hop rap bass boost 2024",
                "{} upbeat pop summer hits 2024",
                "{} workout fitness motivation 2024",
                "{} party club bangers 2024",
            ],
            "romantic": [
                "{} romantic ballad love songs 2024 official",
                "{} slow music emotional soul 2024",
                "{} acoustic guitar love cover 2024",
                "{} indie love songs 2024",
                "{} r&b slow jams 2024",
            ],
            "classical": [
                "{} classical music piano concert",
                "{} orchestral instrumental composition",
                "{} violin solo masterpiece",
                "{} symphony classical relaxation",
                "{} mozart bach classical compilation",
            ],
        },
        "hindi": {
            "chill": [
                "{} bollywood chill lofi remix 2024",
                "{} hindi indie lo-fi beats 2024",
                "{} hindi sad songs emotional 2024",
                "{} acoustic hindi cover 2024",
                "{} hindi relaxation instrumental 2024",
            ],
            "energetic": [
                "{} hindi bollywood party songs 2024",
                "{} hindi rap hip hop 2024",
                "{} hindi dance remix 2024",
                "{} bollywood upbeat party hits",
                "{} hindi edm electronic dance 2024",
            ],
            "romantic": [
                "{} bollywood romantic songs 2024",
                "{} hindi love songs acoustic 2024",
                "{} hindi sad emotional love 2024",
                "{} bollywood couple songs 2024",
                "{} hindi romantic ballad 2024",
            ],
        },
    }

    # Popular artists to avoid generic results
    popular_artists = [
        "the weeknd", "billie eilish", "ariana grande", "dua lipa",
        "bad bunny", "lil baby", "drake", "olivia rodrigo",
        "taylor swift", "harry styles", "travis scott", "post malone",
        "arijit singh", "neha kakkar", "atif aslam", "rahat fateh ali khan",
    ]

    for attempt in range(20):
        try:
            # Get language-specific search keywords
            lang_searches = search_templates.get(language, search_templates["english"])
            mood_searches = lang_searches.get(mood, lang_searches["chill"])
            
            # Pick a random template and artist for variety
            template = random.choice(mood_searches)
            artist = random.choice(popular_artists) if attempt % 3 == 0 else ""
            
            query = template.format(artist) if artist else template
            
            # Add quality filters
            query += " -playlist -mix -covers -karaoke -instrumental -remix"
            
            track_data, track_id = await YouTube.track(query)

            if not track_data or not track_id:
                continue

            title = track_data.get("title", "").lower()
            duration = track_data.get("duration", "0:00")
            
            # Skip unwanted content
            skip_keywords = [
                "playlist", "mix", "compilation", "collection", "radio", "full album",
                "full movie", "trailer", "lyric video only", "bgm", "background",
                "cover band", "covers only", "guitar tutorial", "how to play"
            ]
            
            if any(keyword in title for keyword in skip_keywords):
                continue

            # Skip if already in queue
            if track_id in used_ids:
                continue

            # Duration validation (skip too short or too long)
            try:
                duration_parts = duration.split(":")
                if len(duration_parts) == 2:
                    dur_sec = int(duration_parts[0]) * 60 + int(duration_parts[1])
                else:
                    dur_sec = int(duration_parts[0])
                
                # Accept songs between 2 min and 12 min
                if dur_sec < 120 or dur_sec > 720:
                    continue
            except:
                pass

            # Maintain queue size
            if len(previous_tracks[chat_id]) >= 15:
                previous_tracks[chat_id].pop(0)

            previous_tracks[chat_id].append(
                {
                    "title": track_data.get("title"),
                    "vidid": track_id,
                    "mood": mood,
                    "language": language,
                }
            )

            print(f"✅ Found quality track: {track_data.get('title')}")
            return track_data, track_id

        except Exception as e:
            print(f"Autoplay search attempt {attempt + 1} error: {e}")
            await asyncio.sleep(0.5)
            continue

    print(f"❌ Failed to find quality autoplay recommendation after 20 attempts")
    return None, None
