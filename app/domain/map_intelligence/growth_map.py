# domain/map_intelligence/growth_map.py

from app.services.api_service import get_api_service


class GrowthMap:
    """
    Handles satellite-based crop growth map
    """

    def __init__(self, auth_token=None):
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id: str) -> dict:
        data = await self.api.get_growth_map(plot_id)

        if not data or "error" in data:
            return {}

        pixel = data.get("pixel_summary", {})
        features = data.get("features", [])

        if not features:
            print("[GROWTH MAP] No features found")
            return {}

        feature = features[0]
        properties = feature.get("properties", {})

        return {
            "classification": {
                "week": pixel.get("weak_pixel_percentage"),
                "stress": pixel.get("stress_pixel_percentage"),
                "moderate": pixel.get("moderate_pixel_percentage"),
                "healthy": pixel.get("healthy_pixel_percentage"),
            },
            "map_layer": {
                "tile_url": properties.get("tile_url")
            }
        }
