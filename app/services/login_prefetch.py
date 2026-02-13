import asyncio
from app.services.api_service import get_api_service

async def prefetch_login_data(
    user_id: str,
    plot_id: str,
    auth_token: str
) -> dict:
    """
    Call ALL required APIs at login time.
    Store results in a single prefetched object.
    """

    api = get_api_service(auth_token)

    tasks = {
        "farmer_profile": api.get_farmer_profile(user_id),
        "soil_analysis": api.get_soil_analysis(plot_id),
        "soil_moisture": api.get_soil_moisture_timeseries(plot_id),
        "current_weather": api.get_current_weather(plot_id),
        "pest_detection": api.get_pest_detection(plot_id),
    }

    # 🔥 Parallel API calls
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    prefetched = {}
    for key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            prefetched[key] = {"error": str(result)}
        else:
            prefetched[key] = result

    return prefetched
