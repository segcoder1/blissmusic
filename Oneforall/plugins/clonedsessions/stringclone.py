from pyrogram import filters
from Oneforall.plugins.clonedsessions.sessionmanager import start_session
from Oneforall import app

WAITING_FOR_SESSION = set()


@app.on_message(filters.private & filters.command("stringclone"))
async def arm_session(client, message):

    user_id = message.from_user.id

    WAITING_FOR_SESSION.add(user_id)

    await message.reply_text(
        "📩 Now send your session string directly."
    )


@app.on_message(filters.private & filters.text)
async def receive_session(client, message):

    user_id = message.from_user.id
    text = message.text

    # ignore commands
    if text.startswith("/"):
        return

    # only accept if user is in session mode
    if user_id not in WAITING_FOR_SESSION:
        return

    WAITING_FOR_SESSION.remove(user_id)

    msg = await message.reply_text("⏳ Starting session...")

    ok, response = await start_session(user_id, text.strip())

    await msg.edit_text(response)
