from telethon import events
from telethon.tl.functions.contacts import BlockRequest
import json
import os
import time

WELCOME = (
    "Hi I am Cipher Ai, Master's Assistant.\n"
    "Please wait for approval.\n"
    "Type 'ok' to acknowledge."
)

OK_REPLY = (
    "👍 Acknowledged.\n"
    "Please wait for approval."
)

WARN_MSG = (
    "⚠️ Warning {}/5\n"
    "Please wait for approval before messaging again."
)

MAX_MSG = 5

WELCOME_PIC = "https://i.ibb.co/WvNhxBzG/photo-2026-01-13-08-02-26-7623444305934751744.jpg"


class PMGuard:

    def __init__(self, client, owner_id):

        self.client = client
        self.owner_id = owner_id

        self.msg_count = {}
        self.ok_seen = {}

        self.db_file = f"database/approved_{owner_id}.json"

        self.approved_users = self.load_approved()

    def load_approved(self):

        if not os.path.exists(self.db_file):
            return {}

        with open(self.db_file, "r") as f:
            return json.load(f)

    def save_approved(self):

        with open(self.db_file, "w") as f:
            json.dump(self.approved_users, f)

    def is_approved(self, uid):

        uid = str(uid)

        if uid not in self.approved_users:
            return False

        expiry = self.approved_users[uid]

        if expiry == "permanent":
            return True

        if time.time() < expiry:
            return True

        del self.approved_users[uid]
        self.save_approved()

        return False

    def load(self):

        @self.client.on(events.NewMessage(incoming=True))
        async def incoming_handler(event):

            if not event.is_private:
                return

            user = await event.get_sender()

            uid = user.id
            text = event.raw_text.lower().strip()

            if self.is_approved(uid):
                return

            if uid not in self.msg_count:

                self.msg_count[uid] = 0
                self.ok_seen[uid] = False

                try:
                    await event.reply(
                        file=WELCOME_PIC,
                        message=WELCOME
                    )
                except:
                    await event.reply(WELCOME)

                return

            if text == "ok" and not self.ok_seen.get(uid, False):

                self.ok_seen[uid] = True

                await event.reply(OK_REPLY)

                return

            if not self.ok_seen.get(uid, False):
                return

            count = self.msg_count.get(uid, 0) + 1

            self.msg_count[uid] = count

            if count <= MAX_MSG:

                await event.reply(WARN_MSG.format(count))

                return

            try:
                await self.client(BlockRequest(uid))
            except:
                pass

        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.a$'))
        async def approve_handler(event):

            if not event.is_private:
                return

            uid = event.chat_id

            self.approved_users[str(uid)] = "permanent"

            self.save_approved()

            self.msg_count.pop(uid, None)
            self.ok_seen.pop(uid, None)

            await event.reply("✅ Approved permanently")

        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.disapp$'))
        async def disapprove_handler(event):

            if not event.is_private:
                return

            uid = event.chat_id

            self.approved_users.pop(str(uid), None)

            self.save_approved()

            self.msg_count.pop(uid, None)
            self.ok_seen.pop(uid, None)

            await event.reply("❌ User disapproved")
