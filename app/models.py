from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class City(Base):
    __tablename__ = 'cities'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    weather_records: Mapped[List["WeatherData"]] = relationship(
        back_populates="city", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<City(name='{self.name}', lat={self.latitude}, lon={self.longitude})>"
    

class WeatherData(Base):
    __tablename__ = 'weather_data'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    timestamp: Mapped[datetime] = mapped_column()
    temperature: Mapped[Optional[float]] = mapped_column()
    wind_speed: Mapped[Optional[float]] = mapped_column()
    pressure: Mapped[Optional[float]] = mapped_column()
    humidity: Mapped[Optional[float]] = mapped_column()
    precipitation: Mapped[Optional[float]] = mapped_column()
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    city: Mapped["City"] = relationship(back_populates="weather_records")

    def __repr__(self):
        return f"<WeatherData(city_id={self.city_id}, temp={self.temperature}°C)>"
