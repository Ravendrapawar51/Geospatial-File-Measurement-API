from fastapi import APIRouter, UploadFile, File, status, Query
from typing import List, Optional
from app.schemas.file import FileInfoResponse, FileUploadResponse, FileListResponse
from app.schemas.feature import FeatureListResponse, FeatureItem
from app.schemas.measurement import FileMeasurementsResponse
from app.services.file_service import file_service
from app.core.exceptions import InvalidGeospatialFileError

router = APIRouter()

@router.post("/", response_model=FileInfoResponse, status_code=status.HTTP_201_CREATED, summary="Upload and process a geospatial file")
async def upload_file(file: UploadFile = File(..., description="Geospatial file (.kml or .zip containing a Shapefile)")):
    """
    Uploads and processes a geospatial file (.kml or .zip Shapefile).
    - Extracts features, geometries, attributes, and original CRS.
    - Status set to COMPLETED upon successful processing.
    """
    if not file.filename:
        raise InvalidGeospatialFileError("Uploaded file has no filename.")

    contents = await file.read()
    if not contents:
        raise InvalidGeospatialFileError("Uploaded file is empty (0 bytes).")

    record = file_service.process_and_save_upload(contents, file.filename)
    return FileInfoResponse(
        id=record.id,
        filename=record.filename,
        file_size_bytes=record.file_size_bytes,
        feature_count=record.feature_count,
        crs=record.crs,
        status=record.status,
        uploaded_at=record.uploaded_at,
        error_message=record.error_message
    )

@router.get("/", response_model=FileListResponse, summary="List all uploaded geospatial files")
async def list_files():
    """Returns a list of all uploaded and processed geospatial files."""
    records = file_service.list_files()
    items = [
        FileInfoResponse(
            id=r.id,
            filename=r.filename,
            file_size_bytes=r.file_size_bytes,
            feature_count=r.feature_count,
            crs=r.crs,
            status=r.status,
            uploaded_at=r.uploaded_at,
            error_message=r.error_message
        )
        for r in records
    ]
    return FileListResponse(total=len(items), files=items)

@router.get("/{id}/", response_model=FileInfoResponse, summary="Get information about an uploaded file")
async def get_file_info(id: str):
    """Returns information about the uploaded file by ID."""
    record = file_service.get_file_record(id)
    return FileInfoResponse(
        id=record.id,
        filename=record.filename,
        file_size_bytes=record.file_size_bytes,
        feature_count=record.feature_count,
        crs=record.crs,
        status=record.status,
        uploaded_at=record.uploaded_at,
        error_message=record.error_message
    )

@router.get("/{id}/measurements/", response_model=FileMeasurementsResponse, summary="Get measurements for features in the file")
async def get_file_measurements(id: str):
    """
    Returns measurement information for all features within the specified geospatial file.
    - Polygons -> Area (m2, ha, km2)
    - LineStrings -> Length (m, km)
    - Points -> Skipped gracefully (no length/area)
    - Geographic CRS -> Dynamically transformed to optimal projected CRS (e.g. UTM) before calculation.
    """
    return file_service.get_file_measurements(id)

@router.get("/{id}/features/", response_model=FeatureListResponse, summary="Get extracted features and GeoJSON geometries")
async def get_file_features(id: str):
    """Returns detailed feature properties and GeoJSON geometries."""
    record = file_service.get_file_record(id)
    features = [
        FeatureItem(
            feature_id=f["feature_id"],
            geometry_type=f["geometry_type"],
            crs=record.crs,
            properties=f["properties"],
            geometry=f["geojson"]
        )
        for f in record.extracted_features
    ]
    return FeatureListResponse(file_id=record.id, total_features=len(features), features=features)

@router.delete("/{id}/", status_code=status.HTTP_200_OK, summary="Delete an uploaded file")
async def delete_file(id: str):
    """Deletes an uploaded file record and associated stored files."""
    file_service.delete_file(id)
    return {"message": f"File with ID '{id}' successfully deleted."}
