#domain/map_intelligence/water_uptake_map.py

# from app.services.api_service import get_api_service

class WaterUptakeMap:
    # def __init__(self, auth_token=None):
    #     self.api = get_api_service(auth_token)

    async def fetch(self, cached_data: dict) -> dict:
        data = cached_data.get("water_uptake_map")
        
        if not data or "error" in data:
            return {}
        pixel = data.get("pixel_summary", {})
        feature = data.get("features", [{}])[0]
        properties = feature.get("properties", {})

        return {
            "classification": {
                "deficient": pixel.get("deficient_pixel_percentage"),
                "less": pixel.get("less_pixel_percentage"),
                "Adequate": pixel.get("adequat_pixel_percentage"),
                "excellent": pixel.get("excellent_pixel_percentage"),
                "excess": pixel.get("excess_pixel_percentage"),
            },
            "map_layer": {
                "tile_url": properties.get("tile_url")
            }
        }
