import aiohttp
import asyncio
import re
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from Oneforall.utils.formatters import time_to_seconds
from py_yt import VideosSearch
from Oneforall import LOGGER


API_URL = "http://45.77.174.241:9090"


class YouTubeAPI:

    def __init__(self):
        self.api = API_URL
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


    async def get_audio_stream(self, video_id: str):
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

                stream_url = f"{self.api}/stream/{video_id}?type=audio"
                return stream_url, token

    async def get_video_stream(self, video_id: str):
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

                stream_url = f"{self.api}/stream/{video_id}?type=video"
                return stream_url, token

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def search(self, query: str, limit: int = 10):
        results = VideosSearch(query, limit=limit)
        return (await results.next())["result"]

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def track(self, link: str):
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0],
            }, result["id"]

    async def download(self, link: str, video: bool = False):
        video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

        try:
            if video:
                return await self.get_video_stream(video_id)
            else:
                return await self.get_audio_stream(video_id)
        except Exception:
            return None, None

    async def video(self, *args, **kwargs):
        return None, "Use API stream instead"

    async def formats(self, *args, **kwargs):
        return [], None

    async def slider(self, *args, **kwargs):
        return None
