#domain/map_intelligence/soil_moisture_map.py

# from app.services.api_service import get_api_service

class SoilMoistureMap:
    """
    Handles homepage vertical soil moisture map (satellite-based)
    """

    # def __init__(self, auth_token=None):
    #     # self.api = get_api_service(auth_token)

    async def fetch(self, cached_data) -> dict:
        data = cached_data.get("soil_moisture_map")

        if not data or "error" in data:
            return {}

        pixel = data.get("pixel_summary", {})
        features = data.get("features", [])

        if not features:
            print("[SOIL MOISTURE MAP] No features found")
            return {}

        feature = features[0]
        properties = feature.get("properties", {})

        return {
            "classification": {
                "less": pixel.get("less_pixel_percentage"),
                "adequate": pixel.get("adequate_pixel_percentage"),
                "excellent": pixel.get("excellent_pixel_percentage"),
                "excess": pixel.get("excess_pixel_percentage"),
                "shallow": pixel.get("shallow_water_pixel_percentage"),
            },
            "map_layer": {
                "tile_url": properties.get("tile_url")
            }
        }
