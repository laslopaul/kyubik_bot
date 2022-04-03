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
            quit("Cannot parse config file")
    if type(conf) is not dict:
        quit("Invalid JSON file")
    if conf.get("Server") is None:
        quit("Server URL is not specified in config file")
    if conf.get("Username") is None or conf.get("Password") is None:
        quit("Login credentials are not specified in config file")

    return conf
