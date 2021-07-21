from functions import get_steps_counts
from constants import MAX_RESULTS, PASOS_EMOJIS
import os
from datetime import datetime
from utils import slugify, try_msg

from bot import dp, jq
import data
from config.logger import logger


def start(update, context):
    logger.info(f"[Command /start]")
    message = "¡Hola! Utiliza el comando \"/comuna <i>[nombre-de-comuna]\"</i> para consultar su estado en el plan Paso a Paso.\n"
    if update.message.chat.type == "private":
        message += "\nSi me hablas por este chat privado, no es necesario incluir el comando \"/comuna\", tomaré todos los mensajes directos como consultas de comuna."
    try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text=message)


def comuna(update, context):
    logger.info(f"[Command {update.message.text} from {update.message.chat_id}]")
    try:
        arg = update.message.text[(update.message.text.index(" ") + 1):]
    except ValueError:
        message = "Envía el nombre o parte del nombre de la comuna que quieres consultar.\nEj: <i>\"/comuna santiago\"</i>\n"
        if update.message.chat.type == "private":
            message += "\nSi me hablas por este chat privado, no es necesario incluir el comando \"/comuna\", tomaré todos los mensajes directos como consultas de comuna."
        try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text=message)
        return
    slug_arg = slugify(arg)
    matches = []
    for region in data.current_data["regiones"]:
        for comuna in region["comunas"]:
            result_index = comuna["slug"].find(slug_arg)
            if result_index >= 0:
                comuna_copy = comuna.copy()
                comuna_copy["index"] = result_index
                matches.append(comuna_copy)
    matches.sort(key=lambda comuna: comuna["nombre"])
    matches.sort(key=lambda comuna: comuna["index"])

    message = ""
    if len(matches) > MAX_RESULTS:
        message += f"<i>Mostrando {MAX_RESULTS} resultados de {len(matches)}:</i>\n"
    for match in matches[:MAX_RESULTS]:
        message += f"{PASOS_EMOJIS[int(match['paso'])]} <b>{match['nombre']}</b> - Paso {match['paso']} {match['info']}\n"
    
    if not matches:
        try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="Markdown",
            text=f"No encuentro ninguna comuna con _{arg}_.")
    else:
        try_msg(context.bot,
                chat_id=update.message.chat_id,
                parse_mode="HTML",
                text=message)


def region(update, context):
    logger.info(f"[Command {update.message.text} from {update.message.chat_id}]")
    try:
        arg = update.message.text[(update.message.text.index(" ") + 1):]
    except ValueError:
        message = "Envía el nombre o parte del nombre de la región que quieres consultar.\nEj: <i>\"/region valparaiso\"</i>\n"
        try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="HTML",
            text=message)
        return
    slug_arg = slugify(arg)
    matches = []
    for region in data.current_data["regiones"]:
        result_index = region["slug"].find(slug_arg)
        if result_index >= 0:
            region_copy = region.copy()
            region_copy["index"] = result_index
            matches.append(region_copy)

    message = ""
    if len(matches) > 1:
        message += f"<i>Encontré {len(matches)} regiones con ese término. Refina la búsqueda para mostrar el resultado.</i>\n"
        for match in matches:
            message += f"<b>{match['nombre']}</b>\n"

    elif len(matches) == 1:
        match = matches[0]
        message += f"<b>{match['nombre']}</b>\n"
        for comuna in match["comunas"]:
            message += f"{PASOS_EMOJIS[int(comuna['paso'])]} <b>{comuna['nombre']}</b> - Paso {comuna['paso']} {comuna['info']}\n"
    
    if not matches:
        try_msg(context.bot,
            chat_id=update.message.chat_id,
            parse_mode="Markdown",
            text=f"No encuentro ninguna región con _{arg}_.")
            
    else:
        try_msg(context.bot,
                chat_id=update.message.chat_id,
                parse_mode="HTML",
                text=message)


def comuna_private(update, context):
    update.message.text = "/comuna " + update.message.text
    comuna(update, context)


def estadisticas(update, context):
    logger.info("[Command /estadisticas]")
    counts = get_steps_counts()
    total = sum(counts)
    percents = [round(x*100/total, 1) for x in counts]
    message = "Comunas por paso:\n"
    for i in range(len(counts)):
        message += f"{PASOS_EMOJIS[i+1]} <b>Paso {i+1}</b>: {counts[i]} <i>({percents[i]}%)</i>\n"
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
