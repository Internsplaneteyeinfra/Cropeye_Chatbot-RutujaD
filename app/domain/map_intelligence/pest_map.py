#domain/map_intelligence/water_uptake_map.py

from app.services.api_service import get_api_service

class PestDetectionMap:
    def __init__(self, auth_token=None):
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id: str) -> dict:
        data = await self.api.get_water_uptake_map(plot_id)

        pixel = data.get("pixel_summary", {})
        feature = data.get("features", [{}])[0]
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
