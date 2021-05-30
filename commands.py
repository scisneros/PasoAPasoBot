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
    logger.info(f"[Comando /comuna]")

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
