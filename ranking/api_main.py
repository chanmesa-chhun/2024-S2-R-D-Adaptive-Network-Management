import os
import tempfile
import logging
import csv

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, validator
from tower_analysis.runner import run_pipeline

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("tower-api")

# --- App init ---
app = FastAPI(
    title="Tower Analysis API",
    version="2.2.0",
    description="Upload a CSV of failed towers, run full coverage & ranking pipeline, return JSON results and provide a download link."
)

# --- Global error handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP error for {request.url}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error for {request.url}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please try again later."}
    )

# --- JSON echo endpoint ---
class TowerNamesRequest(BaseModel):
    tower_names: list[str]

    @validator("tower_names")
    def must_have_names(cls, v):
        if not v:
            raise ValueError("tower_names list cannot be empty.")
        for name in v:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("All tower names must be non-empty strings.")
        return v

@app.post("/towers", response_model=dict)
async def handle_tower_names(req: TowerNamesRequest):
    response = {
        "message": "Successfully received tower names.",
        "count": len(req.tower_names),
        "towers": req.tower_names
    }
    logger.info("→ Response /towers: %s", response)
    return response

# --- Pipeline endpoint: upload, run, JSON + download link ---
@app.post("/run-ranking", response_model=dict)
async def run_ranking_api(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # Save uploaded CSV to temp file
    suffix = os.path.splitext(file.filename)[1] or ".csv"
    tmp = tempfile.NamedTemporaryFile(prefix="failed_", suffix=suffix, delete=False)
    tmp.write(await file.read())
    tmp.flush()
    tmp.close()

    # Run pipeline
    try:
        output_csv = run_pipeline(failed_csv_path=tmp.name)
    except Exception as e:
        logger.exception("Pipeline error")
        raise HTTPException(500, f"Pipeline error: {e}")

    # Read CSV into list of dicts
    results = []
    try:
        with open(output_csv, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except Exception as e:
        logger.exception("Error reading output CSV")
        raise HTTPException(500, f"Error parsing result: {e}")

    # Prepare JSON response
    filename = os.path.basename(output_csv)
    download_url = f"/download/{filename}"
    response = {
        "message": "Ranking complete",
        "count": len(results),
        "results": results,
        "download_url": download_url
    }
    logger.info("→ Response /run-ranking: %d rows, download=%s", len(results), download_url)
    return response

# --- Download endpoint ---
@app.get("/download/{filename}")
async def download_csv(filename: str):
    path = os.path.join("output", filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type="text/csv", filename=filename)

# --- Run with Uvicorn ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, log_level="info")