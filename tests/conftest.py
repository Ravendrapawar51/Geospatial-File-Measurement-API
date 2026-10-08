import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
def sample_data_dir():
    return Path(__file__).parent.parent / "sample_data"

@pytest.fixture(scope="session")
def sample_shapefile_zip(sample_data_dir):
    return sample_data_dir / "survey_parcels.zip"

@pytest.fixture(scope="session")
def sample_lines_kml(sample_data_dir):
    return sample_data_dir / "road_lines.kml"

@pytest.fixture(scope="session")
def sample_points_kml(sample_data_dir):
    return sample_data_dir / "poi_points.kml"
