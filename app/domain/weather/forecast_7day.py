# app/domain/weather/forecast.py

from app.services.api_service import get_api_service


class WeatherForecast:
    def __init__(self, auth_token=None):
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id: str, lat: float, lon: float) -> dict:
        """
        Fetch 7-day forecast starting from tomorrow
        """
        response = await self.api.get_weather_forecast(plot_id, lat, lon)

        if "error" in response:
            return response

        forecast = []

        for day in response.get("data", []):
            forecast.append({
                "date": day.get("date"),
                "temperature_max": self._parse_value(day.get("temperature_max")),
                "rainfall_mm": self._parse_value(day.get("precipitation")),
                "wind_kph": self._parse_value(day.get("wind_speed_max")),
                "humidity": self._parse_value(day.get("humidity_max"))
            })

        return {
            "source": response.get("source"),
            "days": forecast
        }

    @staticmethod
    def _parse_value(value: str) -> float:
        """
        Converts '28.9 °C' / '14.2 km/h' / '0.0 mm' → float
        """
        if not value:
            return 0.0
        return float(value.split()[0])
