import os
import time
import geopandas as gpd

from tower_analysis.config import (
    RAW_SHP_DIR,
    DISSOLVED_SHAPEFILE_DIR,
    FAILED_CSV,            # we’ll ignore this default and use the passed-in path
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
from tower_analysis.coverage_analysis import calculate_exclusive_coverage
from tower_analysis.ranking import (
    rank_failed_towers,
    save_ranking_to_csv,
    get_user_weights,
)
from tower_analysis.logger_utils import setup_logger


def run_pipeline(failed_csv_path: str, disaster_type: str = "Default") -> str:
    """
    Full pipeline:
      0. Merge & dissolve raw shapefiles
      0.1 Generate live coverage union
      0.2 Filter uncovered facilities
      1. Load failed towers
      2. Load filtered facilities
      3. Load population grid
      4. Compute exclusive coverage
      5. Fetch scenario weights
      6. Rank & save CSV
    """
    logger = setup_logger()
    start = time.time()

    # 0: Preprocess raw shapefiles → dissolved coverage
    logger.info("0: Merging & dissolving shapefiles")
    merge_and_dissolve_shapefiles(
        RAW_SHP_DIR,
        DISSOLVED_SHAPEFILE_DIR,
        logger
    )

    # 0.1: Build or reuse live-coverage union
    logger.info("0.1: Generating live coverage union")
    live_cov = generate_live_coverage_shapefile(
        DISSOLVED_SHAPEFILE_DIR,
        failed_csv_path,
        CRS,
        OUTPUT_DIR,
        logger=logger,
        batch_size=200,
    )

    # 0.2: Filter out already-covered facilities
    logger.info("0.2: Filtering uncovered facilities")
    filtered_facility = filter_uncovered_facilities(
        live_cov,
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
    logger.info("4: Calculating exclusive coverage")
    failed_excl = calculate_exclusive_coverage(failed_towers)

    # 5: Fetch user-selected weights
    logger.info(f"5: Fetching weights for scenario '{disaster_type}'")
    weights = get_user_weights(disaster_type)
    logger.info(f"Using weights: {weights}")

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
    logger.info(f"Pipeline finished in {elapsed:.2f}s, output at {OUTPUT_CSV}")
    return OUTPUT_CSV
