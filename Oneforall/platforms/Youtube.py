import aiohttp
import re
from py_yt import VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

API_URL = "http://45.77.174.241:9090"


class YouTubeAPI:

    def __init__(self):
        self.api = API_URL
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def search(self, query: str, limit: int = 1):
        try:
            results = VideosSearch(query, limit=limit)
            data = await results.next()
            return data.get("result", [])
        except Exception:
            return []

    async def get_video_id(self, query: str):
        results = await self.search(query)
        if not results:
            return None
        try:
            return results[0]["id"]
        except Exception:
            return None

    async def get_audio(self, video_id: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api}/download",
                    params={"url": video_id, "type": "audio"}
                ) as res:
                    if res.status != 200:
                        return None, None
                    data = await res.json()
                    token = data.get("download_token")
                    if not token:
                        return None, None
                    return f"{self.api}/stream/{video_id}?type=audio", token
        except Exception:
            return None, None

    async def get_video(self, video_id: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api}/download",
                    params={"url": video_id, "type": "video"}
                ) as res:
                    if res.status != 200:
                        return None, None
                    data = await res.json()
                    token = data.get("download_token")
                    if not token:
                        return None, None
                    return f"{self.api}/stream/{video_id}?type=video", token
        except Exception:
            return None, None

    async def url(self, message: Message):
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

    async def exists(self, link: str, videoid: bool = None):
        return bool(re.search(self.regex, link))

    async def title(self, link: str, videoid: bool = None):
        results = VideosSearch(link, limit=1)
        data = await results.next()
        return data["result"][0]["title"]

    async def duration(self, link: str, videoid: bool = None):
        results = VideosSearch(link, limit=1)
        data = await results.next()
        return data["result"][0]["duration"]

    async def thumbnail(self, link: str, videoid: bool = None):
        results = VideosSearch(link, limit=1)
        data = await results.next()
        return data["result"][0]["thumbnails"][0]["url"].split("?")[0]

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

print("QUERY:", query)
print("RESULT:", results)
