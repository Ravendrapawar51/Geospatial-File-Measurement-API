from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class FeatureItem(BaseModel):
    feature_id: Union[int, str] = Field(..., description="Feature identifier or index")
    geometry_type: str = Field(..., description="Geometry type (e.g. Polygon, LineString, Point)")
    crs: str = Field(..., description="CRS of the geometry")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Feature attributes and metadata")
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry representation")

class FeatureListResponse(BaseModel):
    file_id: str
    total_features: int
    features: list[FeatureItem]
