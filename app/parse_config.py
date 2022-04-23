"""Module parse_config\n
Config file parser for kyubik_bot and QBWebAPI
"""


import json


def parse_config(filename: str) -> dict:
    with open(filename) as f:
        try:
            conf = json.load(f)
        except FileNotFoundError:
            quit("Config file not found")
        except json.JSONDecodeError:
            quit("ERROR! Cannot parse config file")
    if type(conf) is not dict:
        quit("ERROR! Invalid JSON file")

    params = ["Server", "Username", "Password", "TelegramUser", "Token"]
    for p in params:
        if conf.get(p) is None:
            quit(f"ERROR! {p} not specified in config file")

    return conf
