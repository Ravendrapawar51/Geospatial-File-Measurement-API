import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
from app.utils.zip_utils import validate_and_extract_shapefile_zip
from app.utils.kml_utils import parse_kml_file
from app.services.geospatial.crs import parse_crs, get_crs_str
from app.core.exceptions import InvalidGeospatialFileError
from app.core.logging import logger

def clean_value(val: Any) -> Any:
    """Converts numpy, pandas, datetime, NaT, NaN, etc. into JSON-serializable standard Python types."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if hasattr(val, "isoformat"):
        return val.isoformat()
    if isinstance(val, (list, tuple)):
        return [clean_value(x) for x in val]
    if isinstance(val, dict):
        return {str(k): clean_value(v) for k, v in val.items()}
    if isinstance(val, (str, bool)):
        return val
    return str(val)

def clean_properties(props: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = {}
    for k, v in props.items():
        val = clean_value(v)
        if val is not None:
            cleaned[str(k)] = val
    return cleaned

def parse_geospatial_file(file_path: Path, filename: str, work_dir: Path) -> Tuple[List[Dict[str, Any]], pyproj.CRS]:
    """
    Main entry point for parsing any supported geospatial file (.zip Shapefile or .kml).
    Returns a tuple of (list of feature dicts, source pyproj.CRS).
    """
    ext = file_path.suffix.lower()

    if ext == ".kml":
        raw_features, crs = parse_kml_file(file_path)
        features = []
        for feat in raw_features:
            features.append({
                "feature_id": feat["feature_id"],
                "geometry_type": feat["geometry_type"],
                "geometry": feat["geometry"],
                "properties": clean_properties(feat["properties"]),
                "geojson": feat["geojson"]
            })
        return features, crs

    elif ext == ".zip":
        extract_dir = work_dir / "extracted_shp"
        extract_dir.mkdir(parents=True, exist_ok=True)

        shp_file = validate_and_extract_shapefile_zip(file_path, extract_dir)

        try:
            gdf = gpd.read_file(shp_file)
            if gdf.empty:
                raise InvalidGeospatialFileError("Shapefile contains no geometry features.")

            source_crs = parse_crs(gdf.crs)

            features = []
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue

                raw_props = {k: v for k, v in row.to_dict().items() if k != "geometry"}
                props = clean_properties(raw_props)

                features.append({
                    "feature_id": int(idx),
                    "geometry_type": geom.geom_type,
                    "geometry": geom,
                    "properties": props,
                    "geojson": geom.__geo_interface__
                })

            return features, source_crs

        except InvalidGeospatialFileError:
            raise
        except Exception as e:
            raise InvalidGeospatialFileError(f"Error reading Shapefile from zip archive: {str(e)}")

    else:
        raise InvalidGeospatialFileError(f"Unsupported file format '{ext}'. Only .zip (Shapefile) and .kml are supported.")
