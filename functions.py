import json
from os import path

import requests
from requests import RequestException

import data
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
    return infographic_data


def check_for_changes(context):
    data.new_data = fetch_data()

    # check diff here

    data.current_data = data.new_data

    save_data()


def save_data():
    with open("data/data_comunas", "w") as infographic_data_file:
        json.dump(data.current_data, infographic_data_file, indent=4)