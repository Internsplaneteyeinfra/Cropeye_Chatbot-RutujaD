# app/domain/weather/current.py

class CurrentWeather:

    @staticmethod
    def _comfort_level(temp_c: float) -> str:
        if temp_c < 15:
            return "Cold"
        if temp_c < 25:
            return "Pleasant"
        if temp_c < 30:
            return "Warm"
        return "Hot"

    async def fetch(self, plot_id: str, lat: float, lon: float, cached: dict) -> dict:
        """
        Fetch current weather for marquee & irrigation cards
        """
        data = cached.get("current_weather", {})

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
