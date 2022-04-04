"""Module parse_config\n
Parse config file for kyubik_bot and QBWebAPI
"""


import os.path
import json


def parse_config(filename: str) -> dict:
    if not os.path.exists(filename):
        quit("Config file not found")
    with open(filename) as f:
        try:
            conf = json.load(f)
        except json.JSONDecodeError:
            quit("ERROR! Cannot parse config file")
    if type(conf) is not dict:
        quit("ERROR! Invalid JSON file")

    params = ["Server", "Username", "Password", "TelegramUser", "Token"]
    for p in params:
        if conf.get(p) is None:
            quit(f"ERROR! {p} not specified in config file")

    return conf
