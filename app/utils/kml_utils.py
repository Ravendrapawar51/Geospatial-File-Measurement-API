import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Tuple
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, MultiLineString, MultiPoint, GeometryCollection, shape
import pyproj
from app.core.exceptions import InvalidGeospatialFileError
from app.core.logging import logger

def parse_kml_coordinates(coord_text: str) -> List[Tuple[float, ...]]:
    """Parses KML coordinate text strings (lon,lat,alt lon,lat,alt ...)."""
    coords = []
    if not coord_text:
        return coords
    
    items = coord_text.strip().split()
    for item in items:
        parts = item.split(',')
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                if len(parts) >= 3:
                    coords.append((lon, lat, float(parts[2])))
                else:
                    coords.append((lon, lat))
            except ValueError:
                continue
    return coords

def parse_kml_file(kml_path: Path) -> Tuple[List[Dict[str, Any]], pyproj.CRS]:
    """
    Parses a KML file into a list of feature dicts.
    KML files always use WGS84 (EPSG:4326).
    """
    crs = pyproj.CRS.from_epsg(4326)
    
    try:
        import geopandas as gpd
        gdf = gpd.read_file(kml_path, driver="KML")
        if not gdf.empty:
            features = []
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue
                props = {k: v for k, v in row.to_dict().items() if k != "geometry" and v is not None}
                features.append({
                    "feature_id": idx,
                    "geometry_type": geom.geom_type,
                    "geometry": geom,
                    "properties": props,
                    "geojson": geom.__geo_interface__
                })
            if features:
                return features, crs
    except Exception as e:
        logger.info(f"GDAL/Pyogrio KML parser notice ({e}), using XML KML parser fallback.")

    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
        
        def get_tag_name(elem):
            return elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
        features = []
        feature_idx = 0
        
        def process_element(elem):
            nonlocal feature_idx
            tag = get_tag_name(elem)
            if tag == 'Placemark':
                name = None
                description = None
                properties = {}
                geom = None
                
                for child in elem:
                    ctag = get_tag_name(child)
                    if ctag == 'name':
                        name = child.text
                    elif ctag == 'description':
                        description = child.text
                    elif ctag == 'ExtendedData':
                        for data_node in child.iter():
                            dtag = get_tag_name(data_node)
                            if dtag in ('Data', 'SimpleData'):
                                key = data_node.attrib.get('name') or 'attribute'
                                val = data_node.findtext('*') if dtag == 'Data' else data_node.text
                                if not val and dtag == 'Data':
                                    val_node = child.find('{*}value')
                                    if val_node is not None:
                                        val = val_node.text
                                if key and val:
                                    properties[key] = val
                    elif ctag in ('Polygon', 'LineString', 'Point', 'MultiGeometry'):
                        geom = parse_kml_geometry_node(child)

                if name:
                    properties['name'] = name
                if description:
                    properties['description'] = description

                if geom is not None and not geom.is_empty:
                    features.append({
                        "feature_id": feature_idx,
                        "geometry_type": geom.geom_type,
                        "geometry": geom,
                        "properties": properties,
                        "geojson": geom.__geo_interface__
                    })
                    feature_idx += 1

            else:
                for child in elem:
                    process_element(child)

        process_element(root)

        if not features:
            logger.warning(f"No placemark features found in KML file '{kml_path.name}'.")
            
        return features, crs

    except Exception as e:
        raise InvalidGeospatialFileError(f"Failed to parse KML file: {str(e)}")

def parse_kml_geometry_node(node) -> Any:
    """Parses a KML XML geometry node into a Shapely geometry."""
    tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag
    
    if tag == 'Point':
        for child in node:
            if child.tag.endswith('coordinates'):
                coords = parse_kml_coordinates(child.text)
                if coords:
                    return Point(coords[0])
        return None
        
    elif tag == 'LineString':
        for child in node:
            if child.tag.endswith('coordinates'):
                coords = parse_kml_coordinates(child.text)
                if len(coords) >= 2:
                    return LineString(coords)
        return None
        
    elif tag == 'Polygon':
        outer_coords = []
        inner_coords_list = []
        
        for child in node:
            ctag = child.tag.split('}')[-1]
            if ctag == 'outerBoundaryIs':
                coords_elem = child.find('.//{*}coordinates')
                if coords_elem is not None and coords_elem.text:
                    outer_coords = parse_kml_coordinates(coords_elem.text)
            elif ctag == 'innerBoundaryIs':
                coords_elem = child.find('.//{*}coordinates')
                if coords_elem is not None and coords_elem.text:
                    inner_coords_list.append(parse_kml_coordinates(coords_elem.text))
                    
        if len(outer_coords) >= 3:
            return Polygon(shell=outer_coords, holes=inner_coords_list if inner_coords_list else None)
        return None
        
    elif tag == 'MultiGeometry':
        sub_geoms = []
        for child in node:
            g = parse_kml_geometry_node(child)
            if g is not None and not g.is_empty:
                sub_geoms.append(g)
        if sub_geoms:
            return GeometryCollection(sub_geoms)
        return None
        
    return None
