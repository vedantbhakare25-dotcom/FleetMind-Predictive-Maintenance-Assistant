# Loads and validates all environment variables for FleetMind

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    # Supabase
    SUPABASE_URL        : str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET : str

    # App
    APP_NAME : str = "FleetMind API"
    VERSION  : str = "1.0.0"
    DEBUG    : bool = False

    # ML Thresholds
    PREDICTION_THRESHOLD : float = 0.50
    CRITICAL_THRESHOLD   : float = 0.90
    HIGH_THRESHOLD       : float = 0.75
    MEDIUM_THRESHOLD     : float = 0.50

    # Health Score Thresholds
    HEALTH_CRITICAL_THRESHOLD : float = 20.0
    HEALTH_HIGH_THRESHOLD     : float = 40.0
    HEALTH_MEDIUM_THRESHOLD   : float = 60.0
    HEALTH_LOW_THRESHOLD      : float = 75.0

    class Config:
        env_file         = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()