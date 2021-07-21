import json

import locale
from os import path

from telegram.ext import CommandHandler, MessageHandler, Filters

import data
import constants

from bot import updater, dp, jq
from commands import estadisticas, region, start, comuna, comuna_private, get_log, force_check
from config.auth import admin_ids
from config.logger import logger
from functions import fetch_data, check_for_changes, save_data
from vaccination.functions import check_for_vaccination_changes, fetch_vaccination_data, load_vaccination_data

locale.setlocale(locale.LC_TIME, "es")

def main():
    try:
        with open("static/locations.json", "r", encoding="utf8") as datajsonfile:
            data.locations = json.load(datajsonfile)
        logger.info("Locations data loaded.")
    except OSError:
        logger.error("Locations data not found. Exiting.")
        return

    try:
        with open("data/data_comunas", "r", encoding="utf8") as datajsonfile:
            data.current_data = json.load(datajsonfile)
        logger.info("Comunas data loaded from local, initial check for changes will be made.")
        check_first = True
    except OSError:
        logger.info("No local data was found, initial scraping will be made without checking for changes.")
        check_first = False
        data.current_data = fetch_data()
        save_data()
        
    load_vaccination_data()

    jq.run_repeating(check_for_changes, interval=constants.FETCH_INTERVAL, first=(1 if check_first else None), name="job_fetch")
    jq.run_repeating(check_for_vaccination_changes, interval=constants.FETCH_INTERVAL_VAC, first=1, name="job_vaccination")

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('comuna', comuna))
    dp.add_handler(CommandHandler('region', region))
    dp.add_handler(MessageHandler(Filters.chat_type.private & (~ Filters.command), comuna_private))
    dp.add_handler(CommandHandler('estadisticas', estadisticas))
    # Admin commands
    dp.add_handler(CommandHandler('force_check', force_check, filters=Filters.user(admin_ids)))
    dp.add_handler(CommandHandler('get_log', get_log, filters=Filters.user(admin_ids)))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
