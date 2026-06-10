import requests

WMO_CODES = {
    0: "晴天", 1: "大部晴朗", 2: "多云", 3: "阴天",
    45: "雾", 48: "霜雾",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "中阵雨", 82: "大阵雨",
    95: "雷暴", 96: "冰雹雷暴", 99: "大冰雹雷暴"
}


class WeatherClient:
    GEO_BASE = "https://geocoding-api.open-meteo.com/v1"
    WTH_BASE = "https://api.open-meteo.com/v1"

    def search_city(self, keyword):
        resp = requests.get(f"{self.GEO_BASE}/search",
                            params={"name": keyword, "count": 5, "language": "zh",
                                    "format": "json"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return [{"id": f"{r['latitude']},{r['longitude']}",
                 "name": r.get("name", ""),
                 "adm1": r.get("admin1", ""),
                 "adm2": r.get("admin2", ""),
                 "lat": r["latitude"], "lon": r["longitude"]}
                for r in results]

    def get_now(self, location_id):
        lat, lon = location_id.split(",")
        resp = requests.get(f"{self.WTH_BASE}/forecast",
                            params={
                                "latitude": lat, "longitude": lon,
                                "current": "temperature_2m,relative_humidity_2m,"
                                           "wind_speed_10m,wind_direction_10m,"
                                           "apparent_temperature,weather_code",
                                "timezone": "auto", "forecast_days": 0
                            }, timeout=10)
        resp.raise_for_status()
        c = resp.json()["current"]
        code = c["weather_code"]
        return {
            "temp": c["temperature_2m"],
            "feels_like": c["apparent_temperature"],
            "text": WMO_CODES.get(code, f"代码{code}"),
            "icon": self._icon(code),
            "humidity": c["relative_humidity_2m"],
            "wind_dir": f"{c['wind_direction_10m']}°",
            "wind_speed": f"{c['wind_speed_10m']} km/h"
        }

    def get_forecast(self, location_id, days=7):
        lat, lon = location_id.split(",")
        resp = requests.get(f"{self.WTH_BASE}/forecast",
                            params={
                                "latitude": lat, "longitude": lon,
                                "daily": "temperature_2m_max,temperature_2m_min,"
                                         "weather_code,precipitation_probability_max",
                                "timezone": "auto",
                                "forecast_days": min(days, 16)
                            }, timeout=10)
        resp.raise_for_status()
        daily = resp.json()["daily"]
        return [{
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "code": daily["weather_code"][i],
            "text_day": WMO_CODES.get(daily["weather_code"][i], "-"),
            "text_night": "",
            "humidity": "",
            "wind_dir": "",
            "wind_speed": ""
        } for i in range(len(daily["time"]))]

    def get_life_index(self, location_id):
        lat, lon = location_id.split(",")
        resp = requests.get(f"{self.WTH_BASE}/forecast",
                            params={
                                "latitude": lat, "longitude": lon,
                                "daily": "uv_index_max",
                                "current": "uv_index",
                                "timezone": "auto",
                                "forecast_days": 1
                            }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        uv = data.get("current", {}).get("uv_index", 0)
        uv_level = "低" if uv < 3 else ("中等" if uv < 6 else ("高" if uv < 8 else "极高"))
        return [
            {"type": "紫外线指数", "level": uv_level, "text": f"UV {uv}"},
            {"type": "舒适度", "level": "参考", "text": "请根据实际体感判断"}
        ]

    @staticmethod
    def _icon(code):
        if code == 0: return "☀️"
        if code <= 2: return "🌤"
        if code == 3: return "☁️"
        if code <= 48: return "🌫"
        if code <= 55: return "🌧"
        if code <= 65: return "🌧"
        if code <= 75: return "❄️"
        if code <= 82: return "⛈"
        return "⚡"
