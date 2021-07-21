from constants import CHANGE_DAY, PASOS_NAMES, PASOS_EMOJIS
import json
from os import path
from utils import searchBySlug, send_long_message, slugify, try_msg

import copy
import requests
from datetime import datetime
from requests import RequestException

import data
from config.auth import channel_id
from config.logger import logger

def fetch_data():
    url = "https://e.infogram.com/81277d3a-5813-46f7-a270-79d1768a70b2"
    logger.info("Fetching phases data...")
    try:
        response = requests.get(url)
    except RequestException as e:
        logger.error("Connection error: {}".format(e))
        raise RequestException("Connection error on scraping")

    scraped_data = [line for line in response.content.decode().split('\n') if "window.infographicData" in line]
    scraped_data_json = json.loads(scraped_data[0].replace("<script>window.infographicData=", "", 1).replace(";</script>", "", 1))
    infographic_data = scraped_data_json["elements"]["content"]["content"]["entities"]["3f026fbf-998f-4ae2-852b-94fa3a2f71d4"]["props"]["chartData"]["data"][0][1:]

    comunas_dict = {}
    for comuna in infographic_data:
        comunas_dict[slugify(comuna[0])] = {"paso": comuna[1], "info": comuna[2].strip(" ")}

    data_dict = {}
    for region in data.locations["regiones"]:
        comunas = []
        for comuna in region["comunas"]:
            comuna_data = comunas_dict.get(comuna["slug"], {})
            comunas.append({
                "nombre": comuna["nombre"],
                "slug": comuna["slug"],
                "paso": comuna_data.get("paso", "-1"),
                "info": comuna_data.get("info", "")
            })
        data_dict.setdefault("regiones", []).append({"nombre": region["nombre"], "slug": region["slug"], "comunas": comunas})

    return data_dict


def check_for_changes(context):
    data.new_data = fetch_data()

    regiones_changes = []
    up_count = 0
    down_count = 0
    enter_counts = [0, 0, 0, 0]
    leave_counts = [0, 0, 0, 0]
    for old_region in data.current_data["regiones"]:
        new_region = searchBySlug(old_region["slug"], data.new_data["regiones"])
        comunas_changes = []
        for old_comuna in old_region["comunas"]:
            slug = old_comuna["slug"]
            new_comuna = searchBySlug(slug, new_region["comunas"])
            if old_comuna["paso"] != new_comuna["paso"]:
                changed_comuna = new_comuna.copy()
                changed_comuna["prev"] = old_comuna["paso"]
                comunas_changes.append(changed_comuna)

                if old_comuna["paso"] < new_comuna["paso"]:
                    up_count += 1
                else:
                    down_count += 1
                    
                enter_counts[int(new_comuna["paso"])-1] += 1
                leave_counts[int(old_comuna["paso"])-1] += 1
        if comunas_changes:
            regiones_changes.append({"nombre": new_region["nombre"], "comunas": comunas_changes})
    
    if regiones_changes:
        notify_changes(context.bot, regiones_changes, {"up": up_count, "down": down_count, "enter": enter_counts, "leave": leave_counts})
    
    data.current_data = data.new_data

    save_data()


def notify_changes(bot, changes, counts):
    time_now = datetime.now().strftime('%A %d/%m/%y %H:%M').capitalize()

    new_counts = get_steps_counts(current=False)
    message = f"<b>[Cambios detectados]</b>\n"
    message += f"<i>{time_now}</i>\n"
    message += "\n"
    message += f"<b>Avances:</b> {counts['up']}\n"
    message += f"<b>Retrocesos:</b> {counts['down']}\n"
    message += "\n"
    message += "<b>Comunas por paso:</b>\n"
    for i in range(len(new_counts)):
        message += f"{PASOS_EMOJIS[i+1]} <b>Paso {i+1}</b>: {new_counts[i]} [+{counts['enter'][i]}, -{counts['leave'][i]}]\n"
    message += "\n"
    #current_day = int(datetime.now().strftime('%w'))
    current_day = 1
    if current_day in CHANGE_DAY:
        message += f"<b>Avances</b> vigentes desde el <b>{CHANGE_DAY[current_day]['up']['day']}</b> a las {CHANGE_DAY[current_day]['up']['time']}\n"
        message += f"<b>Retrocesos</b> vigentes desde el <b>{CHANGE_DAY[current_day]['down']['day']}</b> a las {CHANGE_DAY[current_day]['down']['time']}\n"
    try_msg(bot,
            chat_id=channel_id,
            parse_mode="HTML",
            text=message)
    message = ""

    for region in changes:
        message += f"<b>[{region['nombre']}]</b>\n"
        message += "\n"
        for comuna in region["comunas"]:
            prev = int(comuna["prev"])
            curr = int(comuna["paso"])
            action = "Avanza" if curr > prev else "Retrocede"
            message += f"<b>{comuna['nombre']}</b>: {action}\n"
            message += f"  {PASOS_EMOJIS[curr]} Paso {curr} {PASOS_NAMES[curr]}\n"
        message += "\n"
        message += "——————————\n"
        message += "\n"

    send_long_message(bot,
                      chat_id=channel_id,
                      parse_mode="HTML",
                      text=message,
                      max_length=1800,
                      slice_str="\n<b>[")


def get_steps_counts(current = True):
    counts = [0, 0, 0, 0]
    for region in (data.current_data["regiones"] if current else data.new_data["regiones"]):
        for comuna in region["comunas"]:
            counts[int(comuna["paso"]) - 1] += 1
    
    return counts


def save_data():
    with open("data/data_comunas", "w", encoding="utf8") as infographic_data_file:
        json.dump(data.current_data, infographic_data_file, indent=4, ensure_ascii=False)