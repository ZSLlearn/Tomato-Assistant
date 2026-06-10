from .hefeng_client import WeatherClient


class WeatherService:
    def __init__(self):
        self.client = WeatherClient()
        self._city_cache = {}

    def search_city(self, keyword):
        if not keyword:
            raise ValueError("搜索关键词不能为空")
        return self.client.search_city(keyword)

    def _get_location_id(self, city):
        if city in self._city_cache:
            return self._city_cache[city]
        results = self.client.search_city(city)
        if not results:
            raise ValueError(f"未找到城市: {city}")
        loc_id = results[0]["id"]
        self._city_cache[city] = loc_id
        return loc_id

    def get_real_time(self, city):
        if not city:
            raise ValueError("城市不能为空")
        loc_id = self._get_location_id(city)
        data = self.client.get_now(loc_id)
        data["city"] = city
        return data

    def get_forecast(self, city, days=7):
        if not city:
            raise ValueError("城市不能为空")
        loc_id = self._get_location_id(city)
        return self.client.get_forecast(loc_id, days)

    def get_life_index(self, city):
        if not city:
            raise ValueError("城市不能为空")
        loc_id = self._get_location_id(city)
        return self.client.get_life_index(loc_id)
