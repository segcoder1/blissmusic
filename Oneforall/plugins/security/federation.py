import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from Oneforall import app
from Oneforall.misc import SUDOERS, ADMINS
from Oneforall.utils import get_readable_time
from Oneforall.utils.database import (
    add_federation,
    get_federation,
    get_federations,
    remove_federation,
    add_fed_admin,
    remove_fed_admin,
    get_fed_admins,
    add_fed_ban,
    remove_fed_ban,
    get_fed_bans,
    is_fed_banned,
    add_fed_chat,
    remove_fed_chat,
    get_fed_chats,
    transfer_federation,
    add_fed_sub,
    remove_fed_sub,
    get_fed_subs,
)
from Oneforall.utils.decorators.language import language
from Oneforall.utils.extraction import extract_user
from config import FEDERATION_STORAGE_ID, SUPPORT_CHAT


# ─────────────────────────────
# FEDERATION HELPERS
# ─────────────────────────────
def federation_admin_or_owner(func):
    """Decorator to check if user is federation admin or owner"""
    async def wrapper(client, message: Message, fed_id: str, _):
        federation = await get_federation(fed_id)
        if not federation:
            return await message.reply_text(_["fed_1"])
        
        if message.from_user.id != federation["owner"] and message.from_user.id not in federation.get("admins", []):
            return await message.reply_text(_["fed_2"])
        
        return await func(client, message, fed_id, federation, _)
    return wrapper


