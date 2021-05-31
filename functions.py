from constants import CHANGE_DAY, PASOS_NAMES, PHASES_EMOJIS
import json
from os import path
from utils import send_long_message

import requests
from datetime import datetime
from requests import RequestException

import data
from config.auth import channel_id
from config.logger import logger


def fetch_data():
    url = "https://e.infogram.com/81277d3a-5813-46f7-a270-79d1768a70b2"
    logger.info("Consultando data de pasos de comunas...")
    try:
        response = requests.get(url)
    except RequestException as e:
        logger.error("Connection error: {}".format(e))
        raise RequestException("Connection error on scraping")

    scraped_data = [line for line in response.content.decode().split('\n') if "window.infographicData" in line]
    scraped_data_json = json.loads(scraped_data[0].replace("<script>window.infographicData=", "", 1).replace(";</script>", "", 1))
    infographic_data = scraped_data_json["elements"]["content"]["content"]["entities"]["3f026fbf-998f-4ae2-852b-94fa3a2f71d4"]["props"]["chartData"]["data"][0][1:]

    data_dict = {}
    for comuna in infographic_data:
        data_dict[comuna[0]] = {"paso": comuna[1], "info": comuna[2]}

    return data_dict


def check_for_changes(context):
    data.new_data = fetch_data()

    changes = {}
    for comuna, old_comuna_data in data.current_data.items():
        new_comuna_data = data.new_data[comuna]
        if old_comuna_data["paso"] != new_comuna_data["paso"]:
            changes[comuna] = new_comuna_data.copy()
            changes[comuna]["prev"] = old_comuna_data["paso"]
    
    if changes:
        notify_changes(context.bot, changes)

    data.current_data = data.new_data

    save_data()


def notify_changes(bot, changes):
    message = f"<b>[Cambios detectados]</b>\n<i>{datetime.now().strftime('%A %d/%m/%y %H:%M').capitalize()}</i>\n\n"
    for comuna, comuna_data in changes.items():
        prev = int(comuna_data["prev"])
        curr = int(comuna_data["paso"])
        curr_info = comuna_data["info"]
        message += f"<b>{comuna}</b>\n<del><i>Paso {prev} {PASOS_NAMES[prev]}</i></del>\n{PHASES_EMOJIS[curr]} Paso {curr} {PASOS_NAMES[curr]}\n\n"

    current_day = int(datetime.now().strftime('%w'))
    if current_day in CHANGE_DAY:
        message += f"<b>Avances</b> vigentes desde el <b>{CHANGE_DAY[current_day]['up']['day']}</b> a las {CHANGE_DAY[current_day]['up']['time']}\n"
        message += f"<b>Retrocesos</b> vigentes desde el <b>{CHANGE_DAY[current_day]['down']['day']}</b> a las {CHANGE_DAY[current_day]['down']['time']}\n"
    send_long_message(bot,
                      chat_id=channel_id,
                      parse_mode="HTML",
                      text=message)


def save_data():
    with open("data/data_comunas", "w") as infographic_data_file:
        json.dump(data.current_data, infographic_data_file, indent=4)