#app/domain/dashboard/indices.py    
from collections import defaultdict
from datetime import datetime
from statistics import mean

class FieldIndices:

    INDEX_RANGES = {
        "water": {"good": (0.4, 0.8), "bad": (-0.75, -0.3)},
        "moisture": {"good": (-0.25, 0.8), "bad": (-0.75, -0.6)},
        "growth": {"good": (0.2, 0.8), "bad": (-0.75, 0.15)},
        "stress": {"good": (0.35, 0.8), "bad": (-0.75, 0.2)},
    }

    def _status(self, value, key):
        if value is None:
            return "unknown"

        good_min, good_max = self.INDEX_RANGES[key]["good"]
        bad_min, bad_max = self.INDEX_RANGES[key]["bad"]

        if good_min <= value <= good_max:
            return "good"
        if bad_min <= value <= bad_max:
            return "bad"
        return "moderate"

    def _aggregate(self, data, period):

        if period == "daily":
            return data[-2:] if len(data) >= 2 else data

        grouped = defaultdict(list)

        for item in data:
            dt = datetime.fromisoformat(item["date"])

            if period == "weekly":
                key = f"{dt.year}-W{dt.isocalendar()[1]}"
            elif period == "monthly":
                key = f"{dt.year}-{dt.month:02d}"
            elif period == "yearly":
                key = str(dt.year)
            else:
                key = item["date"]

            grouped[key].append(item)

        result = []

        for key, items in grouped.items():
            result.append({
                "date": key,
                "growth": mean([i["growth"] for i in items]),
                "stress": mean([i["stress"] for i in items]),
                "water": mean([i["water"] for i in items]),
                "moisture": mean([i["moisture"] for i in items]),
            })

        return sorted(result, key=lambda x: x["date"])

    async def fetch(self, cached: dict, period="weekly"):

        raw = cached.get("indices")

        if not raw:
            return {}

        aggregated = self._aggregate(raw, period)

        analysis = []

        for row in aggregated:

            entry = {
                "date": row["date"]
            }

            for key in ["growth", "stress", "water", "moisture"]:
                value = row.get(key)
                entry[key] = {
                    "value": round(value, 4),
                    "status": self._status(value, key)
                }

            analysis.append(entry)

        critical_events = []

        for row in analysis:
            for key in ["growth", "stress", "water", "moisture"]:
                if row[key]["status"] == "bad":
                    critical_events.append({
                        "date": row["date"],
                        "index": key,
                        "value": row[key]["value"]
                    })

        return {
            "period": period,
            "series": analysis,
            "critical_events": critical_events
        }