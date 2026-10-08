import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class FileRecord(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size_bytes: int
    file_type: str  # 'shapefile_zip' or 'kml'
    feature_count: int = 0
    crs: str = "EPSG:4326"
    status: str = "PENDING"  # PENDING, PROCESSING, COMPLETED, FAILED
    uploaded_at: str
    updated_at: str
    error_message: Optional[str] = None
    extracted_features: List[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileRecord":
        return cls(**data)
