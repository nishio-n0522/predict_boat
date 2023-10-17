import os
from pathlib import Path

from pyparsing import Word, alphas

from db.db_setting import session
import db


weather_table = db.WeatherType(weather_type = "晴")
weather_table = db.WeatherType(weather_type = "曇り")
weather_table = db.WeatherType(weather_type="雨")
weather_table = db.WeatherType(weather_type="雪")

def insert_new_weather():
    pass