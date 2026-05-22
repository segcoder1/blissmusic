import asyncio
import os
import re
from typing import Union

import yt_dlp
import aiohttp

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch
from Oneforall.utils.formatters import time_to_seconds
from Oneforall import LOGGER


# =========================
# API CONFIG
# =========================

YOUR_API_URL = None
FALLBACK_API_URL = "http://45.77.174.241:3000"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YTDLP_COOKIES = "cookies.txt"


# =========================
# LOAD API URL
# =========================

async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("Oneforall.platforms.Youtube.py")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pastebin.com/raw/MQAWnp49",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:

                if response.status == 200:
                    YOUR_API_URL = (await response.text()).strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
                    logger.info("Using fallback API URL")

    except Exception:
        YOUR_API_URL = FALLBACK_API_URL
        logger.info("Using fallback API URL")


# auto load
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass


# =========================
# HELPERS
# =========================

def extract_video_id(link: str):
    if "youtu.be/" in link:
        return link.split("youtu.be/")[-1].split("?")[0]
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    return link


# =========================
# FALLBACK YT-DLP (NEW)
# =========================

async def download_with_ytdlp(link: str, is_video: bool = False):
    ydl_opts = {
        "format": "best" if is_video else "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
    }

    if os.path.exists(YTDLP_COOKIES):
        ydl_opts["cookiefile"] = YTDLP_COOKIES

    try:
        loop = asyncio.get_event_loop()

        def run():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info)

        return await loop.run_in_executor(None, run)

    except Exception:
        return None


# =========================
# API DOWNLOAD - AUDIO
# =========================

async def download_song(link: str) -> str:
    global YOUR_API_URL

    if not YOUR_API_URL:
        await load_api_url()

    video_url = link
    video_id = extract_video_id(link)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{YOUR_API_URL}/download",
                params={"url": video_url, "type": "audio"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:

                if response.status != 200:
                    return await download_with_ytdlp(video_url, False)

                data = await response.json()
                download_token = data.get("download_token")

                if not download_token:
                    return await download_with_ytdlp(video_url, False)

            stream_url = f"{YOUR_API_URL}/stream/{download_token}"

            async with session.get(
                stream_url,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as file_response:

                if file_response.status != 200:
                    return await download_with_ytdlp(video_url, False)

                with open(file_path, "wb") as f:
                    async for chunk in file_response.content.iter_chunked(16384):
                        f.write(chunk)

        return file_path

    except Exception:
        return await download_with_ytdlp(video_url, False)


# =========================
# API DOWNLOAD - VIDEO
# =========================

async def download_video(link: str) -> str:
    global YOUR_API_URL

    if not YOUR_API_URL:
        await load_api_url()

    video_url = link
    video_id = extract_video_id(link)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{YOUR_API_URL}/download",
                params={"url": video_url, "type": "video"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:

                if response.status != 200:
                    return await download_with_ytdlp(video_url, True)

                data = await response.json()
                download_token = data.get("download_token")

                if not download_token:
                    return await download_with_ytdlp(video_url, True)

            stream_url = f"{YOUR_API_URL}/stream/{download_token}"

            async with session.get(
                stream_url,
                timeout=aiohttp.ClientTimeout(total=600)
            ) as file_response:

                if file_response.status != 200:
                    return await download_with_ytdlp(video_url, True)

                with open(file_path, "wb") as f:
                    async for chunk in file_response.content.iter_chunked(16384):
                        f.write(chunk)

        return file_path

    except Exception:
        return await download_with_ytdlp(video_url, True)


# =========================
# SHELL CMD
# =========================

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    out, errorz = await proc.communicate()

    if errorz:
        if "unavailable videos are hidden" in errorz.decode().lower():
            return out.decode()
        return errorz.decode()

    return out.decode()


# =========================
# YOUTUBE API CLASS
# =========================

class YouTubeAPI:

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message):
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

    # =========================
    # DETAILS
    # =========================

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)
        data = (await results.next())["result"][0]

        title = data["title"]
        duration_min = data["duration"]
        thumbnail = data["thumbnails"][0]["url"].split("?")[0]
        vidid = data["id"]

        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0

        return title, duration_min, duration_sec, thumbnail, vidid

    # =========================
    # SEARCH
    # =========================

    async def search(self, query: str, limit: int = 10):
        results = VideosSearch(query, limit=limit)
        return (await results.next())["result"]

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")

        item = result[query_type]

        return (
            item["title"],
            item["duration"],
            item["thumbnails"][0]["url"].split("?")[0],
            item["id"]
        )

    # =========================
    # FORMATS (UNCHANGED)
    # =========================

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        ydl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ydl_opts)

        formats_available = []

        with ydl:
            r = ydl.extract_info(link, download=False)

            for fmt in r.get("formats", []):
                try:
                    if "dash" not in str(fmt.get("format", "")).lower():
                        formats_available.append({
                            "format": fmt.get("format"),
                            "filesize": fmt.get("filesize"),
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "format_note": fmt.get("format_note"),
                            "yturl": link,
                        })
                except:
                    continue

        return formats_available, link

    # =========================
    # DOWNLOAD WRAPPER
    # =========================

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link

        try:
            if video:
                file = await download_video(link)
            else:
                file = await download_song(link)

            if file:
                return file, True

            return None, False

        except Exception:
            return None, False
