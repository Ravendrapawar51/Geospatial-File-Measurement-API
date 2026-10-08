import os
import zipfile
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
from pathlib import Path

out_dir = Path(__file__).parent
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Create Polygon Shapefile (.zip) - New York Land Parcels (EPSG:4326)
poly1 = Polygon([(-73.985, 40.748), (-73.980, 40.748), (-73.980, 40.745), (-73.985, 40.745), (-73.985, 40.748)])
poly2 = Polygon([(-73.978, 40.752), (-73.972, 40.752), (-73.975, 40.749), (-73.978, 40.752)])

gdf_polys = gpd.GeoDataFrame(
    [
        {"id": 1, "name": "Empire State Sector", "owner": "Acme Corp"},
        {"id": 2, "name": "East Park Triangle", "owner": "City Metro"}
    ],
    geometry=[poly1, poly2],
    crs="EPSG:4326"
)

shp_temp_dir = out_dir / "temp_shp"
shp_temp_dir.mkdir(exist_ok=True)
shp_path = shp_temp_dir / "survey_parcels.shp"
gdf_polys.to_file(shp_path)

zip_shp_path = out_dir / "survey_parcels.zip"
with zipfile.ZipFile(zip_shp_path, "w", zipfile.ZIP_DEFLATED) as z:
    for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
        f_path = shp_temp_dir / f"survey_parcels{ext}"
        if f_path.exists():
            z.write(f_path, f_path.name)

# 2. Create Road Lines KML (EPSG:4326)
kml_lines_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>City Transit Roads</name>
    <Placemark>
      <name>Main Highway Segment</name>
      <description>Primary north-south corridor</description>
      <LineString>
        <coordinates>
          -73.985,40.748,0 -73.980,40.755,0 -73.970,40.760,0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Crosstown Boulevard</name>
      <description>East-west connector street</description>
      <LineString>
        <coordinates>
          -73.990,40.750,0 -73.970,40.750,0
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""
with open(out_dir / "road_lines.kml", "w", encoding="utf-8") as f:
    f.write(kml_lines_content)

# 3. Create POI Points KML (EPSG:4326)
kml_points_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Survey Landmarks</name>
    <Placemark>
      <name>Station Alpha</name>
      <description>GPS Benchmark 101</description>
      <Point>
        <coordinates>-73.9851,40.7489,15.0</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>Station Beta</name>
      <description>GPS Benchmark 102</description>
      <Point>
        <coordinates>-73.9782,40.7523,12.5</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
"""
with open(out_dir / "poi_points.kml", "w", encoding="utf-8") as f:
    f.write(kml_points_content)

print(f"Sample data files generated successfully in {out_dir}")
