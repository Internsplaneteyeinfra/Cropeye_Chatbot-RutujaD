import redis
import json
from datetime import datetime
# ----------------------------
# Redis connection (Memurai)
# ----------------------------
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# ----------------------------
# Short-term memory settings
# ----------------------------
TTL = 900        # 15 minutes
MAX_MSG = 5      # store last 5 messages only

# ----------------------------
# Helper functions
# ----------------------------
def _key(user_id, plot_id):
    return f"chatmem:{user_id!s}:{plot_id!s}"

def get_memory(user_id, plot_id):
    data = redis_client.get(_key(user_id, plot_id))
    if not data:
        return []
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return []

def save_message(user_id, plot_id, role, message):
    memory = get_memory(user_id, plot_id)

    memory.append({
        "role": role,
        "message": message
    })

    # keep only last N messages
    memory = memory[-MAX_MSG:]

    redis_client.setex(
        _key(user_id, plot_id),
        TTL,
        json.dumps(memory)
    )
