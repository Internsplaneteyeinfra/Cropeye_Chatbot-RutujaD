# app/domain/dashboard/recovery_rate.py

OTHER_FARMERS_RECOVERY = {
    "regional_average": 7.85,
    "top_quartile": 8.52,
    "bottom_quartile": 6.58,
    "similar_farms": 7.63
}


class RecoveryRate:

    async def fetch(self, cached):

        agro = cached.get("agro")

        if not agro:
            return {}

        recovery = agro.get("brix_sugar", {}).get("recovery", {})

        mean = recovery.get("mean")
        min_val = recovery.get("min")
        max_val = recovery.get("max")

        return {
            "your_farm": round(mean, 1) if mean else None,
            "mean": mean,
            "min": min_val,
            "max": max_val,

            "comparison": {
                "regional_avg": OTHER_FARMERS_RECOVERY["regional_average"],
                "top_quartile": OTHER_FARMERS_RECOVERY["top_quartile"],
                "similar_farms": OTHER_FARMERS_RECOVERY["similar_farms"],
                "bottom_quartile": OTHER_FARMERS_RECOVERY["bottom_quartile"]
            }
        }