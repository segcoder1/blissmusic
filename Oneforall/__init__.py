from SafoneAPI import SafoneAPI

from Oneforall.core.bot import Hotty
from Oneforall.core.dir import dirr
from Oneforall.core.git import git
from Oneforall.core.userbot import Userbot
from Oneforall.misc import dbb, heroku, sudo

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Hotty()
userbot = Userbot()
api = SafoneAPI()

# Load sudo users on startup
import asyncio
try:
    asyncio.get_event_loop().run_until_complete(sudo())
except RuntimeError:
    # If event loop is already running, skip this
    pass


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()

APP = "Raiden_Robot"  # connect music api key "Dont change it"
