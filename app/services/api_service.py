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
SOIL_API_URL = os.getenv("SOIL_API_URL", "https://dev-soil.cropeye.ai")
PLOT_API_URL = os.getenv("PLOT_API_URL", "https://dev-plot.cropeye.ai")
EVENTS_API_URL = os.getenv("EVENTS_API_URL", "https://dev-events.cropeye.ai")

# Cache configuration
soil_cache = TTLCache(maxsize=1000, ttl=900)  # 15 minutes
irrigation_cache = TTLCache(maxsize=500, ttl=300)  # 5 minutes
pest_cache = TTLCache(maxsize=500, ttl=600)  # 10 minutes
yield_cache = TTLCache(maxsize=500, ttl=1800)  # 30 minutes
farm_context_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour


class APIService:
    """Centralized API service for chatbot"""
    
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if available"""
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def get_farmer_profile(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get farmer profile with plots information
        API: GET /farms/my-profile/
        """
        cache_key = f"farmer_profile_{user_id or 'default'}"
        
        if cache_key in farm_context_cache:
            return farm_context_cache[cache_key]
        
        try:
            url = f"{BASE_URL}/farms/my-profile/"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            farm_context_cache[cache_key] = data
            return data
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch farmer profile: {str(e)}"}
    
    async def get_soil_analysis(
        self, 
        plot_name: str, 
        date: Optional[str] = None,
        fe_days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get complete soil analysis for a plot
        API: POST /analyze?plot_name={id}&date={date}&fe_days_back=30
        Returns: N, P, K, pH, CEC, OC, BD, Fe, SOC
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"soil_analysis_{plot_name}_{date}"
        
        if cache_key in soil_cache:
            return soil_cache[cache_key]
        
        try:
            url = f"{SOIL_API_URL}/analyze"
            params = {
                "plot_name": plot_name,
                "date": date,
                "fe_days_back": fe_days_back
            }
            response = await self.client.post(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            soil_cache[cache_key] = data
            return data
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch soil analysis: {str(e)}"}
    
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
            return soil_cache[cache_key]
        
        try:
            url = f"{SOIL_API_URL}/required-n/{plot_name}"
            params = {"end_date": end_date}
            response = await self.client.post(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            soil_cache[cache_key] = data
            return data
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch NPK requirements: {str(e)}"}
    
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
