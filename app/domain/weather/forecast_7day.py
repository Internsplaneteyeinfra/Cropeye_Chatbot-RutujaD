# app/domain/weather/forecast.py

class WeatherForecast:

    def __init__(self):
        pass

    async def fetch(self, plot_id: str, cached: dict) -> dict:
        """
        Fetch 7-day forecast from CACHE instead of API
        """

        forecast_data = cached.get("weather_forecast", {})

        if not forecast_data:
            return {"error": "Weather forecast not available"}

        forecast = []

        for day in forecast_data.get("data", []):

            forecast.append({
                "date": day.get("date"),
                "temperature_max": self._parse_value(day.get("temperature_max")),
                "rainfall_mm": self._parse_value(day.get("precipitation")),
                "wind_kph": self._parse_value(day.get("wind_speed_max")),
                "humidity": self._parse_value(day.get("humidity_max"))
            })

        return {
            "source": forecast_data.get("source"),
            "days": forecast
        }

    @staticmethod
    def _parse_value(value):
        """
        Converts values like:
        '28.9 °C'
        '14.2 km/h'
        '0.0 mm'
        → float
        """

        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(str(value).split()[0])
        except:
            return 0.0