from telegram import TelegramError, constants as tg_constants
from telegram.error import BadRequest, Unauthorized

from config.logger import logger


def full_strip(st):
    return st.replace("\n", "").replace("\t", "").strip(" ")


def try_msg(bot, attempts=2, **params):
    chat_id = params["chat_id"]
    attempt = 1
    while attempt <= attempts:
        try:
            bot.send_message(**params)
        except Unauthorized:
            logger.error(f"Chat {chat_id} bloqueó al bot. Abortando mensaje")
            break
        except BadRequest as e:
            logger.error(f"Mensaje al chat {chat_id} arrojó BadRequest: {e}. Abortando mensaje.")
            raise
        except TelegramError as e:
            logger.error(f"[Intento {attempt}/{attempts}] Mensaje al chat {chat_id} arrojó el siguiente error: {type(e).__name__}: {e}")
        else:
            break
        attempt += 1

    if attempt > attempts:
        logger.error(f"Máximos intentos para el chat {str(chat_id)}. Abortando mensaje.")


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
