from constants import MAX_RESULTS, PHASES_EMOJIS
import os
from datetime import datetime
from utils import try_msg

from bot import dp, jq
import data
from config.logger import logger


def start(update, context):
    logger.info(f"[Command /start]")
    try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text="¡Hola! Utiliza el comando \"/comuna <i>[nombre-de-comuna]\"</i> para consultar su estado en el plan Paso a Paso.")


def comuna(update, context):
    logger.info(f"[Command {update.message.text}]")
    try:
        arg = update.message.text[(update.message.text.index(" ") + 1):]
    except ValueError:
        try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text="Envía el nombre o parte del nombre de la comuna que quieres consultar.\nEj: <i>\"/comuna santiago\"</i>")
        return
    matches = [comuna for comuna in data.current_data if comuna[0].lower().find(arg.lower()) >= 0]
    message = ""
    if len(matches) > MAX_RESULTS:
        message += f"<i>Mostrando {MAX_RESULTS} resultados de {len(matches)}:</i>\n"
    for match in matches[:MAX_RESULTS]:
        message += f"{PHASES_EMOJIS[int(match[1])]} <b>{match[0]}</b> - Paso {match[1]} {match[2]}\n"
    try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text=message)


def estadisticas(update, context):
    logger.info("[Command /estadisticas]")
    counts = [0, 0, 0, 0, 0]
    for comuna in data.current_data:
        counts[int(comuna[1]) - 1] += 1
    message = "Comunas por paso:\n"
    for i in range(len(counts)):
        message += f"{PHASES_EMOJIS[i+1]} <b>Paso {i+1}</b>: {counts[i]}\n"
    try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text=message)


# Admin Commands

def force_check(update, context):
    logger.info(
        f"[Command /force_check from admin {update.message.from_user.id}]")
    job_fetch = jq.get_jobs_by_name("job_fetch")[0]
    job_fetch.run(dp)


def get_log(update, context):
    logger.info(f"[Command /get_log from admin {update.message.from_user.id}]")
    context.bot.send_document(chat_id=update.message.from_user.id,
                              document=open(os.path.relpath('bot.log'), 'rb'),
                              filename=f"pasoapasobot_log_{datetime.now().strftime('%d%b%Y-%H%M%S')}.txt")
