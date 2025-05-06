import os
import time
from tower_analysis.file_utils import load_failed_tower_geometries, load_facility_data, load_population_data
from tower_analysis.coverage_analysis import calculate_exclusive_coverage
from tower_analysis.ranking import rank_failed_towers, save_ranking_to_csv
from tower_analysis.logger_utils import setup_logger
import tower_analysis.config as config

def main():
    logger = setup_logger()
    start_time = time.time()
    try:
        logger.info("Step 1: Loading failed towers...")
        failed_towers = load_failed_tower_geometries(
            config.DISSOLVED_SHAPEFILE_DIR, config.FAILED_CSV, config.CRS
        )
        logger.info(f"Loaded {len(failed_towers)} failed towers.")

        logger.info("Step 2: Loading facility data...")
        facility_gdf = load_facility_data(list(config.FACILITY_FILES.values()), config.CRS)
        logger.info(f"Loaded {len(facility_gdf)} facilities.")

        logger.info("Step 3: Loading population data...")
        population_gdf = load_population_data(config.POPULATION_FILE, config.CRS)
        logger.info(f"Loaded {len(population_gdf)} population grid cells.")

        logger.info("Step 4: Calculating exclusive coverage areas...")
        failed_exclusive_coverage = calculate_exclusive_coverage(failed_towers)
        logger.info(f"Calculated exclusive coverage for {len(failed_exclusive_coverage)} towers.")

        logger.info("Step 5: Ranking failed towers...")
        tower_scores = rank_failed_towers(
            failed_exclusive_coverage, population_gdf, facility_gdf, config.WEIGHTS
        )

        logger.info("Step 6: Saving ranking result...")
        os.makedirs(os.path.dirname(config.OUTPUT_CSV), exist_ok=True)
        save_ranking_to_csv(tower_scores, config.OUTPUT_CSV)
        logger.info(f"Ranking saved to {config.OUTPUT_CSV}")

    except Exception as e:
        logger.exception("An error occurred during execution.")
    finally:
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"Script completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
