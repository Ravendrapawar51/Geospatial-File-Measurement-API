from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field

class MeasurementDetail(BaseModel):
    type: str = Field(..., description="Measurement type: 'area', 'length', 'none', or 'unsupported'")
    value: Optional[float] = Field(None, description="Primary measurement value (sq meters for area, meters for length)")
    unit: str = Field(..., description="Primary unit of measurement")
    formatted: str = Field(..., description="Human readable formatted measurement string")
    additional_units: Dict[str, float] = Field(default_factory=dict, description="Values converted to alternative units")
    status: str = Field("calculated", description="Calculation status ('calculated', 'skipped', 'unsupported', 'error')")
    notes: Optional[str] = Field(None, description="Additional context or warning messages")

class FeatureMeasurement(BaseModel):
    feature_id: Union[int, str] = Field(..., description="Feature ID or index")
    geometry_type: str = Field(..., description="Geometry type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Feature attributes")
    measurement: MeasurementDetail

class SummaryMetrics(BaseModel):
    total_features: int
    polygons_count: int
    lines_count: int
    points_count: int
    unsupported_count: int
    total_area_sq_m: float
    total_area_hectares: float
    total_length_m: float
    total_length_km: float

class FileMeasurementsResponse(BaseModel):
    file_id: str
    filename: str
    original_crs: str
    projected_crs: str
    total_features: int
    summary: SummaryMetrics
    features: List[FeatureMeasurement]
