from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from .models import Base, City, WeatherData

DATABASE_URL = "sqlite+aiosqlite:///./weather.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def add_city(name: str, latitude: float, longitude: float) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(City).where(City.name == name)
            )
            existing_city = result.scalars().one_or_none()

            if existing_city:
                return False
            
            city = City(
                name=name,
                latitude=latitude,
                longitude=longitude
            )
            session.add(city)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print(f"Error adding city: {e}")
            return False
        
async def get_all_cities() -> list:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(City).where(City.is_active == True)
        )
        cities = result.scalars().all()
        return [{"name": city.name, "latitude": city.latitude, "longitude": city.longitude}
                for city in cities]
    
async def save_weather_data(city_id: int, weather_data: dict):
    async with AsyncSessionLocal() as session:
        try:
            weather = WeatherData(
                city_id=city_id,
                timestamp=datetime.now(timezone.utc),
                temperature=weather_data.get('temperature'),
                wind_speed=weather_data.get('wind_speed'),
                pressure=weather_data.get('pressure'),
                humidity=weather_data.get('humidity'),
                precipitation=weather_data.get('precipitation')
            )
            session.add(weather)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Error saving weather data: {e}")

async def get_weather_by_city_and_time(city_name: str, time_str: str, params: list | None = None):
    async with AsyncSessionLocal() as session:
        try:
            result_city = await session.execute(
                select(City).where(City.name == city_name)
            )
            city = result_city.scalars().one_or_none()
            
            if not city:
                return None
            
            target_time = datetime.fromisoformat(time_str)
            start_of_day = target_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            result_weather = await session.execute(
                select(WeatherData)
                .where(WeatherData.city_id == city.id)
                .where(WeatherData.timestamp >= start_of_day)
                .where(WeatherData.timestamp < end_of_day)
            )
            weather = result_weather.scalars().all()

            if not weather:
                return None
            
            closest_weather = min(
                weather,
                key=lambda w: abs((w.timestamp - target_time).total_seconds())
            )
            
            response: Dict[str, Any] = {
                "city": city_name,
                "timestamp": closest_weather.timestamp.isoformat()
            }

            field_mapping = {
                "temperature": closest_weather.temperature,
                "humidity": closest_weather.humidity,
                "wind_speed": closest_weather.wind_speed,
                "precipitation": closest_weather.precipitation,
                "pressure": closest_weather.pressure
            }
            
            if params is None:
                for key, value in field_mapping.items():
                    if value is not None:
                        response[key] = value
            else:
                for param in params:
                    if param in field_mapping and field_mapping[param] is not None:
                        response[param] = field_mapping[param]
            
            return response
        except Exception as e:
            print(f"Error getting weather: {e}")
            return None
        
async def get_current_weather_by_coords(latitude: float, longitude: float):
    async with AsyncSessionLocal() as session:
        try:
            result_city = await session.execute(
                select(City)
                .where(City.latitude >= latitude - 0.1)
                .where(City.latitude <= latitude + 0.1)
                .where(City.longitude >= longitude - 0.1)
                .where(City.longitude <= longitude + 0.1)
                .where(City.is_active == True)
            )
            city = result_city.scalars().one_or_none()

            if not city:
                return None
            
            result_weather = await session.execute(
                select(WeatherData)
                .where(WeatherData.city_id == city.id)
                .order_by(WeatherData.timestamp.desc())
                .limit(1)
            )
            weather = result_weather.scalars().one_or_none()
            
            if not weather:
                return None
            
            return {
                "city": city.name,
                "temperature": weather.temperature,
                "wind_speed": weather.wind_speed,
                "pressure": weather.pressure,
                "timestamp": weather.timestamp.isoformat()
            }
        except Exception as e:
            print(f"Error getting current weather: {e}")
            return None
