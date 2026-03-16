
import redis
import os
import orjson
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

logger = logging.getLogger("redis")

REDIS_URL = os.getenv("REDIS_URL")

class RedisManager:

    def __init__(self):
        self.client = redis.from_url(
            REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=30,
            socket_timeout=30,
            retry_on_timeout=True,
        )

    def _serialize(self, data):
        return orjson.dumps(data)

    def _deserialize(self, data):
        if data:
            return orjson.loads(data)
        return None


    def _debug_log_cache(self, key, value, ttl):
        """
        Debug function to store Redis cache operations into a JSON file.
        This helps inspect what data is being cached.
        """
        try:
            record = {
                "key": key,
                "ttl": ttl,
                "value": value
            }
         
            with open("redis_debug.log", "ab") as f:
                f.write(orjson.dumps(record))
                f.write(b"\n")
        except Exception as e:
            logger.warning(f"Redis debug log failed: {e}")


    def set(self, key, value, ttl=None):
        try:
            data = self._serialize(value)

            if ttl:
                self.client.setex(key, ttl, data)
            else:
                self.client.set(key, data)
            self._debug_log_cache(key, value, ttl)

        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")

    def get(self, key):
        try:
            data = self.client.get(key)
            if data:
                logger.info(f"[REDIS] cache hit → {key}")
            return self._deserialize(data)

        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    def set_farm_context(self, plot_id, context):
        self.set(f"farm_context:{plot_id}", context, ttl=86400)

    def get_farm_context(self, plot_id):
        return self.get(f"farm_context:{plot_id}")

    def set_plot_status(self, plot_id, status):
        self.client.set(f"plot_status:{plot_id}", status)

    def get_plot_status(self, plot_id):
        status = self.client.get(f"plot_status:{plot_id}")
        if status:
            return status.decode()
        return None

    def get_plot_cached_data(self, plot_id):

        today = datetime.now().strftime("%Y-%m-%d")
        start_7_days = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        keys = {
            # ---------- SOIL ----------
            "soil_analysis": f"soil_analysis_{plot_id}_{today}",
            "npk_requirements": f"npk_requirements_{plot_id}_{today}",
            "npk_analysis": f"npk_analysis_{plot_id}_{today}_7",

            # ---------- WEATHER ----------
            "current_weather": f"current_weather_{plot_id}",
            "weather_forecast": f"weather_forecast_{plot_id}",

            # ---------- EVENTS ----------
            "stress": f"stress_{plot_id}",
            "harvest_status": f"harvest_status_{plot_id}",
            "agro_stats": f"agro_stats_{plot_id}_{today}",

            # ---------- INDICES ----------
            "indices": f"indices_{plot_id}_None_{today}",

            # ---------- IRRIGATION ----------
            "et": f"et_{plot_id}_{start_7_days}_{today}",
            "soil_moisture_timeseries": f"field_soil_moisture_{plot_id}",

            # ---------- MAP DATA ----------
            "soil_moisture_map": f"soil_moisture_map_{plot_id}_{today}",
            "water_uptake_map": f"water_uptake_map_{plot_id}_{today}",
            "pest_map": f"pest_map_{plot_id}_{today}",
            "growth_map": f"growth_map_{plot_id}_{today}",
            "pest_detection": f"pest_detection_{plot_id}_{today}_7",
        }

        # Faster Redis fetch
        values = self.client.mget(keys.values())

        return {
            k: self._deserialize(v) if v else None
            for k, v in zip(keys.keys(), values)
        }

redis_manager = RedisManager()