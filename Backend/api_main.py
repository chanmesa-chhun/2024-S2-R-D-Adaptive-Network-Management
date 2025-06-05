from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import shutil
import os
import time
import geopandas as gpd
import pandas as pd
from tower_analysis.file_utils import (
    load_failed_tower_geometries,
    load_facility_data,
    load_population_data,
)
from tower_analysis.coverage_analysis import (
    calculate_exclusive_coverage_batch_with_index,
)
from tower_analysis.ranking import (
    rank_failed_towers,
    save_ranking_to_csv,
    get_user_weights,
)
from tower_analysis.logger_utils import setup_logger
from tower_analysis.preprocessing import (
    merge_and_dissolve_shapefiles,
    generate_live_coverage_shapefile,
    filter_uncovered_facilities,
    get_prefix_bounds,
)
from fastapi.middleware.cors import CORSMiddleware
import tower_analysis.config as config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(
    failed_towers: UploadFile = File(...),
    disaster_type: str = Form(...),
    prefix_start: str = Form(None),
    prefix_end: str = Form(None)
):
    logger = setup_logger()
    start_time = time.time()

    try:
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        os.makedirs("static", exist_ok=True)

        failed_csv_path = os.path.join(config.OUTPUT_DIR, failed_towers.filename)
        with open(failed_csv_path, "wb") as buffer:
            shutil.copyfileobj(failed_towers.file, buffer)

        min_prefix, max_prefix = get_prefix_bounds(config.DISSOLVED_SHAPEFILE_DIR)
        prefix_start = prefix_start.zfill(3) if prefix_start else min_prefix
        prefix_end = prefix_end.zfill(3) if prefix_end else max_prefix
        prefix_range = (prefix_start, prefix_end)

        logger.info(f"Received analysis request for disaster type: {disaster_type}")
        logger.info(f"Limiting live tower coverage to prefix range: {prefix_range}")

        merge_and_dissolve_shapefiles(config.RAW_SHP_DIR, config.DISSOLVED_SHAPEFILE_DIR, logger, prefix_range)

        live_coverage_path = generate_live_coverage_shapefile(
            config.DISSOLVED_SHAPEFILE_DIR,
            failed_csv_path,
            config.CRS,
            config.OUTPUT_DIR,
            logger,
            batch_size=200,
            prefix_range=prefix_range
        )

        filtered_facility_file = filter_uncovered_facilities(
            live_coverage_path,
            config.FACILITY_MERGED_FILE,
            failed_csv_path,
            config.CRS,
            config.OUTPUT_DIR,
            logger
        )

        failed_towers_gdf = load_failed_tower_geometries(config.DISSOLVED_SHAPEFILE_DIR, failed_csv_path, config.CRS)
        facility_gdf = load_facility_data([filtered_facility_file], config.CRS)
        population_gdf = load_population_data(config.POPULATION_FILE, config.CRS)

        live_union_geom = gpd.read_file(live_coverage_path).geometry.iloc[0]
        failed_exclusive_coverage = calculate_exclusive_coverage_batch_with_index(
            failed_towers_gdf,
            live_union_geom,
            batch_size=20
        )

        exclusive_output_dir = os.path.join(config.OUTPUT_DIR, "exclusive_areas")
        os.makedirs(exclusive_output_dir, exist_ok=True)
        for tower_id, geom in failed_exclusive_coverage.items():
            try:
                gdf = gpd.GeoDataFrame({"tower_id": [tower_id]}, geometry=[geom], crs=config.CRS)
                output_path = os.path.join(exclusive_output_dir, f"{tower_id}_exclusive.shp")
                gdf.to_file(output_path)
            except Exception as e:
                logger.warning(f"Failed to export shapefile for tower {tower_id}: {e}")

        user_weights = get_user_weights(disaster_type)
        tower_scores = rank_failed_towers(
            failed_exclusive_coverage,
            population_gdf,
            facility_gdf,
            user_weights
        )

        os.makedirs(os.path.dirname(config.OUTPUT_CSV), exist_ok=True)
        save_ranking_to_csv(tower_scores, config.OUTPUT_CSV)

        # Copy result to static folder for download
        download_filename = os.path.basename(config.OUTPUT_CSV)
        static_path = os.path.join("static", download_filename)
        shutil.copyfile(config.OUTPUT_CSV, static_path)

        # Return parsed rows + download URL
        results = tower_scores.to_dict(orient="records")
        duration = time.time() - start_time
        return JSONResponse({
            "message": "Analysis complete",
            "duration": duration,
            "results": results,
            "download_url": f"/static/{download_filename}"
        })

    except Exception as e:
        logger.exception("Error during analysis")
        return JSONResponse(status_code=500, content={"error": str(e)})
