# Cache vs API Call Analysis

## 🎯 Direct Answer to Your Question

**Q: Does the chatbot use cache data or direct API call data?**

**A: The chatbot uses CACHED DATA during chat requests.**

### Evidence:
1. ✅ **Terminal logs show cache hits**: `[REDIS] Returning cached data for...`
2. ✅ **All API methods check cache first** before making API calls
3. ✅ **Most agents read directly from `cached_data`** in context
4. ⚠️ **The `_source: "api"` tag is misleading** - it means "originally from API" not "currently from API"

### When API Calls Happen:
- **During `/initialize-plot`**: API calls are made (if cache miss) and results are stored in Redis
- **During `/chat`**: Data is retrieved from Redis cache (unless cache expired or missing)

---

## Summary
**The chatbot uses CACHED DATA, not direct API calls during chat requests.**

The `_source: "api"` tag in the response is **misleading** - it indicates the data originally came from an API, but it's actually being served from Redis cache during chat requests.

---

## Data Flow Architecture

### Phase 1: Initialization (`/initialize-plot`)

When `/initialize-plot` is called:

1. **Location**: `app/main.py` → `run_initialization()` function (lines 63-152)

2. **Process**:
   ```python
   # All API methods are called in parallel
   tasks = {
       "soil_analysis": api.get_soil_analysis(plot_id, today),
       "weather_forecast": api.get_weather_forecast(plot_id, lat, lon),
       "current_weather": api.get_current_weather(plot_id, lat, lon),
       # ... etc
   }
   ```

3. **Each API Method** (in `app/services/api_service.py`):
   - **First checks Redis cache**:
     ```python
     cache_key = f"weather_forecast_{plot_id}"
     cached = redis_manager.get(cache_key)
     if cached:
         return cached  # ← Returns cached data if available
     ```
   
   - **If cache miss, makes API call**:
     ```python
     response = await self.client.get(url, ...)
     data = response.json()
     data["_source"] = "api"  # ← Tags as API source
     redis_manager.set(cache_key, data, ttl=7200)  # ← Stores in cache
     return data
     ```

4. **Final Storage**:
   - All results are stored in Redis under key: `plot:{plot_id}`
   - Each result has `_source: "api"` tag added (line 129 in `main.py`)
   - Status set to `"ready"` when complete

---

### Phase 2: Chat Request (`/chat`)

When `/chat` is called:

1. **Location**: `app/main.py` → `chat()` function (lines 282-366)

2. **Process**:
   ```python
   # Retrieves entire cached data dictionary
   cached = redis_manager.get_plot(plot_id)  # ← Gets from Redis
   state["context"]["cached_data"] = cached  # ← Passes to agents
   ```

3. **Agents Use Cached Data**:
   - **Weather Agent** (`app/agents/weather_agent.py`):
     ```python
     # ❌ OLD CODE (commented out) - Would make API calls
     # analysis["weather"]["current_weather"] = await current.fetch(...)
     
     # ✅ CURRENT CODE - Uses cached data from context
     cached = context.get("cached_data", {})
     # Agents read from cached_data, not making new API calls
     ```
   
   - **Map Agent** (`app/agents/map_agent.py`):
     ```python
     cached = context.get("cached_data", {})
     analysis["map"]["soil_moisture"] = get_cached("soil_moisture_map")
     # ← Directly uses cached data
     ```
   
   - **Dashboard Agent** (`app/agents/dashboard_agent.py`):
     ```python
     cached = context.get("cached_data", {})
     analysis["dashboard"]["crop"] = get_cached_or_fail(cached, "agro")
     # ← Directly uses cached data
     ```

---

## Evidence from Your Terminal Output

```
[REDIS] Returning cached data for chatmemory:0:162_1
[REDIS] Returning cached data for farmer_profile_default
[REDIS] Returning cached data for current_weather_162_1        ← CACHE HIT
[CURRENT WEATHER] Returning cached data for 162_1              ← CACHE HIT
[REDIS] Returning cached data for weather_forecast_162_1       ← CACHE HIT
```

**This confirms**: The system is using cached data, not making API calls.

---

## The Confusion: `_source: "api"` Tag

### Why It's Misleading

1. **During Initialization**:
   - When data is fetched from API, it's tagged with `_source: "api"` (line 129 in `main.py`)
   - This tag is stored in Redis along with the data

2. **During Chat**:
   - The cached data (with `_source: "api"` tag) is retrieved from Redis
   - The tag remains in the response, making it **look like** fresh API data
   - But it's actually **cached data** from Redis

### The Tag Doesn't Indicate Current Source

- `_source: "api"` means: "This data originally came from an API call"
- It does **NOT** mean: "This data was just fetched from an API"

---

## Cache TTL (Time To Live)

Different data types have different cache expiration times:

| Data Type | TTL | Location |
|-----------|-----|----------|
| Weather Forecast | 7200s (2 hours) | `api_service.py:646` |
| Current Weather | 7200s (2 hours) | `api_service.py:612` |
| Soil Analysis | 43200s (12 hours) | `api_service.py:219` |
| Maps (Growth, Pest, etc.) | 43200s (12 hours) | `api_service.py:371, 400, 429, 461` |
| NPK Requirements | 43200s (12 hours) | `api_service.py:293` |
| Farmer Profile | 3600s (1 hour) | `api_service.py:75` |

---

## How to Verify Cache vs API

