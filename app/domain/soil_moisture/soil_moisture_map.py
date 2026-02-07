# # domain/soil_moisture/soil_moisture_map.py

# from app.services.api_service import get_api_service

# class SatelliteSoilMoisture:
#     """
#     Handles homepage vertical soil moisture map (satellite-based)
#     """

#     def __init__(self, auth_token=None):
#         self.api = get_api_service(auth_token)

#     async def fetch(self, plot_id: str) -> dict:
#         data = await self.api.get_soil_moisture_map(plot_id)

#         pixel = data.get("pixel_summary", {})
#         feature = data.get("features", [{}])[0]
#         properties = feature.get("properties", {})

#         return {
#             "classification": {
#                 "less": pixel.get("less_pixel_percentage"),
#                 "adequate": pixel.get("adequate_pixel_percentage"),
#                 "excellent": pixel.get("excellent_pixel_percentage"),
#                 "excess": pixel.get("excess_pixel_percentage"),
#                 "shallow": pixel.get("shallow_water_pixel_percentage"),
#             },
#             "map_layer": {
#                 "geojson": data.get("geojson"),
#                 "raster_url": properties.get("raster_url")
#             },
#             "metadata": {
#                 "sensor": pixel.get("sensor_used"),
#                 "latest_image_date": pixel.get("latest_image_date"),
#                 "pixel_count": pixel.get("total_pixel_count")
#             }
#         }
