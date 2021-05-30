from constants import MAX_RESULTS, PHASES_EMOJIS
import os
import datetime
from utils import try_msg

from bot import dp, jq
import data
from config.logger import logger


def start(update, context):
    logger.info(f"[Comando /start]")
    try_msg(context.bot,
            chat_id=update.message.chat_id,
            text="Holi!")


def comuna(update, context):
    logger.info(f"[Comando {update.message.text}]")
    arg = update.message.text[(update.message.text.index(" ") + 1):]
    matches = [comuna for comuna in data.current_data if comuna[0].lower().find(arg.lower()) >= 0]
    message = ""
    if len(matches) > MAX_RESULTS:
        message += f"<i>Mostrando {MAX_RESULTS} resultados de {len(matches)}:</i>\n"
    for match in matches[:MAX_RESULTS]:
        message += f"{PHASES_EMOJIS[match[1]]} <b>{match[0]}</b> - Fase {match[1]} {match[2]}\n"
    try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text=message)

# Admin Commands

def force_check(update, context):
    logger.info(
        f"[Comando /force_check desde admin  {update.message.from_user.id}]")
    job_fetch = jq.get_jobs_by_name("job_fetch")[0]
    job_fetch.run(dp)


def get_log(update, context):
    logger.info(f"[Comando /get_log desde admin  {update.message.from_user.id}]")
    context.bot.send_document(chat_id=update.message.from_user.id,
                              document=open(os.path.relpath('bot.log'), 'rb'),
                              filename=f"pasoapasobot_log_{datetime.now().strftime('%d%b%Y-%H%M%S')}.txt")
