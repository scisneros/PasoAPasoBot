from telegram import TelegramError, constants as tg_constants
from telegram.error import BadRequest, Unauthorized
from unidecode import unidecode

from config.logger import logger


def slugify(value):
    value = value.replace("\n", "").replace("\t", "").strip(" ")  # Remove empty spaces
    value = value.replace(" - ", "-").replace("'", "")  # Remove special cases
    value = value.replace(" ", "-")
    value = unidecode(value)  # Remove accents
    value = value.lower()
    return value


def try_msg(bot, attempts=2, **params):
    chat_id = params["chat_id"]
    attempt = 1
    while attempt <= attempts:
        try:
            bot.send_message(**params)
        except TelegramError as e:
            logger.error(f"[Attempt {attempt}/{attempts}] Messaging chat {chat_id} raised following error: {type(e).__name__}: {e}")
        else:
            break
        attempt += 1

    if attempt > attempts:
        logger.error(f"Max attempts reached for chat {str(chat_id)}. Aborting message and raising exception.")


def send_long_message(bot, **params):
    text = params.pop("text", "")
    maxl = tg_constants.MAX_MESSAGE_LENGTH
    if len(text) > maxl:
        slice_index = maxl
        for i in range(maxl, -1, -1):
            if text[i] == "\n":
                slice_index = i
                break
        sliced_text = text[:slice_index]
        rest_text = text[slice_index + 1:]
        try_msg(bot, text=sliced_text, **params)
        send_long_message(bot, text=rest_text, **params)
    else:
        try_msg(bot, text=text, **params)


def format_int(number):
    return '{:,}'.format(int(number)).replace(',','.')


def searchBySlug(slug, data):
    for item in data:
        if item.get("slug", "") == slug:
            return item
    return None