from telegram.ext import CommandHandler, Filters

import constants
from bot import updater, dp, jq
from commands import start, comuna, get_log, force_check
from config.auth import admin_ids
from functions import fetch_data


def main():
    jq.run_repeating(fetch_data, interval=300, first=(
        0 if constants.CHECK_FIRST else None), name="job_check")

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('comuna', comuna))
    # Admin commands
    dp.add_handler(CommandHandler('force_check', force_check,
                   filters=Filters.user(admin_ids)))
    dp.add_handler(CommandHandler('get_log', get_log,
                   filters=Filters.user(admin_ids)))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
