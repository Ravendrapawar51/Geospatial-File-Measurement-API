import pytest
from shapely.geometry import Polygon, LineString, Point, GeometryCollection
from app.services.geospatial.measurer import calculate_feature_measurement

def test_polygon_area_measurement():
    # Square polygon 100m x 100m = 10,000 m2 (1 hectare) in projected coordinates
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    result = calculate_feature_measurement(poly, "Polygon")
    
    assert result.type == "area"
    assert result.status == "calculated"
    assert pytest.approx(result.value, rel=1e-2) == 10000.0
    assert result.unit == "square_meters"
    assert "hectares" in result.additional_units
    assert pytest.approx(result.additional_units["hectares"], rel=1e-2) == 1.0

def test_linestring_length_measurement():
    # Line 500m long in projected coordinates
    line = LineString([(0, 0), (300, 400)]) # 3-4-5 triangle: length 500m
    result = calculate_feature_measurement(line, "LineString")
    
    assert result.type == "length"
    assert result.status == "calculated"
    assert pytest.approx(result.value, rel=1e-2) == 500.0
    assert result.unit == "meters"
    assert "kilometers" in result.additional_units
    assert pytest.approx(result.additional_units["kilometers"], rel=1e-2) == 0.5

def test_point_no_measurement():
    point = Point(100, 200)
    result = calculate_feature_measurement(point, "Point")
    
    assert result.type == "none"
    assert result.status == "skipped"
    assert result.value == 0.0
    assert "no area or length measurement required" in result.formatted

def test_unsupported_geometry_graceful_handling():
    geom_coll = GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])
    result = calculate_feature_measurement(geom_coll, "GeometryCollection")
    
    assert result.type == "unsupported"
    assert result.status == "unsupported"
    assert result.value is None
    assert "is not supported" in result.formatted
