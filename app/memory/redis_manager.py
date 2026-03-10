
# import redis
# import json
# import os
# import logging
# from datetime import datetime
# from dotenv import load_dotenv
# from app.utils.timer import timer

# load_dotenv()

# logger = logging.getLogger("redis")
# REDIS_URL = os.getenv("REDIS_URL")

# if not REDIS_URL:
#     raise ValueError("REDIS_URL not set in environment variables")

# class RedisManager:

#     def __init__(self):
#         try:
#             self.client = redis.from_url(
#                 REDIS_URL,
#                 decode_responses=True,
#                 socket_connect_timeout=15,
#                 socket_timeout=30,
#                 retry_on_timeout=True,
#                 health_check_interval=30
#             )

#             self.client.ping()
#             logger.info("✅ Redis connected")

#         except Exception as e:
#             logger.error("❌ Redis connection failed")
#             raise e

#     def _serialize(self, value):
#         return json.dumps(value)

#     def _deserialize(self, value):
#         return json.loads(value) if value else None

#     def _debug_log_cache(self, key, value, ttl):
#         try:
#             record = {
#                 "key": key,
#                 "value": value,
#                 "ttl": ttl,
#                 "time": datetime.now().isoformat()
#             }
#             file = "cache_debug.json"
#             if os.path.exists(file):
#                 with open(file, "r") as f:
#                     data = json.load(f) 
#             else:
#                 data = []

#             data = {r["key"]: r for r in data} if isinstance(data, list) else data
#             data[key] = record

#             with open(file, "w") as f:
#                 json.dump(data, f, indent=2)

#         except Exception as e:
#             logger.warning(f"Debug file write failed: {e}")

#     def set(self, key, value, ttl=None):
#         try:
#             if ttl:
#                 self.client.setex(key, ttl, self._serialize(value))
#             else:
#                 self.client.set(key, self._serialize(value))
#             # ---------- DISABLE DEBUG LOGGING FOR PERFORMANCE ----------
#             self._debug_log_cache(key, value, ttl)

#         except Exception as e:
#             logger.warning(f"Redis SET failed: {e}")

#     def get(self, key):
#         try:
#             data = self.client.get(key)

#             if data:
#                 print(f"[REDIS] Returning cached data for {key}")
#                 return self._deserialize(data)

#             return None

#         except Exception as e:
#             logger.warning(f"Redis GET failed: {e}")
#             return None

#     def delete(self, key):
#         try:
#             self.client.delete(key)
#         except Exception as e:
#             logger.warning(f"Redis DELETE failed: {e}")


#     def exists(self, key):
#         try:
#             return self.client.exists(key) == 1
#         except:
#             return False

#     def set_plot(self, plot_id, data, ttl=86400):
#         self.set(f"plot:{plot_id}", data, ttl)


#     def get_plot(self, plot_id):
#         return self.get(f"plot:{plot_id}")

#     def set_plot_status(self, plot_id, status):
#         self.set(f"plot_status:{plot_id}", status)

#     def get_plot_status(self, plot_id):
#         return self.get(f"plot_status:{plot_id}")

#     def _chat_key(self, user_id, plot_id):
#         return f"chatmemory:{user_id}:{plot_id}"

#     def get_memory(self, user_id, plot_id):
#         data = self.get(self._chat_key(user_id, plot_id))
#         return data if data else []

#     def save_message(self, user_id, plot_id, role, message,
#                      ttl=900, max_msg=5):

#         memory = self.get_memory(user_id, plot_id)
#         memory.append({
#             "role": role,
#             "message": message
#         })
#         memory = memory[-max_msg:]

#         self.set(
#             self._chat_key(user_id, plot_id),
#             memory,
#             ttl
#         )

# redis_manager = RedisManager()


import redis
import os
import orjson
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("redis")

REDIS_URL = os.getenv("REDIS_URL")

class RedisManager:

    def __init__(self):
        self.client = redis.from_url(
            REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=10,
            socket_timeout=10,
        )

    # -------------------------------
    # Serialization (FAST)
    # -------------------------------

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
                # f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
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
            # ---------- DISABLE DEBUG LOGGING FOR PERFORMANCE ----------
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

    def set_plot_section(self, plot_id, section, data, ttl=86400):
        key = f"plot:{plot_id}:{section}"
        self.set(key, data, ttl)

    def get_plot_section(self, plot_id, section):
        key = f"plot:{plot_id}:{section}"
        return self.get(key)

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

    def get_all_plot_sections(self, plot_id):
        keys = self.client.keys(f"plot:{plot_id}:*")
        if not keys:
            return {}
        values = self.client.mget(keys)
        data = {}
        for key, value in zip(keys, values):
            section = key.decode().split(":")[-1]
            if value:
                data[section] = self._deserialize(value)

        return data
   
    def chat_key(self, user_id, plot_id):
        return f"chat:{user_id}:{plot_id}"

    def save_message(self, user_id, plot_id, role, message):

        key = self.chat_key(user_id, plot_id)

        entry = orjson.dumps({
            "role": role,
            "message": message
        })

        self.client.lpush(key, entry)

        # keep only last 5 messages
        self.client.ltrim(key, 0, 4)

        # expire memory
        self.client.expire(key, 900)

    def get_memory(self, user_id, plot_id):

        key = self.chat_key(user_id, plot_id)

        items = self.client.lrange(key, 0, 4)

        memory = []

        for item in items:
            memory.append(orjson.loads(item))

        return memory


redis_manager = RedisManager()