# ─────────────────────────────
# CREATE FEDERATION
# ─────────────────────────────
@app.on_message(filters.command(["newfed", "fnew"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def create_federation(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["fed_3"])
    
    fed_name = " ".join(message.command[1:])
    fed_id = f"{message.from_user.id}_{message.chat.id}"
    
    federation = {
        "fed_id": fed_id,
        "name": fed_name,
        "owner": message.from_user.id,
        "admins": [],
        "bans": {},
        "chats": [],
        "subscribed_feds": [],
        "log_channel": None,
    }
    
    await add_federation(federation)
    
    await message.reply_text(
        _["fed_4"].format(
            message.from_user.mention,
            fed_name,
            fed_id,
        )
    )


# ─────────────────────────────
# FEDERATION INFO
# ─────────────────────────────
@app.on_message(filters.command(["fedinfo", "finfo"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def federation_info(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(_["fed_5"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    if not fed_id and message.reply_to_message:
        fed_id = message.reply_to_message.text.split()[0]
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    info_text = _["fed_6"].format(
        federation["name"],
        fed_id,
        federation["owner"],
        len(federation["admins"]),
        len(federation["bans"]),
        len(federation["chats"]),
    )
    
    await message.reply_text(info_text)


# ─────────────────────────────
# FEDERATION BAN
# ─────────────────────────────
@app.on_message(filters.command(["fban", "sfban"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def federation_ban(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 3:
        return await message.reply_text(_["fed_7"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    user = await extract_user(message)
    reason = " ".join(message.command[3:]) if len(message.command) > 3 else "No reason provided"
    
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"] and message.from_user.id not in federation.get("admins", []):
        return await message.reply_text(_["fed_2"])
    
    if await is_fed_banned(fed_id, user.id):
        return await message.reply_text(_["fed_8"].format(user.mention))
    
    served_chats = federation["chats"]
    time_expected = get_readable_time(len(served_chats))
    
    mystic = await message.reply_text(_["fed_9"].format(user.mention, fed_id, time_expected))
    
    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
    
    await add_fed_ban(fed_id, user.id, reason)
    
    await message.reply_text(
        _["fed_10"].format(
            user.mention,
            user.id,
            fed_id,
            reason,
            number_of_chats,
        )
    )
    
    # Send log
    try:
        if federation.get("log_channel"):
            await app.send_message(
                federation["log_channel"],
                _["fed_11"].format(
                    message.from_user.mention,
                    user.mention,
                    user.id,
                    fed_id,
                    reason,
                ),
            )
    except:
        pass
    
    await mystic.delete()


# ─────────────────────────────
# FEDERATION UNBAN
# ─────────────────────────────
@app.on_message(filters.command(["unfban", "funban"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def federation_unban(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 3:
        return await message.reply_text(_["fed_12"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    user = await extract_user(message)
    
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"] and message.from_user.id not in federation.get("admins", []):
        return await message.reply_text(_["fed_2"])
    
    if not await is_fed_banned(fed_id, user.id):
        return await message.reply_text(_["fed_13"].format(user.mention))
    
    served_chats = federation["chats"]
    time_expected = get_readable_time(len(served_chats))
    
    mystic = await message.reply_text(_["fed_14"].format(user.mention, fed_id, time_expected))
    
    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
    
    await remove_fed_ban(fed_id, user.id)
    
    await message.reply_text(
        _["fed_15"].format(user.mention, fed_id, number_of_chats)
    )
    
    await mystic.delete()


# ─────────────────────────────
# FEDERATION BAN LIST
# ─────────────────────────────
@app.on_message(filters.command(["fbanlist", "exportfbans", "fexport"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def federation_ban_list(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(_["fed_16"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    bans = await get_fed_bans(fed_id)
    if not bans:
        return await message.reply_text(_["fed_17"])
    
    mystic = await message.reply_text(_["fed_18"])
    msg = _["fed_19"].format(federation["name"], fed_id)
    count = 0
    
    for ban in bans:
        count += 1
        try:
            user = await app.get_users(ban["user_id"])
            user_name = user.mention if user.mention else user.first_name
            msg += f"{count}. {user_name} - {ban.get('reason', 'No reason')}\n"
        except:
            msg += f"{count}. {ban['user_id']} - {ban.get('reason', 'No reason')}\n"
    
    await mystic.edit_text(msg)


# ─────────────────────────────
# FEDERATION CHECK BAN
# ─────────────────────────────
@app.on_message(filters.command(["fcheck", "fbanstat"], prefixes=["/", "!", "."]))
@language
async def federation_check_ban(client, message: Message, _):
    if message.chat.type == "private":
        if len(message.command) < 2:
            return await message.reply_text(_["fed_20"])
        user_id = int(message.command[1]) if message.command[1].isdigit() else None
        show_all = "full" in message.command
    else:
        if not message.reply_to_message and len(message.command) < 2:
            return await message.reply_text(_["fed_21"])
        
        if len(message.command) > 1:
            fed_id = message.command[1]
            user = await extract_user(message)
            user_id = user.id
        else:
            return await message.reply_text(_["fed_22"])
        show_all = False
    
    if not user_id:
        return await message.reply_text(_["fed_23"])
    
    federations = await get_federations()
    banned_in = []
    
    for federation in federations:
        if await is_fed_banned(federation["fed_id"], user_id):
            banned_in.append(federation)
    
    if not banned_in:
        return await message.reply_text(_["fed_24"])
    
    msg = _["fed_25"]
    for fed in banned_in:
        msg += f"\n• {fed['name']} ({fed['fed_id']})"
    
    await message.reply_text(msg)


# ─────────────────────────────
# TRANSFER FEDERATION OWNERSHIP
# ─────────────────────────────
@app.on_message(filters.command(["transferfed", "ftransfer"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def transfer_federation_ownership(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 3:
        return await message.reply_text(_["fed_26"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    new_owner = await extract_user(message)
    
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    await transfer_federation(fed_id, new_owner.id)
    await message.reply_text(
        _["fed_28"].format(federation["name"], new_owner.mention)
    )


# ─────────────────────────────
# PROMOTE FEDERATION ADMIN
# ─────────────────────────────
@app.on_message(filters.command(["fpromote"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def promote_fed_admin(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 3:
        return await message.reply_text(_["fed_29"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    user = await extract_user(message)
    
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    if user.id in federation.get("admins", []):
        return await message.reply_text(_["fed_30"].format(user.mention))
    
    await add_fed_admin(fed_id, user.id)
    await message.reply_text(
        _["fed_31"].format(user.mention, federation["name"])
    )


# ─────────────────────────────
# DEMOTE FEDERATION ADMIN
# ─────────────────────────────
@app.on_message(filters.command(["fdemote"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def demote_fed_admin(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 3:
        return await message.reply_text(_["fed_32"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    user = await extract_user(message)
    
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    if user.id not in federation.get("admins", []):
        return await message.reply_text(_["fed_33"].format(user.mention))
    
    await remove_fed_admin(fed_id, user.id)
    await message.reply_text(
        _["fed_34"].format(user.mention, federation["name"])
    )


# ─────────────────────────────
# LIST FEDERATION ADMINS
# ─────────────────────────────
@app.on_message(filters.command(["fadmins", "fedadmins"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def federation_admins(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(_["fed_35"])
    
    fed_id = message.command[1] if len(message.command) > 1 else None
    if not fed_id:
        return await message.reply_text(_["fed_5"])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    msg = _["fed_36"].format(federation["name"], fed_id)
    msg += f"\n👑 Owner: {federation['owner']}\n"
    
    if federation.get("admins"):
        msg += "\n🔱 Admins:\n"
        for admin_id in federation["admins"]:
            try:
                admin = await app.get_users(admin_id)
                msg += f"• {admin.mention}\n"
            except:
                msg += f"• {admin_id}\n"
    else:
        msg += "\nNo admins in this federation.\n"
    
    await message.reply_text(msg)


# ─────────────────────────────
# JOIN FEDERATION (ADMIN ONLY)
# ─────────────────────────────
@app.on_message(filters.command(["joinfed", "fjoin"], prefixes=["/", "!", "."]))
@language
async def join_federation(client, message: Message, _):
    if not message.chat.type.name == "supergroup":
        return await message.reply_text(_["fed_37"])
    
    if len(message.command) < 2:
        return await message.reply_text(_["fed_38"])
    
    fed_id = message.command[1]
    federation = await get_federation(fed_id)
    
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    # Check if user is admin
    member = await app.get_chat_member(message.chat.id, message.from_user.id)
    if not member.status.name in ["administrator", "creator"]:
        return await message.reply_text(_["fed_39"])
    
    if message.chat.id in federation["chats"]:
        return await message.reply_text(_["fed_40"])
    
    await add_fed_chat(fed_id, message.chat.id)
    await message.reply_text(
        _["fed_41"].format(message.chat.title, federation["name"])
    )


# ─────────────────────────────
# LEAVE FEDERATION (ADMIN ONLY)
# ─────────────────────────────
@app.on_message(filters.command(["leavefed", "fleave"], prefixes=["/", "!", "."]))
@language
async def leave_federation(client, message: Message, _):
    if not message.chat.type.name == "supergroup":
        return await message.reply_text(_["fed_37"])
    
    # Check if user is admin
    member = await app.get_chat_member(message.chat.id, message.from_user.id)
    if not member.status.name in ["administrator", "creator"]:
        return await message.reply_text(_["fed_39"])
    
    federations = await get_federations()
    chat_fed = None
    
    for fed in federations:
        if message.chat.id in fed["chats"]:
            chat_fed = fed
            break
    
    if not chat_fed:
        return await message.reply_text(_["fed_42"])
    
    await remove_fed_chat(chat_fed["fed_id"], message.chat.id)
    await message.reply_text(
        _["fed_43"].format(message.chat.title, chat_fed["name"])
    )


# ─────────────────────────────
# FEDERATION SUBSCRIBE
# ─────────────────────────────
@app.on_message(filters.command(["fsub"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def subscribe_federation(client, message: Message, _):
    if len(message.command) < 3:
        return await message.reply_text(_["fed_44"])
    
    fed_id = message.command[1]
    sub_fed_id = message.command[2]
    
    federation = await get_federation(fed_id)
    sub_federation = await get_federation(sub_fed_id)
    
    if not federation or not sub_federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    if sub_fed_id in federation.get("subscribed_feds", []):
        return await message.reply_text(_["fed_45"])
    
    await add_fed_sub(fed_id, sub_fed_id)
    await message.reply_text(
        _["fed_46"].format(federation["name"], sub_federation["name"])
    )


# ─────────────────────────────
# FEDERATION UNSUBSCRIBE
# ─────────────────────────────
@app.on_message(filters.command(["funsub"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def unsubscribe_federation(client, message: Message, _):
    if len(message.command) < 3:
        return await message.reply_text(_["fed_47"])
    
    fed_id = message.command[1]
    sub_fed_id = message.command[2]
    
    federation = await get_federation(fed_id)
    
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    if sub_fed_id not in federation.get("subscribed_feds", []):
        return await message.reply_text(_["fed_48"])
    
    await remove_fed_sub(fed_id, sub_fed_id)
    await message.reply_text(
        _["fed_49"].format(fed_id, sub_fed_id)
    )


# ─────────────────────────────
# LIST FEDERATION CHATS
# ─────────────────────────────
@app.on_message(filters.command(["fchats"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def list_federation_chats(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["fed_50"])
    
    fed_id = message.command[1]
    federation = await get_federation(fed_id)
    
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    chats = federation.get("chats", [])
    if not chats:
        return await message.reply_text(_["fed_51"])
    
    msg = _["fed_52"].format(federation["name"], len(chats))
    
    for idx, chat_id in enumerate(chats, 1):
        try:
            chat = await app.get_chat(chat_id)
            msg += f"\n{idx}. {chat.title} ({chat_id})"
        except:
            msg += f"\n{idx}. {chat_id}"
    
    await message.reply_text(msg)


# ─────────────────────────────
# RENAME FEDERATION
# ─────────────────────────────
@app.on_message(filters.command(["frename"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def rename_federation(client, message: Message, _):
    if len(message.command) < 3:
        return await message.reply_text(_["fed_53"])
    
    fed_id = message.command[1]
    new_name = " ".join(message.command[2:])
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    old_name = federation["name"]
    federation["name"] = new_name
    await add_federation(federation)
    
    await message.reply_text(
        _["fed_54"].format(old_name, new_name)
    )


# ─────────────────────────────
# DELETE FEDERATION
# ─────────────────────────────
@app.on_message(filters.command(["fdelete"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def delete_federation(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["fed_55"])
    
    fed_id = message.command[1]
    federation = await get_federation(fed_id)
    
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"]:
        return await message.reply_text(_["fed_27"])
    
    await remove_federation(fed_id)
    await message.reply_text(
        _["fed_56"].format(federation["name"])
    )


# ─────────────────────────────
# SET FEDERATION LOG CHANNEL
# ─────────────────────────────
@app.on_message(filters.command(["fsetlog", "setfedlog"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def set_federation_log(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["fed_57"])
    
    fed_id = message.command[1]
    log_channel = message.command[2] if len(message.command) > 2 else message.chat.id
    
    federation = await get_federation(fed_id)
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"] and message.from_user.id not in federation.get("admins", []):
        return await message.reply_text(_["fed_2"])
    
    federation["log_channel"] = log_channel
    await add_federation(federation)
    
    await message.reply_text(
        _["fed_58"].format(federation["name"], log_channel)
    )


# ─────────────────────────────
# UNSET FEDERATION LOG CHANNEL
# ─────────────────────────────
@app.on_message(filters.command(["funsetlog", "unsetfedlog"], prefixes=["/", "!", "."]) & ADMINS)
@language
async def unset_federation_log(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["fed_59"])
    
    fed_id = message.command[1]
    federation = await get_federation(fed_id)
    
    if not federation:
        return await message.reply_text(_["fed_1"])
    
    if message.from_user.id != federation["owner"] and message.from_user.id not in federation.get("admins", []):
        return await message.reply_text(_["fed_2"])
    
    federation["log_channel"] = None
    await add_federation(federation)
    
    await message.reply_text(
        _["fed_60"].format(federation["name"])
    )
