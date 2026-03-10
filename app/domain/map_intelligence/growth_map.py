# domain/map_intelligence/growth_map.py

class GrowthMap:
    """
    Handles satellite-based crop growth map
    """
    async def fetch(self, cached_data) -> dict:

        data = cached_data.get("growth_map")
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
                "weak": pixel.get("weak_pixel_percentage"),
                "stress": pixel.get("stress_pixel_percentage"),
                "moderate": pixel.get("moderate_pixel_percentage"),
                "healthy": pixel.get("healthy_pixel_percentage"),
            },
            "map_layer": {
                "tile_url": properties.get("tile_url")
            }
        }
