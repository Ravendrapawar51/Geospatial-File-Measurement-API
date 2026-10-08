from fastapi import HTTPException, status

class GeospatialAPIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class FileNotFoundError(GeospatialAPIException):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' was not found."
        )

class InvalidGeospatialFileError(GeospatialAPIException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid geospatial file: {message}"
        )

class CRSConversionError(GeospatialAPIException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CRS processing error: {message}"
        )
