FETCH_INTERVAL = 300

MAX_RESULTS = 10

PHASES_EMOJIS = {
    1: "\U0001F534",
    2: "\U0001F7E0",
    3: "\U0001F7E1",
    4: "\U0001F7E2",
    5: "\U0001F535",
}

PASOS_NAMES = {
    1: "Cuarentena",
    2: "Transición",
    3: "Preparación",
    4: "Apertura Inicial",
    5: "Apertura Avanzada",
}

CHANGE_DAY = {
    1: {  # Monday
        "up": {"day": "jueves", "time": "5:00am"},
        "down": {"day": "jueves", "time": "5:00am"}
    },
    4: {  # Thursday
        "up": {"day": "lunes", "time": "5:00am"},
        "down": {"day": "sábado", "time": "5:00am"}
    }
}
