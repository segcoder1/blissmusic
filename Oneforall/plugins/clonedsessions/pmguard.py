from pyrogram import filters
import json
import os
import time

WELCOME = (
    "Hi I am Cipher Ai, Master's Assistant.\n"
    "Please wait for approval.\n"
    "Type 'ok' to acknowledge."
)

OK_REPLY = "👍 Acknowledged.\nPlease wait for approval."

WARN_MSG = "⚠️ Warning {}/5\nPlease wait for approval."

MAX_MSG = 5

WELCOME_PIC = "https://i.ibb.co/WvNhxBzG/photo.jpg"


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

        app = self.client

        @app.on_message(filters.private & filters.incoming)
        async def handler(client, message):

            uid = message.from_user.id
            text = (message.text or "").lower().strip()

            if self.is_approved(uid):
                return

            if uid not in self.msg_count:

                self.msg_count[uid] = 0
                self.ok_seen[uid] = False

                try:
                    await message.reply_photo(
                        WELCOME_PIC,
                        caption=WELCOME
                    )
                except:
                    await message.reply_text(WELCOME)

                return

            if text == "ok" and not self.ok_seen.get(uid):

                self.ok_seen[uid] = True
                await message.reply_text(OK_REPLY)
                return

            if not self.ok_seen.get(uid):
                return

            self.msg_count[uid] += 1

            if self.msg_count[uid] <= MAX_MSG:
                await message.reply_text(WARN_MSG.format(self.msg_count[uid]))
                return

            try:
                await app.block_user(uid)
            except:
                pass

        @app.on_message(filters.private & filters.outgoing & filters.regex(r"^\.a$"))
        async def approve(client, message):

            uid = message.chat.id

            self.approved_users[str(uid)] = "permanent"
            self.save_approved()

            self.msg_count.pop(uid, None)
            self.ok_seen.pop(uid, None)

            await message.reply("✅ Approved permanently")

        @app.on_message(filters.private & filters.outgoing & filters.regex(r"^\.disapp$"))
        async def disapprove(client, message):

            uid = message.chat.id

            self.approved_users.pop(str(uid), None)
            self.save_approved()

            self.msg_count.pop(uid, None)
            self.ok_seen.pop(uid, None)

            await message.reply("❌ User disapproved")
