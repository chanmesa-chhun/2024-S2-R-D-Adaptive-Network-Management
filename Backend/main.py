# main.py
from typing import List
import logging
import csv
from io import StringIO

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import uvicorn

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("tower-api")

# --- Request schema for JSON-based POST ---
class TowerNamesRequest(BaseModel):
    tower_names: List[str]

    @validator("tower_names")
    def must_have_names(cls, v):
        if not v:
            raise ValueError("tower_names list cannot be empty.")
        for name in v:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("All tower names must be non-empty strings.")
        return v

# --- App init ---
app = FastAPI(
    title="Tower Names API",
    version="1.1.0",
    description="Accepts either a JSON list of tower codes or a CSV file upload."
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

# --- JSON endpoint (unchanged) ---
@app.post("/towers", response_model=dict)
async def handle_tower_names(req: TowerNamesRequest):
    tower_names = req.tower_names
    logger.info(f"Processing {len(tower_names)} tower(s) via JSON: {tower_names}")
    return {
        "message": "Successfully received tower names.",
        "count": len(tower_names),
        "towers": tower_names
    }

# --- New CSV upload endpoint ---
@app.post("/towers/upload-csv", response_model=dict)
async def upload_tower_csv(file: UploadFile = File(...)):
    """
    Accept a CSV file (header 'tower_name' or single-column) listing tower codes,
    e.g.:
        tower_name
        004-RWGR
        004-RTAI
    """
    # 1) Validate content type
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # 2) Read & decode
    try:
        raw = await file.read()
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "Could not decode file as UTF-8 text.")

    # 3) Parse CSV
    reader = csv.reader(StringIO(text))
    rows = list(reader)
    if not rows or all(len(r) == 0 for r in rows):
        raise HTTPException(400, "CSV is empty or malformed.")

    # 4) Determine whether there’s a header
    header = [h.strip().lower() for h in rows[0]]
    start_idx = 1 if "tower_name" in header else 0

    # 5) Extract first column as tower codes
    tower_names = []
    for idx, row in enumerate(rows[start_idx:], start=start_idx + 1):
        if not row or not row[0].strip():
            logger.warning(f"Skipping empty row {idx}")
            continue
        tower_names.append(row[0].strip())

    # 6) Validate same constraints as JSON
    if not tower_names:
        raise HTTPException(400, "No tower names found in CSV.")
    for t in tower_names:
        if not t:
            raise HTTPException(400, f"Invalid tower name in CSV: '{t}'")

    # 7) Business logic (echo back for now)
    logger.info(f"Processing {len(tower_names)} tower(s) via CSV upload: {tower_names}")
    return {
        "message": "Successfully received tower names via CSV.",
        "count": len(tower_names),
        "towers": tower_names
    }

# --- Run with Uvicorn ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
