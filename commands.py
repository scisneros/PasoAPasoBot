import os
import datetime

from config.logger import logger


def start(update, context):
    logger.info(f"[Comando /start desde admin {update.message.from_user.id}]")


def comuna(update, context):
    logger.info(f"[Comando /comuna desde admin {update.message.from_user.id}]")


def force_check(update, context):
    logger.info(f"[Comando /force_check desde admin  {update.message.from_user.id}]")


def get_log(update, context):
    logger.info(f"[Comando /get_log desde admin  {update.message.from_user.id}]")
    context.bot.send_document(chat_id=update.message.from_user.id,
                              document=open(os.path.relpath('bot.log'), 'rb'),
                              filename=f"pasoapasobot_log_{datetime.now().strftime('%d%b%Y-%H%M%S')}.txt")
