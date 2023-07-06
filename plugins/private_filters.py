import re
import math
from Script import script
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from pyrogram.errors import MessageNotModified
from utils import get_size, get_settings, replace_blacklist
from database.ia_filterdb import get_search_results
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
blacklist = script.BLACKLIST



        


