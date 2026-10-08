from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import GeospatialAPIException
from app.api.router import api_router

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ### Geospatial File Measurement API
    
    High-performance backend API built with FastAPI, GeoPandas, Shapely, and PyProj.
    Accepts **Shapefile (.zip archives)** and **KML (.kml)** files, extracts features, 
    and accurately calculates geometric measurements (Area for Polygons, Length for LineStrings) 
    by dynamically selecting an appropriate projected CRS for geographic coordinates (e.g. EPSG:4326 WGS84 -> UTM zone).
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(GeospatialAPIException)
async def geospatial_exception_handler(request: Request, exc: GeospatialAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
