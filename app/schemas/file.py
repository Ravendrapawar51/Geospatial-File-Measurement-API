from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class FileInfoResponse(BaseModel):
    id: str = Field(..., description="Unique file identifier", json_schema_extra={"example": "abc12345"})
    filename: str = Field(..., description="Original filename", json_schema_extra={"example": "survey.kml"})
    file_size_bytes: int = Field(..., description="Size of uploaded file in bytes", json_schema_extra={"example": 10240})
    feature_count: int = Field(..., description="Number of extracted features", json_schema_extra={"example": 120})
    crs: str = Field(..., description="Original CRS of the dataset", json_schema_extra={"example": "EPSG:4326"})
    status: str = Field(..., description="File processing status (COMPLETED, FAILED, PROCESSING)", json_schema_extra={"example": "COMPLETED"})
    uploaded_at: str = Field(..., description="ISO timestamp of upload")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: str
    status: str
    message: str = "File uploaded and processed successfully."

class FileListResponse(BaseModel):
    total: int
    files: List[FileInfoResponse]
