#domain/map_intelligence/pest_map.py

# from app.services.api_service import get_api_service

class PestMap:
    # def __init__(self, auth_token=None):
    #     self.api = get_api_service(auth_token)

    async def fetch(self, cached_data: dict) -> dict:
        data = cached_data.get("pest_map")
        print("PEST MAP CACHE:", data)
        if not data or "error" in data:
            return {}

        pixel = data.get("pixel_summary", {})
        feature = data.get("features", [{}])[0]
        properties = feature.get("properties", {})

        return {
            "classification": {
                "chewing": pixel.get("chewing_affected_pixel_percentage"),
                "sucking": pixel.get("sucking_affected_pixel_percentage"),
                "fungi": pixel.get("fungi_affected_pixel_percentage"),
                "soil_borne": pixel.get("SoilBorn_affected_pixel_percentage"),
            },
            "map_layer": {
                "tile_url": properties.get("tile_url")
            }
        }
