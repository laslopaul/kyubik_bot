"""
Module qb_instance - contains an instance of QBWebAPI class, which is used by
bot message handlers
"""

from app.parse_config import parse_config
import app.qb_control as qb_control

cfg = parse_config("config.json")
qb = qb_control.QBWebAPI(cfg["Server"], cfg["Username"], cfg["Password"])
