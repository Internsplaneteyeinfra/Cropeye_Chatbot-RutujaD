def get_cached_or_fail(cached: dict, key: str):
    data = cached.get(key)

    if not data or (isinstance(data, dict) and data.get("status") == "failed"):
        return {"message": "This data is currently unavailable for this plot."}

    return data