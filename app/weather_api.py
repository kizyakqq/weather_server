import httpx
from typing import Dict, Optional, Union, List

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

QueryParamValue = Union[str, int, float, None, List[Union[str, int, float, bool, None]]]

async def fetch_weather_data(latitude: float, longitude: float) -> Optional[Dict]:
    params: Dict[str, QueryParamValue] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,surface_pressure,relative_humidity_2m,precipitation",
        "hourly": "temperature_2m,wind_speed_10m,surface_pressure,relative_humidity_2m,precipitation",
        "forecast_days": 1,
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            current_data = data.get("current", {})
            
            return {
                "temperature": current_data.get("temperature_2m"),
                "wind_speed": current_data.get("wind_speed_10m"),
                "pressure": current_data.get("surface_pressure"),
                "humidity": current_data.get("relative_humidity_2m"),
                "precipitation": current_data.get("precipitation")
            }
        except httpx.HTTPError as e:
            print(f"Error fetching weather: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

async def fetch_hourly_forecast(latitude: float, longitude: float) -> Optional[Dict]:
    params: Dict[str, QueryParamValue] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,surface_pressure,relative_humidity_2m,precipitation",
        "hourly": "temperature_2m,wind_speed_10m,surface_pressure,relative_humidity_2m,precipitation",
        "forecast_days": 1,
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            hourly = data.get("hourly", {})
            timestamps = hourly.get("time", [])
            
            forecast = []
            for i, timestamp in enumerate(timestamps):
                forecast.append({
                    "timestamp": timestamp,
                    "temperature": hourly.get("temperature_2m", [])[i] if i < len(hourly.get("temperature_2m", [])) else None,
                    "wind_speed": hourly.get("wind_speed_10m", [])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
                    "pressure": hourly.get("surface_pressure", [])[i] if i < len(hourly.get("surface_pressure", [])) else None,
                    "humidity": hourly.get("relative_humidity_2m", [])[i] if i < len(hourly.get("relative_humidity_2m", [])) else None,
                    "precipitation": hourly.get("precipitation", [])[i] if i < len(hourly.get("precipitation", [])) else None
                })
            
            return {"hourly_forecast": forecast}
        except httpx.HTTPError as e:
            print(f"Error fetching hourly forecast: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None