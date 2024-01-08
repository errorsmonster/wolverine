import re
from os import environ

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# Bot information
API_ID = environ.get('API_ID', "11948995")
API_HASH = environ.get('API_HASH', "cdae9279d0105638165415bf2769730d")
BOT_TOKEN = environ.get('BOT_TOKEN', "5207489037:AAEtZTr6Ni-dUsmIC5Eh6ZqA_X46kqUYhvA")

# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1247742004 2141736280').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '0').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_channel = environ.get('AUTH_CHANNEL', '-1001596389161')
auth_grp = environ.get('AUTH_GROUP', "-1001522024342")
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://Prime:Prime@cluster0.tajxlrr.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = environ.get('DATABASE_NAME', "Rajappan")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'netflimsbot')

# Others
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1001770663662'))
FORCESUB_CHANNEL = int(environ.get('FORCESUB_CHANNEL', "-1001773614166"))
SLOW_MODE_DELAY = int(environ.get('SLOW_MODE_DELAY', 60))
WAIT_TIME = int(environ.get('AUTO_DELETE_WAIT_TIME', 600))
FORWARD_CHANNEL = int(environ.get('FORWARD_CHANNEL', "-1002123504264"))

# other
ACCESS_KEY = environ.get("LICENSE_ACCESS_KEY", "PZUNTLGIZFE67MR0I0H0")
BIN_CHANNEL = environ.get("BIN_CHANNEL", "-1001935670400")
URL = environ.get("STREAM_URL", "https://linkrobot.onrender.com")
SHORTNER_SITE = environ.get("SHORTNER_SITE", "https://shortyfi.in/api")
SHORTNER_API = environ.get("SHORTNER_API", "ce34a5441431b6af2d82a88cb46fd8c0301e6ff2")
