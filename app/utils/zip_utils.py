import os
import zipfile
from pathlib import Path
from typing import List, Optional
from app.core.exceptions import InvalidGeospatialFileError

def validate_and_extract_shapefile_zip(zip_path: Path, extract_to_dir: Path) -> Path:
    """
    Validates a ZIP file containing a Shapefile (.shp, .dbf, .shx) and extracts it safely.
    Returns the path to the main .shp file.
    """
    if not zipfile.is_zipfile(zip_path):
        raise InvalidGeospatialFileError("Uploaded file is not a valid ZIP archive.")

    shp_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise InvalidGeospatialFileError("Zip file contains insecure path traversal references.")
                
            if member.filename.lower().endswith(".shp"):
                shp_files.append(member.filename)
                
        if not shp_files:
            raise InvalidGeospatialFileError("ZIP archive does not contain a '.shp' Shapefile.")

        zip_ref.extractall(extract_to_dir)

    main_shp = extract_to_dir / shp_files[0]
    return main_shp
