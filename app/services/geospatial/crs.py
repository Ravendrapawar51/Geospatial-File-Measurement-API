import math
import pyproj
from typing import Tuple, Union, Optional, Any
from shapely.geometry import base
from shapely.ops import transform
from app.core.logging import logger

def parse_crs(crs_input: Any) -> pyproj.CRS:
    """Parses a CRS input (string, int, dict, or CRS object) into a valid pyproj.CRS."""
    if crs_input is None:
        return pyproj.CRS.from_epsg(4326)
    
    if isinstance(crs_input, pyproj.CRS):
        return crs_input
        
    try:
        if isinstance(crs_input, str):
            crs_str = crs_input.strip()
            if crs_str.isdigit():
                return pyproj.CRS.from_epsg(int(crs_str))
            return pyproj.CRS.from_user_input(crs_str)
        elif isinstance(crs_input, int):
            return pyproj.CRS.from_epsg(crs_input)
        else:
            return pyproj.CRS.from_user_input(crs_input)
    except Exception as e:
        logger.warning(f"Could not parse CRS '{crs_input}', defaulting to EPSG:4326. Error: {e}")
        return pyproj.CRS.from_epsg(4326)

def get_crs_str(crs: pyproj.CRS) -> str:
    """Returns a clean string representation of a CRS, preferring EPSG code if available."""
    epsg_code = crs.to_epsg()
    if epsg_code is not None:
        return f"EPSG:{epsg_code}"
    return crs.name or str(crs)

def is_geographic_crs(crs: pyproj.CRS) -> bool:
    """Checks if a CRS uses geographic coordinates (degrees lat/lon)."""
    return crs.is_geographic

def get_utm_epsg_for_bounds(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> int:
    """
    Calculates the UTM zone EPSG code based on the bounding box centroid.
    Formula:
        Zone = floor((lon + 180) / 6) + 1
        EPSG = 32600 + Zone (Northern Hemisphere) or 32700 + Zone (Southern Hemisphere)
    """
    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    
    center_lon = max(-180.0, min(180.0, center_lon))
    center_lat = max(-90.0, min(90.0, center_lat))
    
    utm_zone = math.floor((center_lon + 180) / 6) + 1
    utm_zone = max(1, min(60, utm_zone))
    
    if center_lat >= 0:
        epsg_code = 32600 + utm_zone
    else:
        epsg_code = 32700 + utm_zone
        
    return epsg_code

def select_projected_crs(source_crs: pyproj.CRS, bounds: Tuple[float, float, float, float]) -> pyproj.CRS:
    """
    Selects an appropriate projected CRS for accurate measurement calculations.
    - If source CRS is already projected with linear units (meters, feet, etc.), use source_crs.
    - If geographic, calculate local UTM zone based on bounding box centroid.
    """
    if not source_crs.is_geographic:
        return source_crs
        
    min_lon, min_lat, max_lon, max_lat = bounds
    utm_epsg = get_utm_epsg_for_bounds(min_lon, min_lat, max_lon, max_lat)
    
    try:
        projected_crs = pyproj.CRS.from_epsg(utm_epsg)
        logger.info(f"Transformed geographic CRS {get_crs_str(source_crs)} to UTM Projected CRS {get_crs_str(projected_crs)}")
        return projected_crs
    except Exception as e:
        logger.error(f"Failed to load UTM EPSG:{utm_epsg}, falling back to Web Mercator EPSG:3857: {e}")
        return pyproj.CRS.from_epsg(3857)

def get_geometry_transformer(source_crs: pyproj.CRS, target_crs: pyproj.CRS):
    """Creates a Shapely geometry transformer between two CRSs."""
    if source_crs == target_crs:
        return lambda geom: geom
        
    transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)
    
    def transform_func(geom: base.BaseGeometry) -> base.BaseGeometry:
        if geom is None or geom.is_empty:
            return geom
        return transform(transformer.transform, geom)
        
    return transform_func
