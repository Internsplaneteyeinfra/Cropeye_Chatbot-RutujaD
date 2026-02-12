# api_service.py

"""
API Service Layer for CROPEYE Chatbot
Handles all backend API calls with caching and error handling
"""

import httpx
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()

# Base URLs
BASE_URL = os.getenv("BASE_URL", "https://cropeye-server-1.onrender.com/api")
SOIL_API_URL = os.getenv("SOIL_API_URL", "https://main-cropeye.up.railway.app")
PLOT_API_URL = os.getenv("PLOT_API_URL", "https://admin-cropeye.up.railway.app")
EVENTS_API_URL = os.getenv("EVENTS_API_URL", "https://dev-events.cropeye.ai")
FIELD_API_URL = os.getenv("FIELD_API_URL", "https://sef-cropeye.up.railway.app")
WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://weather-cropeye.up.railway.app")

# Debug: Print which URLs are being used
print(f"[API SERVICE INIT] SOIL_API_URL: {SOIL_API_URL}")
print(f"[API SERVICE INIT] PLOT_API_URL: {PLOT_API_URL}")
print(f"[API SERVICE INIT] BASE_URL: {BASE_URL}")



# Cache configuration
map_cache = TTLCache(maxsize=300, ttl=43200)  # 12 hours
soil_cache = TTLCache(maxsize=1000, ttl=43200)  # 12 hours
weather_cache = TTLCache(maxsize=500, ttl=7200)  # 2 hours
irrigation_cache = TTLCache(maxsize=500, ttl=43200)  # 12 hour
farm_context_cache = TTLCache(maxsize=100, ttl=3600)  # 12 hour
pest_cache = TTLCache(maxsize=500, ttl=43200)  # 12 hours

# yield_cache = TTLCache(maxsize=500, ttl=1800)  # 30 minutes


