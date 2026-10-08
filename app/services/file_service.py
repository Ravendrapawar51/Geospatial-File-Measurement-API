import json
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import shape, box, MultiPolygon, Polygon
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import FileNotFoundError, InvalidGeospatialFileError
from app.models.file_record import FileRecord
from app.services.geospatial.parser import parse_geospatial_file
from app.services.geospatial.crs import get_crs_str, select_projected_crs, get_geometry_transformer, parse_crs
from app.services.geospatial.measurer import calculate_feature_measurement
from app.schemas.measurement import FileMeasurementsResponse, FeatureMeasurement, SummaryMetrics

def get_now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class FileService:
    def __init__(self):
        self.metadata_file = settings.METADATA_FILE
        self._records: Dict[str, FileRecord] = {}
        self._load_metadata()

    def _load_metadata(self):
        """Loads persisted file records from metadata.json file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for file_id, rec_data in data.items():
                        self._records[file_id] = FileRecord.from_dict(rec_data)
            except Exception as e:
                logger.error(f"Failed to load metadata.json: {e}")

    def _save_metadata(self):
        """Persists current file records to metadata.json file."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                data = {fid: rec.to_dict() for fid, rec in self._records.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata.json: {e}")

    def list_files(self) -> List[FileRecord]:
        return list(self._records.values())

    def get_file_record(self, file_id: str) -> FileRecord:
        if file_id not in self._records:
            raise FileNotFoundError(file_id)
        return self._records[file_id]

    def delete_file(self, file_id: str) -> bool:
        record = self.get_file_record(file_id)
        
        file_dir = Path(record.file_path).parent
        if file_dir.exists():
            shutil.rmtree(file_dir, ignore_errors=True)

        del self._records[file_id]
        self._save_metadata()
        return True

    def process_and_save_upload(self, file_bytes: bytes, filename: str) -> FileRecord:
        """
        Saves uploaded file bytes, processes features, extracts CRS, and persists record.
        """
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise InvalidGeospatialFileError(f"Unsupported file extension '{file_ext}'. Must be .kml or .zip (Shapefile).")

        file_id = uuid.uuid4().hex[:10]
        file_dir = settings.UPLOAD_DIR / file_id
        file_dir.mkdir(parents=True, exist_ok=True)

        target_file_path = file_dir / filename
        with open(target_file_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        now_str = get_now_utc_iso()

        record = FileRecord(
            id=file_id,
            filename=filename,
            file_path=str(target_file_path),
            file_size_bytes=file_size,
            file_type="kml" if file_ext == ".kml" else "shapefile_zip",
            feature_count=0,
            crs=settings.DEFAULT_GEOGRAPHIC_CRS,
            status="PROCESSING",
            uploaded_at=now_str,
            updated_at=now_str
        )
        self._records[file_id] = record
        self._save_metadata()

        try:
            features, source_crs = parse_geospatial_file(target_file_path, filename, file_dir)

            record.feature_count = len(features)
            record.crs = get_crs_str(source_crs)
            record.status = "COMPLETED"
            record.updated_at = get_now_utc_iso()

            serialized_features = []
            for feat in features:
                serialized_features.append({
                    "feature_id": feat["feature_id"],
                    "geometry_type": feat["geometry_type"],
                    "properties": feat["properties"],
                    "geojson": feat["geojson"]
                })

            record.extracted_features = serialized_features
            self._save_metadata()
            return record

        except Exception as e:
            record.status = "FAILED"
            record.error_message = str(e)
            record.updated_at = get_now_utc_iso()
            self._save_metadata()
            if isinstance(e, InvalidGeospatialFileError):
                raise e
            raise InvalidGeospatialFileError(f"Processing failed: {str(e)}")

    def get_file_measurements(self, file_id: str) -> FileMeasurementsResponse:
        """
        Calculates measurements for all features in the specified file.
        Dynamically handles CRS projected transformations for geographic coordinates.
        """
        record = self.get_file_record(file_id)

        if record.status != "COMPLETED":
            raise InvalidGeospatialFileError(f"Cannot calculate measurements for file in status '{record.status}'. Error: {record.error_message}")

        if not record.extracted_features:
            return FileMeasurementsResponse(
                file_id=record.id,
                filename=record.filename,
                original_crs=record.crs,
                projected_crs=record.crs,
                total_features=0,
                summary=SummaryMetrics(
                    total_features=0, polygons_count=0, lines_count=0, points_count=0,
                    unsupported_count=0, total_area_sq_m=0.0, total_area_hectares=0.0,
                    total_length_m=0.0, total_length_km=0.0
                ),
                features=[]
            )

        source_crs = parse_crs(record.crs)

        shapely_geoms = []
        for feat in record.extracted_features:
            try:
                g = shape(feat["geojson"])
                shapely_geoms.append(g)
            except Exception:
                shapely_geoms.append(None)

        valid_geoms = [g for g in shapely_geoms if g is not None and not g.is_empty]
        if valid_geoms:
            bounds = []
            for g in valid_geoms:
                bounds.append(g.bounds)
            min_x = min(b[0] for b in bounds)
            min_y = min(b[1] for b in bounds)
            max_x = max(b[2] for b in bounds)
            max_y = max(b[3] for b in bounds)
            dataset_bounds = (min_x, min_y, max_x, max_y)
        else:
            dataset_bounds = (-180.0, -90.0, 180.0, 90.0)

        projected_crs = select_projected_crs(source_crs, dataset_bounds)
        projected_crs_str = get_crs_str(projected_crs)

        transformer_fn = get_geometry_transformer(source_crs, projected_crs)

        feature_measurements: List[FeatureMeasurement] = []

        total_area_sq_m = 0.0
        total_length_m = 0.0
        polygons_cnt = 0
        lines_cnt = 0
        points_cnt = 0
        unsupported_cnt = 0

        for idx, feat_data in enumerate(record.extracted_features):
            geom_raw = shapely_geoms[idx]
            gtype = feat_data["geometry_type"]

            if geom_raw is not None:
                transformed_geom = transformer_fn(geom_raw)
            else:
                transformed_geom = None

            meas_detail = calculate_feature_measurement(transformed_geom, gtype)

            if meas_detail.type == "area" and meas_detail.value is not None:
                total_area_sq_m += meas_detail.value
                polygons_cnt += 1
            elif meas_detail.type == "length" and meas_detail.value is not None:
                total_length_m += meas_detail.value
                lines_cnt += 1
            elif meas_detail.type == "none":
                points_cnt += 1
            else:
                unsupported_cnt += 1

            feature_measurements.append(FeatureMeasurement(
                feature_id=feat_data["feature_id"],
                geometry_type=gtype,
                properties=feat_data["properties"],
                measurement=meas_detail
            ))

        summary = SummaryMetrics(
            total_features=len(feature_measurements),
            polygons_count=polygons_cnt,
            lines_count=lines_cnt,
            points_count=points_cnt,
            unsupported_count=unsupported_cnt,
            total_area_sq_m=round(total_area_sq_m, 2),
            total_area_hectares=round(total_area_sq_m / 10000.0, 4),
            total_length_m=round(total_length_m, 2),
            total_length_km=round(total_length_m / 1000.0, 4)
        )

        return FileMeasurementsResponse(
            file_id=record.id,
            filename=record.filename,
            original_crs=record.crs,
            projected_crs=projected_crs_str,
            total_features=len(feature_measurements),
            summary=summary,
            features=feature_measurements
        )

file_service = FileService()
