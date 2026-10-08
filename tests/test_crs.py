import pytest
import pyproj
from app.services.geospatial.crs import (
    parse_crs,
    get_crs_str,
    is_geographic_crs,
    get_utm_epsg_for_bounds,
    select_projected_crs
)

def test_parse_crs():
    crs_wgs84 = parse_crs("EPSG:4326")
    assert crs_wgs84.to_epsg() == 4326
    assert is_geographic_crs(crs_wgs84) is True

def test_utm_zone_calculation():
    # New York City (approx -73.98, 40.75) -> UTM Zone 18N -> EPSG:32618
    epsg_ny = get_utm_epsg_for_bounds(-74.0, 40.7, -73.9, 40.8)
    assert epsg_ny == 32618

    # Sydney, Australia (approx 151.2, -33.8) -> UTM Zone 56S -> EPSG:32756
    epsg_sydney = get_utm_epsg_for_bounds(151.1, -33.9, 151.3, -33.7)
    assert epsg_sydney == 32756

def test_select_projected_crs():
    geographic_crs = parse_crs("EPSG:4326")
    bounds_ny = (-74.0, 40.7, -73.9, 40.8)
    
    projected = select_projected_crs(geographic_crs, bounds_ny)
    assert projected.is_geographic is False
    assert projected.to_epsg() == 32618
