import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "Geospatial File Measurement API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Storage settings
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    METADATA_FILE: Path = BASE_DIR / "storage" / "metadata.json"
    
    # Supported extensions
    ALLOWED_EXTENSIONS: set = {".kml", ".zip"}
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # CRS defaults
    DEFAULT_GEOGRAPHIC_CRS: str = "EPSG:4326"
    DEFAULT_FALLBACK_PROJECTED_CRS: str = "EPSG:3857" # Web Mercator fallback if UTM fails

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
