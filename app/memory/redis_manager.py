
import redis
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("redis")

# =========================================================
# CONNECTION
# =========================================================

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("REDIS_URL not set in environment variables")

class RedisManager:

    def __init__(self):
        try:
            self.client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )

            self.client.ping()
            logger.info("✅ Redis connected")

        except Exception as e:
            logger.error("❌ Redis connection failed")
            raise e


    # =========================================================
    # INTERNAL UTILS
    # =========================================================

    def _serialize(self, value):
        return json.dumps(value)

    def _deserialize(self, value):
        return json.loads(value) if value else None

    
    # =========================================================
    # DEBUG LOGGING
    # =========================================================
    def _debug_log_cache(self, key, value, ttl):
        try:
            record = {
                "key": key,
                "value": value,
                "ttl": ttl,
                "time": datetime.now().isoformat()
            }

            file = "cache_debug.json"

            if os.path.exists(file):
                with open(file, "r") as f:
                    data = json.load(f) 
            else:
                data = []

            data = {r["key"]: r for r in data} if isinstance(data, list) else data
            data[key] = record


            with open(file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Debug file write failed: {e}")

    # =========================================================
    # GENERIC CACHE
    # =========================================================

    def set(self, key, value, ttl=None):
        try:
            if ttl:
                self.client.setex(key, ttl, self._serialize(value))
            else:
                self.client.set(key, self._serialize(value))            
            self._debug_log_cache(key, value, ttl)

        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")


    # def get(self, key):
    #     try:
    #         return self._deserialize(self.client.get(key))
    #     except Exception as e:
    #         logger.warning(f"Redis GET failed: {e}")
    #         return None

    def get(self, key):
        try:
            data = self.client.get(key)

            if data:
                print(f"[REDIS] Returning cached data for {key}")
                return self._deserialize(data)

            return None

        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    def delete(self, key):
        try:
            self.client.delete(key)
        except Exception as e:
            logger.warning(f"Redis DELETE failed: {e}")


    def exists(self, key):
        try:
            return self.client.exists(key) == 1
        except:
            return False


    # =========================================================
    # PLOT CACHE
    # =========================================================

    def set_plot(self, plot_id, data, ttl=86400):
        self.set(f"plot:{plot_id}", data, ttl)


    def get_plot(self, plot_id):
        return self.get(f"plot:{plot_id}")

    # =========================================================
    # PLOT STATUS
    # =========================================================
    def set_plot_status(self, plot_id, status):
        self.set(f"plot_status:{plot_id}", status)

    def get_plot_status(self, plot_id):
        return self.get(f"plot_status:{plot_id}")

    # =========================================================
    # CHAT MEMORY - Conversation
    # =========================================================

    def _chat_key(self, user_id, plot_id):
        return f"chatmemory:{user_id}:{plot_id}"


    def get_memory(self, user_id, plot_id):
        data = self.get(self._chat_key(user_id, plot_id))
        return data if data else []


    def save_message(self, user_id, plot_id, role, message,
                     ttl=900, max_msg=5):

        memory = self.get_memory(user_id, plot_id)

        memory.append({
            "role": role,
            "message": message
        })

        memory = memory[-max_msg:]

        self.set(
            self._chat_key(user_id, plot_id),
            memory,
            ttl
        )


# =========================================================
# SINGLETON INSTANCE
# =========================================================

redis_manager = RedisManager()
