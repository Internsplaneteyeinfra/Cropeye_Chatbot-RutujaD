# app/domain/weather/current.py

from app.services.api_service import get_api_service

class CurrentWeather:
    def __init__(self, auth_token=None):
        self.api = get_api_service(auth_token)

    @staticmethod
    def _comfort_level(temp_c: float) -> str:
        if temp_c < 15:
            return "Cold"
        if temp_c < 25:
            return "Pleasant"
        if temp_c < 30:
            return "Warm"
        return "Hot"

    async def fetch(self, plot_id: str, lat: float, lon: float) -> dict:
        """
        Fetch current weather for marquee & irrigation cards
        """
        data = await self.api.get_current_weather(plot_id, lat, lon)

        if "error" in data:
            return data

        temperature = float(data.get("temperature_c", 0))

        return {
            "location": data.get("location"),
            "temperature_c": temperature,
            "humidity": data.get("humidity"),
            "wind_kph": data.get("wind_kph"),
            "comfort_level": self._comfort_level(temperature)
        }
