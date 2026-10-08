from typing import Dict, Any, Union, Optional
from shapely.geometry import base, Polygon, MultiPolygon, LineString, MultiLineString, Point, MultiPoint
from app.schemas.measurement import MeasurementDetail
from app.core.logging import logger

def calculate_feature_measurement(geom: base.BaseGeometry, geometry_type: str) -> MeasurementDetail:
    """
    Calculates measurement information for a single transformed Shapely geometry.
    - Polygon / MultiPolygon -> Area
    - LineString / MultiLineString -> Length
    - Point / MultiPoint -> No measurement
    - Unsupported / Invalid -> Graceful handling without crashing
    """
    if geom is None or geom.is_empty:
        return MeasurementDetail(
            type="none",
            value=0.0,
            unit="n/a",
            formatted="Empty or null geometry",
            status="skipped",
            notes="Geometry is empty or null"
        )

    gtype = geometry_type.upper() if geometry_type else geom.geom_type.upper()

    try:
        # Polygon / MultiPolygon Area calculation
        if "POLYGON" in gtype:
            area_m2 = float(geom.area)
            hectares = area_m2 / 10000.0
            sq_km = area_m2 / 1000000.0
            sq_ft = area_m2 * 10.763910416709724

            if sq_km >= 1.0:
                formatted_str = f"{area_m2:,.2f} m\u00b2 ({sq_km:,.2f} km\u00b2 / {hectares:,.2f} ha)"
            elif hectares >= 1.0:
                formatted_str = f"{area_m2:,.2f} m\u00b2 ({hectares:,.2f} ha)"
            else:
                formatted_str = f"{area_m2:,.2f} m\u00b2"

            return MeasurementDetail(
                type="area",
                value=round(area_m2, 4),
                unit="square_meters",
                formatted=formatted_str,
                additional_units={
                    "hectares": round(hectares, 4),
                    "square_kilometers": round(sq_km, 6),
                    "square_feet": round(sq_ft, 2)
                },
                status="calculated"
            )

        # LineString / MultiLineString Length calculation
        elif "LINESTRING" in gtype or "LINE" in gtype:
            length_m = float(geom.length)
            km = length_m / 1000.0
            feet = length_m * 3.28084
            miles = length_m / 1609.344

            if km >= 1.0:
                formatted_str = f"{length_m:,.2f} m ({km:,.2f} km)"
            else:
                formatted_str = f"{length_m:,.2f} m"

            return MeasurementDetail(
                type="length",
                value=round(length_m, 4),
                unit="meters",
                formatted=formatted_str,
                additional_units={
                    "kilometers": round(km, 4),
                    "feet": round(feet, 2),
                    "miles": round(miles, 4)
                },
                status="calculated"
            )

        # Point / MultiPoint
        elif "POINT" in gtype:
            return MeasurementDetail(
                type="none",
                value=0.0,
                unit="n/a",
                formatted="Point feature (no area or length measurement required)",
                additional_units={},
                status="skipped",
                notes="Point features do not possess linear length or surface area."
            )

        # Unsupported geometry types (e.g. GeometryCollection, PolyhedralSurface, TIN)
        else:
            logger.warning(f"Unsupported geometry type encountered: {geometry_type}")
            return MeasurementDetail(
                type="unsupported",
                value=None,
                unit="n/a",
                formatted=f"Geometry type '{geometry_type}' is not supported for measurement",
                additional_units={},
                status="unsupported",
                notes=f"Measurement calculations are not defined for geometry type '{geometry_type}'"
            )

    except Exception as e:
        logger.error(f"Error calculating measurement for geometry '{geometry_type}': {e}")
        return MeasurementDetail(
            type="unsupported",
            value=None,
            unit="n/a",
            formatted=f"Error processing measurement: {str(e)}",
            additional_units={},
            status="error",
            notes=str(e)
        )
