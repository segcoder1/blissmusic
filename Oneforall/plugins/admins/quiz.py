
import random
import requests
import asyncio
import html
from pyrogram import filters
from pyrogram.enums import PollType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Oneforall import app  # Replace with your actual import

quiz_loops = {}
active_polls = {}


# Fetch quiz question
async def fetch_quiz_question():
    categories = [9, 17, 18, 20, 21, 27]

    url = (
        f"https://opentdb.com/api.php?"
        f"amount=1&category={random.choice(categories)}&type=multiple"
    )

    try:
        response = requests.get(url)
        data = response.json()

        question_data = data["results"][0]

        question = html.unescape(question_data["question"])

        correct = html.unescape(question_data["correct_answer"])

        incorrect = [
            html.unescape(i)
            for i in question_data["incorrect_answers"]
        ]

        options = incorrect + [correct]
        random.shuffle(options)

        cid = options.index(correct)

        return question, options, cid

    except Exception as e:
        print(e)
        return None, None, None


# Send quiz poll
async def send_quiz_poll(client, chat_id, user_id, duration):
    question, options, cid = await fetch_quiz_question()

    if not question:
        return

    # Delete previous poll
    if user_id in active_polls:
        try:
            await app.delete_messages(
                chat_id,
                active_polls[user_id]
            )
        except:
            pass

    poll = await app.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        type=PollType.QUIZ,
        is_anonymous=False,
        correct_option_id=cid,
        open_period=duration
    )

    if poll:
        active_polls[user_id] = poll.id


# /quiz command
@app.on_message(
    filters.command(
        ["quiz", "uiz"],
        prefixes=["/", ".", "!", "Q", "q"]
    )
)
async def quiz_help(client, message):

    PHOTO_URL = "https://files.catbox.moe/m3dv8i.jpg"

    await message.reply_photo(
        photo=PHOTO_URL,

        caption=(
            "🌟 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ Qᴜɪᴢ Sʏsᴛᴇᴍ!** 🎯📚\n\n"

            "🛠️ **ʜᴏᴡ ᴛᴏ ᴜsᴇ:**\n"
            "1️⃣ ᴛʏᴘᴇ `/quizon` ✨\n"
            "2️⃣ ᴄʜᴏᴏsᴇ ᴀ ᴛɪᴍᴇ ɪɴᴛᴇʀᴠᴀʟ ⏳\n"
            "3️⃣ ǫᴜɪᴢ ᴡɪʟʟ sᴛᴀʀᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ 🚀\n"
            "4️⃣ ᴜsᴇ `/quizoff` 🛑 ᴛᴏ sᴛᴏᴘ\n\n"

            "📌 **ᴄᴏᴍᴍᴀɴᴅs:**\n"
            "▶️ `/quizon` — sᴛᴀʀᴛ ǫᴜɪᴢ ʟᴏᴏᴘ 🔄\n"
            "⏹️ `/quizoff` — sᴛᴏᴘ ǫᴜɪᴢ ❌"
        )
    )


# /quizon command
@app.on_message(
    filters.command(
        ["quizon", "uizon"],
        prefixes=["/", ".", "!", "Q", "q"]
    )
)
async def quizon_start(client, message):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "30s",
                    callback_data="30_sec"
                ),

                InlineKeyboardButton(
                    "1min",
                    callback_data="1_min"
                )
            ],

            [
                InlineKeyboardButton(
                    "5min",
                    callback_data="5_min"
                ),

                InlineKeyboardButton(
                    "10min",
                    callback_data="10_min"
                )
            ]
        ]
    )

    await message.reply_text(
        "**Choose a quiz interval to begin:**",
        reply_markup=keyboard
    )


# Callback query
@app.on_callback_query(
    filters.regex(r"^\d+_sec$|^\d+_min$")
)
async def interval_selected(client, query):

    user_id = query.from_user.id
    chat_id = query.message.chat.id

    if quiz_loops.get(user_id):
        await query.answer(
            "Quiz is already running!",
            show_alert=True
        )
        return

    interval_map = {
        "30_sec": (30, "30 seconds"),
        "1_min": (60, "1 minute"),
        "5_min": (300, "5 minutes"),
        "10_min": (600, "10 minutes")
    }

    interval, label = interval_map.get(
        query.data,
        (60, "1 minute")
    )

    await query.answer(
        "Quiz loop started!",
        show_alert=True
    )

    await query.message.delete()

    await query.message.reply_text(
        f"✅ Quiz started!\n"
        f"📚 New quiz every {label}."
    )

    quiz_loops[user_id] = True

    while quiz_loops.get(user_id):

        await send_quiz_poll(
            client,
            chat_id,
            user_id,
            duration=interval
        )

        for _ in range(interval):

            if not quiz_loops.get(user_id):
                return

            await asyncio.sleep(1)


# /quizoff command
@app.on_message(
    filters.command(
        ["quizoff", "uizoff"],
        prefixes=["/", ".", "!", "Q", "q"]
    )
)
async def quiz_stop(client, message):

    user_id = message.from_user.id

    if not quiz_loops.get(user_id):

        await message.reply_text(
            "❌ No quiz is running."
        )
        return

    quiz_loops.pop(user_id)

    await message.reply_text(
        "🛑 Quiz loop stopped."
    )

    # Delete active poll
    if user_id in active_polls:

        try:
            await app.delete_messages(
                message.chat.id,
                active_polls[user_id]
            )

            active_polls.pop(user_id)

        except:
            pass


# MADE BY NOBITA ONLY FOR AKSHIT 😊
```
