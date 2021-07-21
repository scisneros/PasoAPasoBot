from constants import MA_DAYS, MA_SMOOTHING, TARGET_POPULATION, TARGET_POPULATION_THRESHOLD, TOTAL_POPULATION, TOTAL_POPULATION_THRESHOLD
import csv
from datetime import datetime, timedelta
import json

import requests
from requests import RequestException

import data
from config.auth import vaccination_channel_id
from config.logger import logger
from utils import format_int, try_msg


def fetch_vaccination_data():
    url = "https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto76/vacunacion.csv"
    logger.info("Fetching vaccination data...")
    try:
        response = requests.get(url)
    except RequestException as e:
        logger.error("Connection error: {}".format(e))
        raise RequestException("Connection error on scraping")

    scraped_data = csv.reader(
        response.content.decode().split('\n'), delimiter=',')
    total_data = {}

    i = 0
    for row in scraped_data:
        if len(row) <= 0:
            continue
        if i == 0:
            total_data["date"] = row[2:]
        if row[0] == "Total":
            total_data[row[1]] = [float(x) for x in row[2:]]
        i += 1

    return total_data


def check_for_vaccination_changes(context):
    last_processed_data = ""
    if len(data.vaccination_data):
        last_processed_data = data.vaccination_data["date"][-1]

    raw_data = fetch_vaccination_data()

    if last_processed_data == datetime.strptime(raw_data["date"][-1], '%Y-%m-%d'):
        return

    data.vaccination_data["date"] = [datetime.strptime(x, '%Y-%m-%d') for x in raw_data["date"]]
    data.vaccination_data["first"] = raw_data["Primera"]
    data.vaccination_data["second"] = raw_data["Segunda"]
    data.vaccination_data["unique"] = raw_data["Unica"]

    process_vaccination_data()

    save_vaccination_processed_data()

    notify_vaccination_changes(context.bot)


def process_vaccination_data():
    dates = data.vaccination_data["date"]
    first = data.vaccination_data["first"]
    second = data.vaccination_data["second"]
    unique = data.vaccination_data["unique"]

    N = len(dates)

    done = []  # Second + Unique doses
    delta = []  # Differences in daily dones
    ma = []  # Delta Moving Averages
    ma_smoothed = []  # Smoothed Delta Moving Averages
    eta_threshold_target = []  # Estimated Time of Arrival for target population threshold
    eta_threshold_total = []  # Estimated Time of Arrival for total population threshold

    for i in range(N):
        done.append(second[i] + unique[i])

    for i in range(N):
        this_done = done[i]
        prev_done = done[i-1] if i > 0 else 0
        delta.append(this_done - prev_done)

    for i in range(N):
        ma_sum = 0
        for j in range(MA_DAYS):
            ma_sum += delta[i-j] if i-j >= 0 else 0
        ma.append(ma_sum / MA_DAYS)

    for i in range(N):
        ma_sum = 0
        for j in range(MA_SMOOTHING):
            ma_sum += ma[i-j] if i-j >= 0 else 0
        ma_smoothed.append(ma_sum / MA_SMOOTHING)

    for i in range(N):
        this_day = dates[i]
        if ma_smoothed[i] > 0:
            days_left_target = round(
                (TARGET_POPULATION*TARGET_POPULATION_THRESHOLD - done[i]) / ma_smoothed[i], 0)
            days_left_total = round(
                (TOTAL_POPULATION*TOTAL_POPULATION_THRESHOLD - done[i]) / ma_smoothed[i], 0)
            if days_left_target < 1000 and days_left_total < 1000:
                eta_threshold_target.append(this_day + timedelta(days=days_left_target))
                eta_threshold_total.append(this_day + timedelta(days=days_left_total))
                continue
        eta_threshold_target.append(None)
        eta_threshold_total.append(None)

    data.vaccination_data = {
        "date": dates,
        "first": first,
        "second": second,
        "unique": unique,
        "done": done,
        "delta": delta,
        "ma": ma,
        "ma_smoothed": ma_smoothed,
        "eta_threshold_target": eta_threshold_target,
        "eta_threshold_total": eta_threshold_total,
    }


