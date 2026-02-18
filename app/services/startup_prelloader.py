#app/services/s

import asyncio
from app.services.api_service import get_api_service

async def safe(task):
    try:
        return await task
    except Exception as e:
        print("Preload failed:", e)


async def preload_all():

    print("🚀 Preloading APIs...")

    api = get_api_service()

    farms = await api.get_farmer_profile()

    if isinstance(farms, dict):
        print("Farm load failed — skipping preload")
        return

    tasks = []

    for farm in farms:

        plot = farm.get("plot_name")
        lat = farm.get("lat")
        lon = farm.get("lon")

        if not plot:
            continue

        tasks.extend([
            safe(api.get_soil_analysis(plot)),
            safe(api.get_npk_analysis(plot)),
            safe(api.get_soil_moisture_map(plot)),
            safe(api.get_evapotranspiration(plot)),
            safe(api.get_pest_detection(plot)),
        ])

        if lat and lon:
            tasks.append(safe(api.get_current_weather(plot, lat, lon)))
            tasks.append(safe(api.get_weather_forecast(plot, lat, lon)))

    await asyncio.gather(*tasks)

    print("✅ Preload finished")
