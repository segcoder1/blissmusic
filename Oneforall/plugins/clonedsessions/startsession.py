from pyrogram import filters
from Oneforall.plugins.clonedsessions.sessionmanager import start_session
from Oneforall import app

WAITING_FOR_SESSION = set()


@app.on_message(filters.private & filters.command("stringclone"))
async def stringclone_cmd(client, message):

    user_id = message.from_user.id

    WAITING_FOR_SESSION.add(user_id)

    await message.reply_text(
        "Send your Telethon/Pyrogram string session."
    )


@app.on_message(filters.private & filters.text)
async def receive_session(client, message):

    user_id = message.from_user.id

    if user_id not in WAITING_FOR_SESSION:
        return

    if not message.text:
        return

    if message.text.startswith("/"):
        return

    session_string = message.text.strip()

    WAITING_FOR_SESSION.remove(user_id)

    msg = await message.reply_text("Starting PMGuard...")

    try:

        ok, response = await start_session(
            user_id,
            session_string
        )

        await msg.edit_text(response)

    except Exception as e:

        await msg.edit_text(f"❌ Error:\n{e}")

        WAITING_FOR_SESSION.add(user_id)