def notify_vaccination_changes(bot):
    update_date = data.vaccination_data['date'][-1].strftime('%d/%m/%y').capitalize()
    total_str = format_int(
        data.vaccination_data['first'][-1] + data.vaccination_data['second'][-1] + data.vaccination_data['unique'][-1])
    first_str = format_int(data.vaccination_data['first'][-1])
    second_str = format_int(data.vaccination_data['second'][-1])
    unique_str = format_int(data.vaccination_data['unique'][-1])
    done_str = format_int(data.vaccination_data['done'][-1])
    percentage_str = '{:.1%}'.format(
        data.vaccination_data['done'][-1]/TARGET_POPULATION)
    target_str = format_int(TARGET_POPULATION)
    delta_str = format_int(data.vaccination_data['delta'][-1])
    ma_str = format_int(data.vaccination_data['ma'][-1])
    target_with_threshold = format_int(TARGET_POPULATION*TARGET_POPULATION_THRESHOLD)
    eta_target_str = data.vaccination_data['eta_threshold_target'][-1].strftime('%d de %B de %Y')
    days_left_target = (data.vaccination_data['eta_threshold_target'][-1] - datetime.today()).days
    total_with_threshold = format_int(TOTAL_POPULATION*TOTAL_POPULATION_THRESHOLD)
    eta_total_str = data.vaccination_data['eta_threshold_total'][-1].strftime('%d de %B de %Y')
    days_left_total = (data.vaccination_data['eta_threshold_total'][-1] - datetime.today()).days

    message = f"<b>💉 [Actualización]</b> - <i>Datos al {update_date}</i>\n\n"

    message += f"<b>Vacunas totales:</b> {total_str}\n"
    message += f"<b>Primera vacuna:</b> {first_str}\n"
    message += f"<b>Segunda vacuna:</b> {second_str}\n"
    message += f"<b>Vacuna dosis única:</b> {unique_str}\n\n"

    message += f"<b>Esquema completo (2da o Única):</b> {done_str}\n"
    message += f"<b>Población objetivo:</b> {target_str} mayores de 12 años\n"
    message += f"<b>Progreso:</b> {percentage_str} de la población objetivo\n\n"

    message += f"<b>Esquemas completos del día:</b> {delta_str}\n"
    message += f"<b>Promedio semanal:</b> {ma_str} esquemas completos por día\n\n"
    message += f"<b>🗓 Estimación esquema completo en {int(TARGET_POPULATION_THRESHOLD*100)}% de la población objetivo:</b>\n"
    message += f"<i>{target_with_threshold} mayores de 12 años</i>\n"
    message += f"{eta_target_str} ({days_left_target} días)\n\n"
    message += f"<b>🗓 Estimación esquema completo en {int(TOTAL_POPULATION_THRESHOLD*100)}% de la población total:</b>\n"
    message += f"<i>{total_with_threshold} personas</i>\n"
    message += f"{eta_total_str} ({days_left_total} días)\n"

    try_msg(bot,
            chat_id=vaccination_channel_id,
            parse_mode="HTML",
            text=message)


def save_vaccination_processed_data():
    processed_data = data.vaccination_data.copy()
    str_date = [(x.strftime('%Y-%m-%d') if x else None)
                for x in processed_data["date"]]
    str_eta_target = [(x.strftime('%Y-%m-%d') if x else None)
                      for x in processed_data["eta_threshold_target"]]
    str_eta_total = [(x.strftime('%Y-%m-%d') if x else None)
                     for x in processed_data["eta_threshold_total"]]
    processed_data["date"] = str_date
    processed_data["eta_threshold_target"] = str_eta_target
    processed_data["eta_threshold_total"] = str_eta_total
    with open("data/data_vaccination", "w") as vaccination_data_file:
        json.dump(processed_data, vaccination_data_file, indent=4)


def load_vaccination_data():
    try:
        with open("data/data_vaccination", "r") as vaccination_data_file:
            file_data = json.load(vaccination_data_file)
            datetime_date = [datetime.strptime(x, '%Y-%m-%d')
                             for x in file_data["date"]]
            datetime_eta_target = [(datetime.strptime(x, '%Y-%m-%d') if x else None)
                                   for x in file_data["eta_threshold_target"]]
            datetime_eta_total = [(datetime.strptime(x, '%Y-%m-%d') if x else None)
                                  for x in file_data["eta_threshold_total"]]
            file_data["date"] = datetime_date
            file_data["eta_threshold_target"] = datetime_eta_target
            file_data["eta_threshold_total"] = datetime_eta_total
            data.vaccination_data = file_data
        logger.info("Vaccination data loaded from local.")
    except OSError:
        logger.info("No local vaccination data was found.")