class APIService:
    """Centralized API service for chatbot"""
    
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if available"""
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    # ----------------------------------------------------------------

    async def get_farmer_profile(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get farmer profile with plots information
        API: GET /farms/
        """
        cache_key = f"farmer_profile_{user_id or 'default'}"
        
        if cache_key in farm_context_cache:
            return farm_context_cache[cache_key]
        
        try:
            url = f"{BASE_URL}/farms/"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            print("Backend authentication verified successfully via /farms API.")
            data = response.json()
            
            farm_context_cache[cache_key] = data
            return data
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch farmer profile: {str(e)}"}
    
    # ----------------------------------------------------------------

    async def get_soil_analysis(self, plot_name: str, date: Optional[str] = None, fe_days_back: int = 30 ) -> Dict[str, Any]:
        """
        Get complete soil analysis for a plot
        API: POST /analyze?plot_name={id}&date={date}&fe_days_back=30
        Returns: N, P, K, pH, CEC, OC, BD, Fe, SOC
        Includes metadata: _from_cache, _api_called, _cache_key
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"soil_analysis_{plot_name}_{date}"
        
        if cache_key in soil_cache:
            cached_data = soil_cache[cache_key].copy()
            cached_data["_from_cache"] = True
            cached_data["_api_called"] = False
            cached_data["_cache_key"] = cache_key
            print(f"[API SERVICE] Returning cached soil data for {plot_name} (cache_key: {cache_key})")
            return cached_data
        
        try:
            url = f"{SOIL_API_URL}/analyze"
            params = {
                "plot_name": plot_name,
                "date": date,
                "fe_days_back": fe_days_back
            }
            print(f"[API SERVICE] Making API call to {url} with params: {params}")
            response = await self.client.post(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            # Add metadata
            data["_from_cache"] = False
            data["_api_called"] = True
            data["_cache_key"] = cache_key
            
            # Store in cache (without metadata to keep cache clean)
            cache_data = {k: v for k, v in data.items() if not k.startswith("_")}
            soil_cache[cache_key] = cache_data
            
            print(f"[API SERVICE] API call successful for {plot_name}, data cached (cache_key: {cache_key})")
            return data
        except httpx.HTTPStatusError as e:
            print(f"[API SERVICE] HTTP error for {plot_name}: {e.response.status_code} - {e.response.text}")
            return {
                "error": f"HTTP {e.response.status_code}: Failed to fetch soil analysis",
                "_from_cache": False,
                "_api_called": True,
                "_cache_key": cache_key
            }
        except httpx.RequestError as e:
            print(f"[API SERVICE] Request error for {plot_name}: {str(e)}")
            return {
                "error": f"Request failed: {str(e)}",
                "_from_cache": False,
                "_api_called": True,
                "_cache_key": cache_key
            }
        except Exception as e:
            print(f"[API SERVICE] Unexpected error for {plot_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Unexpected error: {str(e)}",
                "_from_cache": False,
                "_api_called": True,
                "_cache_key": cache_key
            }

    # ----------------------------------------------------------------

    async def get_npk_requirements(
        self,
        plot_name: str,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPK requirements and fertilizer recommendations
        API: POST /required-n/{plot_name}?end_date={date}
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"npk_requirements_{plot_name}_{end_date}"
        
        if cache_key in soil_cache:
            cached_data = soil_cache[cache_key].copy()            
            return cached_data
        
        try:
            url = f"{SOIL_API_URL}/required-n/{plot_name}"
            params = {"end_date": end_date}
            response = await self.client.post(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            soil_cache[cache_key] = data
            return data
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: Failed to fetch NPK requirements"}
        except httpx.RequestError as e:
            print(f"[API SERVICE] Request error for NPK requirements {plot_name}: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            print(f"[API SERVICE] Unexpected error for NPK requirements {plot_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Unexpected error: {str(e)}"}
    
    # ----------------------------------------------------------------

    async def get_npk_analysis(
        self,
        plot_name: str,
        end_date: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get NPK analysis with time series data
        API: POST /analyze-npk/{plot_name}?end_date={date}&days_back=7
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"npk_analysis_{plot_name}_{end_date}_{days_back}"
        
        if cache_key in soil_cache:
            return soil_cache[cache_key]
        
        try:
            url = f"{SOIL_API_URL}/analyze-npk/{plot_name}"
            params = {
                "end_date": end_date,
                "days_back": days_back
            }
            response = await self.client.post(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            soil_cache[cache_key] = data
            return data
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch NPK analysis: {str(e)}"}
    

    # ==================================================
    # MAP APIs (Spatial Intelligence)
    # ==================================================

    async def get_soil_moisture_map(self, plot_name: str, end_date: str = None) -> dict:
        """
        Get satellite soil moisture map (GeoJSON / raster)
        API: POST /SoilMoisture
        """

        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"soil_moisture_map_{plot_name}_{end_date}"

        if cache_key in map_cache:
            return map_cache[cache_key]

        print(f"[SOIL MAP] plot_name={plot_name}, end_date={end_date}")

        try:
            url = f"{PLOT_API_URL}/SoilMoisture"
            params = {
                "plot_name": plot_name,
                "end_date": end_date
            }

            response = await self.client.post(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()

            map_cache[cache_key] = data
            return data

        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch soil moisture map: {str(e)}"}

    # ----------------------------------------------------------------
    
    async def get_water_uptake_map(self, plot_id: str, end_date: Optional[str] = None) -> dict:
        """
        Satellite water uptake map
        API: POST /wateruptake
        """
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        cache_key = f"water_uptake_map_{plot_id}_{end_date}"

        if cache_key in map_cache:
            return map_cache[cache_key]

        try:
            response = await self.client.post(
                f"{PLOT_API_URL}/wateruptake",
                params={"plot_name": plot_id, "end_date": end_date},
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            map_cache[cache_key] = data
            return data

        except httpx.HTTPError as e:
            return {"error": f"Water uptake map fetch failed: {str(e)}"}
   
    # ----------------------------------------------------------------
    
    async def get_growth_map(self, plot_id: str, end_date: Optional[str] = None) -> dict:
        """
        Satellite crop growth map
        API: POST /analyze_Growth
        """
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        try:
            response = await self.client.post(
                f"{PLOT_API_URL}/analyze_Growth",
                params={
                    "plot_name": plot_id,
                    "end_date": end_date
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            print("Growth Map RAW data ", data)
            
            return data

        except httpx.HTTPError as e:
            return {"error": f"Growth map fetch failed: {str(e)}"}

    # ----------------------------------------------------------------
    
    async def get_pest_detection(self, plot_id: str, end_date: Optional[str] = None, days_back: int = 7) -> dict:
        """
        Get pest detection data from API
        API: POST /pest-detection?plot_name={plot_id}&end_date={end_date}&days_back={days_back}
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"pest_detection_{plot_id}_{end_date}_{days_back}"
        
        if cache_key in pest_cache:
            return pest_cache[cache_key]
        
        try:
            # Use PLOT_API_URL for pest detection (same as other map endpoints)
            url = f"{PLOT_API_URL}/pest-detection"
            params = {
                "plot_name": plot_id,
                "end_date": end_date,
                "days_back": days_back
            }
            
            response = await self.client.post(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            pest_cache[cache_key] = data
            return data
            
        except httpx.HTTPError as e:
            return {"error": f"Pest detection fetch failed: {str(e)}"}

    # ----------------------------------------------------------------

    async def get_soil_moisture_timeseries(self, plot_name: str) -> dict:
        """
        Get soil moisture timeseries from field service
        API: GET /soil-moisture/{plot_name}
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_key = f"field_soil_moisture_{plot_name}"

        if cache_key in irrigation_cache:
            print("[FIELD API] returning cached data")
            return irrigation_cache[cache_key]

        url = f"{FIELD_API_URL}/soil-moisture/{plot_name}"  
        headers = self._get_headers()

        try:          
            response = await self.client.post(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()

            #  ✅ cache ONLY success
            if isinstance(data, list):
                irrigation_cache[cache_key] = data

            return data

        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch field soil moisture: {str(e)}"}

    # ----------------------------------------------------------------

    async def get_evapotranspiration(self, plot_id: str) -> Dict[str, Any]:
        """
        Evapotranspiration (ET) for irrigation logic
        API: GET /plots/{plot_id}/compute-et/
        """
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cache_key = f"et_{plot_id}_{start_date}_{today}"

        if cache_key in irrigation_cache:
            print("[ET CACHE HIT]")
            return irrigation_cache[cache_key]

        url = f"{FIELD_API_URL}/plots/{plot_id}/compute-et/"

        print("\n========== ET API REQUEST ==========")
        print("METHOD = POST")
        print("URL =", url)
        print("HEADERS =", self._get_headers())
        print("====================================")
        
        try:
            url = f"{FIELD_API_URL}/plots/{plot_id}/compute-et/"
            body = {
                "plot_name": plot_id,
                "start_date": start_date,
                "end_date": today,
            }
            response = await self.client.post(
                url,
                json=body,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            print("\n✅ ET FETCH SUCCESS")
            print("DATA =", data)

            irrigation_cache[cache_key] = data
            return data

        except httpx.HTTPError as e:
            return {"error": f"ET fetch failed: {str(e)}"}
        
    # ----------------------------------------------------------------

    async def get_current_weather(self, plot_id: str) -> Dict[str, Any]:
        """
        Get current weather for marquee & irrigation cards
        API: GET /current-weather?plot_id=
        """
        cache_key = f"current_weather_{plot_id}"

        if cache_key in weather_cache:
            return weather_cache[cache_key]

        try:
            url = f"{WEATHER_API_URL}/current-weather"
            params = {
                "plot_id": plot_id, 
                "lat": 19.36470605,
                "lon": 75.45908165, 
            }

            response = await self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

            weather_cache[cache_key] = data
            return data

        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch current weather: {str(e)}"}

    # ----------------------------------------------------------------
    async def get_weather_forecast(self, plot_id: str) -> Dict[str, Any]:
        """
        Get 7-day weather forecast (starts from tomorrow)
        API: GET /forecast?plot_id=
        """
        cache_key = f"weather_forecast_{plot_id}"

        if cache_key in weather_cache:
            return weather_cache[cache_key]

        try:
            url = f"{WEATHER_API_URL}/forecast"
            params = {
                "plot_id": plot_id, 
                "lat": 19.36470605,
                "lon": 75.45908165, 
            }

            response = await self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

            weather_cache[cache_key] = data
            return data

        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch weather forecast: {str(e)}"}

    # ----------------------------------------------------------------

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()



# Global API service instance (will be initialized with auth token when available)
api_service: Optional[APIService] = None

def get_api_service(auth_token: Optional[str] = None) -> APIService:
    """Get or create API service instance"""
    global api_service
    if api_service is None or (auth_token and api_service.auth_token != auth_token):
        if api_service:
            # Close existing client
            import asyncio
            asyncio.create_task(api_service.close())
        api_service = APIService(auth_token=auth_token)
    return api_service
