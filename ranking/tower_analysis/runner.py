# runner.py

import os
import time
import geopandas as gpd
from typing import Optional, Tuple

from tower_analysis.config import (
    RAW_SHP_DIR,
    DISSOLVED_SHAPEFILE_DIR,
    CRS,
    FACILITY_MERGED_FILE,
    POPULATION_FILE,
    OUTPUT_DIR,
    OUTPUT_CSV,
)
from tower_analysis.preprocessing import (
    merge_and_dissolve_shapefiles,
    generate_live_coverage_shapefile,
    filter_uncovered_facilities,
)
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


def run_pipeline(
    failed_csv_path: str,
    disaster_type: str = "Default",
    prefix_range: Optional[Tuple[int,int]] = None,
) -> str:
    """
    Full pipeline:
      0. Merge & dissolve raw shapefiles  (with optional prefix_range)
      0.1 Generate live coverage union (with optional prefix_range)
      0.2 Filter uncovered facilities
      1. Load failed towers
      2. Load filtered facilities
      3. Load population grid
      4. Compute exclusive coverage (batch with index)
      5. Fetch scenario weights
      6. Rank & save CSV
    """
    logger = setup_logger()
    start = time.time()

    # 0: Preprocess raw shapefiles → dissolved coverage
    logger.info("0: Merging & dissolving shapefiles (prefix=%s)", prefix_range)
    merge_and_dissolve_shapefiles(
        RAW_SHP_DIR,
        DISSOLVED_SHAPEFILE_DIR,
        logger,
        prefix_range=prefix_range,
    )

    # 0.1: Build or reuse live-coverage union
    logger.info("0.1: Generating live coverage union (prefix=%s)", prefix_range)
    live_cov_path = generate_live_coverage_shapefile(
        DISSOLVED_SHAPEFILE_DIR,
        failed_csv_path,
        CRS,
        OUTPUT_DIR,
        logger=logger,
        batch_size=200,
        prefix_range=prefix_range,
    )

    # 0.2: Filter out already-covered facilities
    logger.info("0.2: Filtering uncovered facilities")
    filtered_facility = filter_uncovered_facilities(
        live_cov_path,
        FACILITY_MERGED_FILE,
        failed_csv_path,
        CRS,
        OUTPUT_DIR,
        logger=logger,
    )

    # 1: Load failed-tower geometries
    logger.info("1: Loading failed towers")
    failed_towers = load_failed_tower_geometries(
        shapefile_dir=DISSOLVED_SHAPEFILE_DIR,
        failed_csv_path=failed_csv_path,
        crs=CRS,
    )

    # 2: Load only filtered facilities
    logger.info("2: Loading filtered facilities")
    facility_gdf = load_facility_data(
        file_paths=[filtered_facility],
        target_crs=CRS,
    )

    # 3: Load population grid
    logger.info("3: Loading population grid")
    population_gdf = load_population_data(
        population_path=POPULATION_FILE,
        target_crs=CRS,
    )

    # 4: Compute exclusive coverage
    logger.info("4: Calculating exclusive coverage (batch with index)")
    # read the live-union geometry we just generated
    union_geom = gpd.read_file(live_cov_path).geometry.iloc[0]
    failed_excl = calculate_exclusive_coverage_batch_with_index(
        failed_towers,
        union_geom,
        batch_size=200,
    )

    # 5: Fetch user-selected weights
    logger.info("5: Fetching weights for scenario '%s'", disaster_type)
    weights = get_user_weights(disaster_type)
    logger.info("   Using weights: %s", weights)

    # 6: Rank & save
    logger.info("6: Ranking and saving results")
    scores = rank_failed_towers(
        failed_exclusive_coverage=failed_excl,
        population_gdf=population_gdf,
        facility_gdf=facility_gdf,
        user_weights=weights,
        logger=logger,
    )
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    save_ranking_to_csv(scores, OUTPUT_CSV)

    elapsed = time.time() - start
    logger.info("Pipeline finished in %.2fs, output at %s", elapsed, OUTPUT_CSV)
    return OUTPUT_CSV
