#!/usr/bin/env python3
import logging

from tower_analysis.config import (
    RAW_SHP_DIR,
    DISSOLVED_SHAPEFILE_DIR,
    FAILED_CSV,
    CRS,
    OUTPUT_DIR,
)
from tower_analysis.preprocessing import (
    merge_and_dissolve_shapefiles,
    generate_live_coverage_shapefile,
)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger("precompute")

    # Step 0: Merge & dissolve every raw-sector shapefile into per-tower coverage
    logger.info("▶️  Precompute: merging & dissolving raw shapefiles…")
    merge_and_dissolve_shapefiles(
        raw_shp_dir=RAW_SHP_DIR,
        output_dir=DISSOLVED_SHAPEFILE_DIR,
        logger=logger
    )
    logger.info("✔️  All dissolved shapefiles are in place.")

    # (Optional) Step 0.1: build your “live network” union once for the default FAILED_CSV
    logger.info("▶️  Precompute: generating live‐network coverage union…")
    live_cov = generate_live_coverage_shapefile(
        dissolved_dir=DISSOLVED_SHAPEFILE_DIR,
        failed_csv_path=FAILED_CSV,
        crs=CRS,
        output_base_dir=OUTPUT_DIR,
        logger=logger,
        batch_size=200
    )
    logger.info(f"✔️  Live network coverage ready at: {live_cov}")

if __name__ == "__main__":
    main()
