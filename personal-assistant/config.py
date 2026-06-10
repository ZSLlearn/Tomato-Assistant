import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "data.db")
# 天气使用 Open-Meteo API，免费无需 KEY
DEFAULT_CITY = "北京"
