import aiohttp
from py_yt import VideosSearch
from typing import Optional

API_URL = "http://45.77.174.241:9090"


class YouTubeAPI:

    def __init__(self):
        self.api = API_URL

    async def search(self, query: str, limit: int = 1):
        try:
            results = VideosSearch(query, limit=limit)
            data = await results.next()
            if not data or "result" not in data:
                return None
            return data["result"]
        except Exception:
            return None

    async def get_video_id(self, query: str) -> Optional[str]:
        results = await self.search(query)
        if not results:
            return None
        try:
            return results[0]["id"]
        except Exception:
            return None

    async def get_audio(self, video_id: str):
        if not video_id:
            return None, None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api}/download",
                    params={"url": video_id, "type": "audio"},
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as res:
                    if res.status != 200:
                        return None, None
                    data = await res.json()
                    token = data.get("download_token")
                    if not token:
                        return None, None
                    stream_url = f"{self.api}/stream/{video_id}?type=audio"
                    return stream_url, token
        except Exception:
            return None, None

    async def get_video(self, video_id: str):
        if not video_id:
            return None, None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api}/download",
                    params={"url": video_id, "type": "video"},
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as res:
                    if res.status != 200:
                        return None, None
                    data = await res.json()
                    token = data.get("download_token")
                    if not token:
                        return None, None
                    stream_url = f"{self.api}/stream/{video_id}?type=video"
                    return stream_url, token
        except Exception:
            return None, None

    async def play_audio(self, query: str):
        video_id = await self.get_video_id(query)
        if not video_id:
            return None, None
        return await self.get_audio(video_id)

    async def play_video(self, query: str):
        video_id = await self.get_video_id(query)
        if not video_id:
            return None, None
        return await self.get_video(video_id)

    async def url(self, message):
    from pyrogram.enums import MessageEntityType

    messages = [message]
    if message.reply_to_message:
        messages.append(message.reply_to_message)

    for msg in messages:
        if msg.entities:
            for entity in msg.entities:
                if entity.type == MessageEntityType.URL:
                    text = msg.text or msg.caption
                    return text[entity.offset: entity.offset + entity.length]

        if msg.caption_entities:
            for entity in msg.caption_entities:
                if entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url

    return None
