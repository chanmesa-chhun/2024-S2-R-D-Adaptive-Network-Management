# api_main.py

import os
import tempfile
import logging
import csv

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from tower_analysis.runner import run_pipeline
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# — Logging setup —
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("tower-api")

# — App init —
app = FastAPI(
    title="Tower Analysis API",
    version="2.3.1",
    description="Upload failed-towers CSV + scenario → full coverage & ranking",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="data"), name="static")


@app.exception_handler(HTTPException)
async def http_exc(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} at {request.url}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exc(request: Request, exc: Exception):
    logger.exception(f"Unhandled error at {request.url}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please try again later."},
    )


@app.post("/run-ranking", response_model=dict)
async def run_ranking_api(
    file: UploadFile = File(...),
    scenario: str = Form("Default"),
    prefix_start: Optional[int] = Form(None),
    prefix_end:   Optional[int] = Form(None),
):
    # 1) Validate file
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # 2) Save to temp
    suffix = os.path.splitext(file.filename)[1] or ".csv"
    tmp = tempfile.NamedTemporaryFile(prefix="failed_", suffix=suffix, delete=False)
    try:
        tmp.write(await file.read())
        tmp.flush()
    except Exception as e:
        raise HTTPException(500, f"Failed to save upload: {e}")
    finally:
        tmp.close()

    # 3) Run pipeline (pass prefix_range if provided)
    try:
        pr = (prefix_start, prefix_end) if prefix_start is not None and prefix_end is not None else None
        output_csv = run_pipeline(
            failed_csv_path=tmp.name,
            disaster_type=scenario,
            prefix_range=pr,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(400, f"Missing data file: {fnf}")
    except ValueError as ve:
        raise HTTPException(422, f"Validation error: {ve}")
    except Exception as e:
        logger.exception("Pipeline error")
        raise HTTPException(500, f"Pipeline error: {e}")

    # 4) Read results
    results = []
    try:
        with open(output_csv, newline="") as f:
            for row in csv.DictReader(f):
                results.append(row)
    except Exception as e:
        logger.exception("Error reading output CSV")
        raise HTTPException(500, f"Error parsing result: {e}")

    # 5) Build response
    filename = os.path.basename(output_csv)
    download_url = f"/download/{filename}"
    response = {
        "message": "Ranking complete",
        "count": len(results),
        "results": results,
        "download_url": download_url,
    }
    logger.info("→ /run-ranking: %d rows (scenario=%s, prefix=%s)", len(results), scenario, pr)
    return response


@app.get("/download/{filename}")
async def download_csv(filename: str):
    path = os.path.join("output", filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type="text/csv", filename=filename)