### Method 1: Check Terminal Logs
- **Cache Hit**: `[REDIS] Returning cached data for {key}`
- **API Call**: `[API SERVICE] Making API call to {url}` or HTTP request logs

### Method 2: Check Redis Directly
```python
# In your code, add:
from app.memory.redis_manager import redis_manager
cached = redis_manager.get_plot(plot_id)
print(f"Cache exists: {cached is not None}")
```

### Method 3: Add Source Tracking
Modify `api_service.py` to track actual source:
```python
# When returning cached data:
if cached:
    cached["_actual_source"] = "cache"  # ← Add this
    cached["_cached_at"] = datetime.now().isoformat()
    return cached

# When making API call:
data["_actual_source"] = "api"  # ← Add this
data["_api_called_at"] = datetime.now().isoformat()
return data
```

---

## Agent Behavior Analysis

### Agents That Use Cached Data Directly

These agents read from `context["cached_data"]` without making API calls:

1. **Map Agent** (`app/agents/map_agent.py`):
   - Uses: `cached.get("soil_moisture_map")`, `cached.get("growth_map")`, etc.
   - ✅ **No API calls during chat**

2. **Dashboard Agent** (`app/agents/dashboard_agent.py`):
   - Uses: `get_cached_or_fail(cached, "agro")`, `get_cached_or_fail(cached, "harvest")`
   - ✅ **No API calls during chat**

3. **Fertilizer Agent** (`app/agents/fertilizer_agent.py`):
   - Uses: `get_cached_or_fail(cached, "npk_requirements")`
   - ✅ **No API calls during chat** (lines 117-118)

### Agents That Make API Calls (But Still Use Cache)

These agents call domain classes/API service, which **automatically check cache first**:

1. **Weather Agent** (`app/agents/weather_agent.py`):
   - Calls: `CurrentWeather.fetch()` → `api.get_current_weather()` → **checks Redis cache first**
   - Calls: `WeatherForecast.fetch()` → `api.get_weather_forecast()` → **checks Redis cache first**
   - ✅ **Uses cache if available, API only if cache miss**

2. **Irrigation Agent** (`app/agents/irrigation_agent.py`):
   - Calls: `IrrigationStatus.build()` → `api.get_current_weather()`, `api.get_evapotranspiration()` → **checks Redis cache first**
   - Calls: `IrrigationSchedule.build()` → `api.get_weather_forecast()`, `api.get_evapotranspiration()` → **checks Redis cache first**
   - ✅ **Uses cache if available, API only if cache miss**

3. **Soil Moisture Agent** (`app/agents/soil_moisture_agent.py`):
   - Calls: `IrrigationSoilMoisture.build()` → `api.get_soil_moisture_timeseries()` → **checks Redis cache first**
   - ✅ **Uses cache if available, API only if cache miss**

4. **Soil Analysis Agent** (`app/agents/soil_analysis_agent.py`):
   - Calls: `api.get_soil_analysis()`, `api.get_npk_requirements()` → **checks Redis cache first**
   - ⚠️ **Note**: This agent makes API calls even during chat, but they go through cache layer
   - ✅ **Uses cache if available, API only if cache miss**

5. **Pest Agent** (`app/agents/pest_agent.py`):
   - Calls: `api.get_current_weather()`, `api.get_pest_detection()`, `api.get_farmer_profile()` → **checks Redis cache first**
   - ✅ **Uses cache if available, API only if cache miss**

### Key Insight: All API Calls Go Through Cache Layer

**Every API method in `api_service.py` follows this pattern:**

```python
async def get_weather_forecast(self, plot_id: str, lat: float, lon: float):
    cache_key = f"weather_forecast_{plot_id}"
    
    cached = redis_manager.get(cache_key)  # ← CHECK CACHE FIRST
    if cached:
        return cached  # ← RETURN CACHED DATA
    
    # Only makes API call if cache miss
    response = await self.client.get(url, ...)
    data = response.json()
    redis_manager.set(cache_key, data, ttl=7200)  # ← STORE IN CACHE
    return data
```

**This means**: Even agents that appear to make "direct API calls" are actually using the cache layer, so they benefit from cached data during chat requests.

---

## Current Behavior Summary

| Phase | Data Source | `_source` Tag | Makes API Call? |
|-------|-------------|---------------|-----------------|
| **Initialization** | API (if cache miss) or Cache (if cache hit) | `"api"` | ✅ Yes (if cache miss) |
| **Chat Request** | **Cache (primary)** or API (if cache miss/expired) | `"api"` (misleading) | ⚠️ Only if cache miss/expired |

---

## Recommendations

### 1. Fix the Misleading Tag
Update `main.py` line 129 to track actual source:
```python
# Instead of always setting "_source": "api"
if isinstance(data, dict):
    # Check if it came from cache or API
    if data.get("_from_cache"):
        data["_source"] = "cache"
    else:
        data["_source"] = "api"
```

### 2. Add Cache Metadata
Include cache timestamp in responses:
```python
cached_data["_cached_at"] = datetime.now().isoformat()
cached_data["_cache_ttl"] = ttl
cached_data["_cache_expires_at"] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
```

### 3. Add Debug Endpoint
Create `/debug/cache-status/{plot_id}` to show:
- What's cached
- Cache age
- TTL remaining
- Last API call time

---

## Conclusion

**Your chatbot is using cached data during chat requests**, not making direct API calls. The `_source: "api"` tag is historical metadata indicating the data originally came from an API, but it doesn't reflect the current data source.

The terminal logs clearly show cache hits, confirming this behavior.
