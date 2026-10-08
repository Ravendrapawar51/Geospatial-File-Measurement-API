import pytest
from pathlib import Path

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_upload_shapefile_zip(client, sample_shapefile_zip):
    assert sample_shapefile_zip.exists()
    
    with open(sample_shapefile_zip, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("survey_parcels.zip", f, "application/zip")}
        )
        
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "survey_parcels.zip"
    assert data["feature_count"] == 2
    assert data["status"] == "COMPLETED"
    assert "EPSG" in data["crs"]

    file_id = data["id"]

    # Test GET /api/files/{id}/
    info_res = client.get(f"/api/files/{file_id}/")
    assert info_res.status_code == 200
    assert info_res.json()["id"] == file_id

    # Test GET /api/files/{id}/measurements/
    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert meas_data["file_id"] == file_id
    assert meas_data["total_features"] == 2
    assert meas_data["summary"]["polygons_count"] == 2
    assert meas_data["summary"]["total_area_sq_m"] > 0
    assert "EPSG:32618" in meas_data["projected_crs"] # Transformed to UTM 18N for NYC!

def test_upload_kml(client, sample_lines_kml):
    assert sample_lines_kml.exists()

    with open(sample_lines_kml, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("road_lines.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "road_lines.kml"
    assert data["feature_count"] == 2
    assert data["status"] == "COMPLETED"

    file_id = data["id"]

    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert meas_data["summary"]["lines_count"] == 2
    assert meas_data["summary"]["total_length_m"] > 0

def test_upload_points_kml(client, sample_points_kml):
    assert sample_points_kml.exists()

    with open(sample_points_kml, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("poi_points.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 201
    file_id = response.json()["id"]

    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert meas_data["summary"]["points_count"] == 2
    for feat in meas_data["features"]:
        assert feat["measurement"]["type"] == "none"

def test_invalid_file_extension(client):
    response = client.post(
        "/api/files/",
        files={"file": ("document.pdf", b"pdf content", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]

def test_file_not_found(client):
    response = client.get("/api/files/non_existent_id/")
    assert response.status_code == 404
