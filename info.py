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
SESSION = environ.get('SESSION', 'autofilter')
API_ID = environ.get('API_ID', "11948995")
API_HASH = environ.get('API_HASH', "cdae9279d0105638165415bf2769730d")
BOT_TOKEN = environ.get('BOT_TOKEN', "6496586495:AAFZXdcbC7XANI3lwtmeDTPVs43EHp0HG3I")

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))

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
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://ryu:ryu@ryu.watcr8f.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = environ.get('DATABASE_NAME', "primehub")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'ryu')

# Others
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1001770663662'))
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'iPrimeHub')
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "True")), False)
IMDB = is_enabled((environ.get('IMDB', "False")), True)
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "True")), False)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", None)
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", "<b>Query: {query}</b> \n‌‌‌‌IMDb Data:\n\n🏷 Title: <a href={url}>{title}</a>\n🎭 Genres: {genres}\n📆 Year: <a href={url}/releaseinfo>{year}</a>\n🌟 Rating: <a href={url}/ratings>{rating}</a> / 10")
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "False"), True)
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "False")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "False")), True)
APPROVE = is_enabled(environ.get("AUTO_APPROVE", "True"), True)
MAINTAINENCE_MODE = is_enabled(environ.get("MAINTAINENCE_MODE", "False"), True)
FORCESUB_CHANNEL = int(environ.get('FORCESUB_CHANNEL', "-1001773614166"))
SLOW_MODE_DELAY = int(environ.get('SLOW_MODE_DELAY', 60))
RESPONCE_LIMIT = int(environ.get('RESPONCE_LIMIT', 10))
ONE_LINK_ONE_FILE = is_enabled((environ.get('ONE_LINK_ONE_FILE', "True")), False)
accss_grp = environ.get('ACCESS_GROUP', "-1001786962803")
ACCESS_GROUPS = [int(ch) for ch in accss_grp.split()] if auth_grp else None
WAIT_TIME = int(environ.get('AUTO_DELETE_WAIT_TIME', 600))
APPROVE = is_enabled(environ.get("APPROVE", "True"), True)
DB_URI = environ.get('DATABASE_URI', "mongodb+srv://msg:msg@msg.dkqp9lz.mongodb.net/?retryWrites=true&w=majority")
PROFANITY_FILTER = is_enabled(environ.get("PROFANITY_FILTER", "False"), False)
# for copying all files into db
FORWARD_CHANNEL = int(environ.get('FORWARD_CHANNEL', "-1002072810590"))

# For stream purposes
BIN_CHANNEL = environ.get("BIN_CHANNEL", "-1001935670400")
URL = environ.get("URL", "https://linkrobot.onrender.com")
