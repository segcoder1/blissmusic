# Autoplay functions

async def set_autoplay(chat_id: int, status: bool):
    """Set autoplay status for a chat"""
    await autoplay_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )


async def is_autoplay_on(chat_id: int) -> bool:
    """Check if autoplay is enabled for a chat"""
    result = await autoplay_db.find_one({"chat_id": chat_id})
    return result.get("enabled", False) if result else False


async def set_autoplay_mood(chat_id: int, mood_data: dict):
    """Set autoplay mood preferences for a chat"""
    await autoplay_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"mood": mood_data.get("mood"), "language": mood_data.get("language")}},
        upsert=True
    )


async def get_autoplay_mood(chat_id: int) -> dict:
    """Get autoplay mood preferences for a chat"""
    result = await autoplay_db.find_one({"chat_id": chat_id})
    if result:
        return {"mood": result.get("mood"), "language": result.get("language")}
    return None