# plugins/session_manager.py

from telethon import TelegramClient
from telethon.sessions import StringSession

from Oneforallplugins.clonedsessions.pmguard import PMGuard

API_ID = 123456
API_HASH = "your_api_hash"

active_clients = {}
active_pmguard = {}


async def start_session(user_id, session_string):

    if user_id in active_clients:
        return False, "Session already running"

    try:

        client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH
        )

        await client.start()

        me = await client.get_me()

        pmguard = PMGuard(client, user_id)
        pmguard.load()

        active_clients[user_id] = client
        active_pmguard[user_id] = pmguard

        return True, f"✅ PMGuard started on @{me.username}"

    except Exception as e:
        return False, f"❌ Failed:\n{e}"


async def stop_session(user_id):

    client = active_clients.get(user_id)

    if not client:
        return False, "No active session"

    try:

        await client.disconnect()

        del active_clients[user_id]
        del active_pmguard[user_id]

        return True, "🛑 Session stopped"

    except Exception as e:
        return False, f"❌ Error:\n{e}"
