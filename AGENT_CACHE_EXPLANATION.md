# Agent Cache Usage Explanation

## The Key Distinction

**ALL agents use cached data**, but they access it in **two different ways**:

---

## Type 1: Direct Cache Access (No API Calls)

These agents read **directly** from the `cached_data` dictionary in the context:

### Example: Map Agent
```python
async def map_agent(state: dict) -> dict:
    context = state.get("context", {})
    cached = context.get("cached_data", {})  # ← Reads directly from context
    
    # No API calls - just reads from cached_data
    analysis["map"]["soil_moisture"] = get_cached("soil_moisture_map")
    return state
```

**Agents using this approach:**
- ✅ **Map Agent** - Reads `cached.get("soil_moisture_map")`, `cached.get("growth_map")`, etc.
- ✅ **Dashboard Agent** - Reads `cached.get("agro")`, `cached.get("harvest")`, etc.
- ✅ **Fertilizer Agent** - Reads `cached.get("npk_requirements")`

**Flow:**
```
Agent → context["cached_data"] → Returns data
(No API service calls, no Redis checks during chat)
```

---

## Type 2: Indirect Cache Access (Through API Service)

These agents call domain classes/API methods, which **then check Redis cache** before making API calls:

### Example: Weather Agent
```python
async def weather_agent(state: dict) -> dict:
    current = CurrentWeather(auth_token)
    # Calls domain class method
    analysis["weather"]["current_weather"] = await current.fetch(plot_id, lat, lon)
    return state
```

**What happens inside `current.fetch()`:**
```python
# In app/domain/weather/current_weather.py
async def fetch(self, plot_id: str, lat: float, lon: float):
    # Calls API service method
    data = await self.api.get_current_weather(plot_id, lat, lon)
    return data
```

**What happens inside `api.get_current_weather()`:**
```python
# In app/services/api_service.py
async def get_current_weather(self, plot_id: str, lat: float, lon: float):
    cache_key = f"current_weather_{plot_id}"
    
    # ✅ CHECKS REDIS CACHE FIRST
    cached = redis_manager.get(cache_key)
    if cached:
        return cached  # ← Returns cached data
    
    # Only makes API call if cache miss
    response = await self.client.get(url, ...)
    data = response.json()
    redis_manager.set(cache_key, data, ttl=7200)
    return data
```

**Agents using this approach:**
- ⚠️ **Weather Agent** - Calls `CurrentWeather.fetch()` → `api.get_current_weather()` → checks Redis cache
- ⚠️ **Irrigation Agent** - Calls `IrrigationStatus.build()` → `api.get_evapotranspiration()` → checks Redis cache
- ⚠️ **Soil Moisture Agent** - Calls `IrrigationSoilMoisture.build()` → `api.get_soil_moisture_timeseries()` → checks Redis cache
- ⚠️ **Soil Analysis Agent** - Calls `api.get_soil_analysis()` → checks Redis cache
- ⚠️ **Pest Agent** - Calls `api.get_pest_detection()` → checks Redis cache

**Flow:**
```
Agent → Domain Class → API Service → Redis Cache Check → Returns cached data (or API if miss)
```

---

## Why Both Approaches Work

### Both Use Cached Data During Chat:

1. **Type 1 (Direct)**: 
   - Data was already loaded into `context["cached_data"]` from Redis during `/chat` endpoint
   - Agent just reads from this dictionary
   - ✅ **Fastest** - no function calls, no Redis queries

2. **Type 2 (Indirect)**:
   - Agent calls API service method
   - API service checks Redis cache first
   - Returns cached data if available
   - ✅ **Still uses cache** - just goes through an extra layer

### The Important Point:

**During chat requests, both approaches return cached data** because:
- Type 1: Reads from `cached_data` which was populated from Redis
- Type 2: API service methods check Redis cache first and return cached data

---

## Visual Comparison

### Type 1: Direct Access
```
/chat endpoint
    ↓
Loads cached_data from Redis → context["cached_data"] = {...}
    ↓
Map Agent reads: cached.get("soil_moisture_map")
    ↓
Returns data (from context, already cached)
```

### Type 2: Indirect Access
```
/chat endpoint
    ↓
Weather Agent calls: current.fetch()
    ↓
Domain class calls: api.get_current_weather()
    ↓
API service checks: redis_manager.get("current_weather_162_1")
    ↓
Returns cached data (from Redis)
```

---

## Summary

| Approach | Agent Examples | Cache Access | API Calls During Chat? |
|----------|---------------|--------------|------------------------|
| **Direct** | Map, Dashboard, Fertilizer | Reads from `context["cached_data"]` | ❌ No |
| **Indirect** | Weather, Irrigation, Soil | Calls API service → checks Redis | ⚠️ Only if cache miss/expired |

**Both use cached data** - the difference is just the **path** they take to get it!
