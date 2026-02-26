class FieldIndices:

    INDEX_RANGES = {
        "water": {"good": (0.4, 0.8), "bad": (-0.75, -0.3), "api": "NDWI"},
        "moisture": {"good": (-0.25, 0.8), "bad": (-0.75, -0.6), "api": "NDRE"},
        "growth": {"good": (0.2, 0.8), "bad": (-0.75, 0.15), "api": "NDVI"},
        "stress": {"good": (0.35, 0.8), "bad": (-0.75, 0.2), "api": "NDMI"},
    }

    def _status(self, value: float, key: str) -> str:
        if value is None:
            return "unknown"

        r = self.INDEX_RANGES[key]

        if r["good"][0] <= value <= r["good"][1]:
            return "good"

        if r["bad"][0] <= value <= r["bad"][1]:
            return "bad"

        return "moderate"

    async def fetch(self, cached: dict):

        data = cached.get("indices")

        if not data:
            return {}

        latest = data[-1]

        result = {}

        for key, meta in self.INDEX_RANGES.items():

            val = latest.get(meta["api"])

            result[key] = {
                "value": val,
                "status": self._status(val, key),
                "good_range": meta["good"],
                "bad_range": meta["bad"],
                "index_name": meta["api"]
            }

        result["date"] = latest.get("date")

        return result