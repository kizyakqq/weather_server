from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from contextlib import asynccontextmanager

from .database import (
    init_db, add_city, get_all_cities, save_weather_data,
    get_weather_by_city_and_time, AsyncSessionLocal
)
from .weather_api import fetch_weather_data
from .models import City

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    update_task = asyncio.create_task(update_weather_periodically())
    
    yield

    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        print("Update task stopped")

app = FastAPI(
    title="Weather API Server",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CityRequest(BaseModel):
    name: str
    latitude: float
    longitude: float

class WeatherResponse(BaseModel):
    city: str
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    timestamp: str

class CurrentWeatherRequest(BaseModel):
    latitude: float
    longitude: float

async def update_weather_periodically():
    while True:
        try:
            cities = await get_all_cities()
            
            for city in cities:
                weather_data = await fetch_weather_data(
                    city["latitude"], 
                    city["longitude"]
                )
                
                if weather_data:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(
                            select(City).where(City.name == city["name"])
                        )
                        city_obj = result.scalars().one_or_none()
                        
                        if city_obj:
                            await save_weather_data(city_obj.id, weather_data)
            
            print(f"Weather data updated at {datetime.now(timezone.utc)}")
            
        except Exception as e:
            print(f"Error in periodic update: {e}")
        
        await asyncio.sleep(900)

@app.get("/")
async def root():
    return {"message": "Weather API Server is running"}

@app.post("/weather/current")
async def get_current_weather(request: CurrentWeatherRequest):
    weather_data = await fetch_weather_data(
        request.latitude, 
        request.longitude
    )
    
    if not weather_data:
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")
    
    return {
        "temperature": weather_data.get("temperature"),
        "wind_speed": weather_data.get("wind_speed"),
        "pressure": weather_data.get("pressure"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/cities")
async def add_city_endpoint(request: CityRequest):
    success = await add_city(
        request.name, 
        request.latitude, 
        request.longitude
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="City already exists or failed to add")
    
    weather_data = await fetch_weather_data(
        request.latitude, 
        request.longitude
    )
    
    if weather_data:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(City).where(City.name == request.name)
            )
            city_obj = result.scalars().one_or_none()
            
            if city_obj:
                await save_weather_data(city_obj.id, weather_data)
    
    return {"message": f"City {request.name} added successfully"}

@app.get("/cities")
async def get_cities():
    cities = await get_all_cities()
    return {"cities": cities}

@app.get("/weather/{city_name}/{time}")
async def get_weather_by_time(
    city_name: str,
    time: str,
    params: Optional[List[str]] = Query(None, description="Список параметров: temperature, humidity, wind_speed, precipitation")
):
    weather_data = await get_weather_by_city_and_time(city_name, time, params)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail="Weather data not found")
    
    return weather_data
