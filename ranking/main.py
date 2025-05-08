import os
import time
from tower_analysis.file_utils import load_failed_tower_geometries, load_facility_data, load_population_data
from tower_analysis.coverage_analysis import calculate_exclusive_coverage
from tower_analysis.ranking import rank_failed_towers, save_ranking_to_csv, get_user_weights
from tower_analysis.logger_utils import setup_logger
from tower_analysis.preprocessing import merge_and_dissolve_shapefiles
import tower_analysis.config as config

def main():
    logger = setup_logger()
    start_time = time.time()
    try:
        logger.info("Step 0: Checking and preprocessing dissolved shapefiles if missing...")
        merge_and_dissolve_shapefiles(
            config.RAW_SHP_DIR,
            config.DISSOLVED_SHAPEFILE_DIR,
            logger=logger
        )

        # Step 1: Load failed towers
        logger.info("Step 1: Loading failed tower geometries...")
        failed_towers = load_failed_tower_geometries(
            shapefile_dir=config.DISSOLVED_SHAPEFILE_DIR,
            failed_csv_path=config.FAILED_CSV,
            crs=config.CRS
        )
        logger.info(f"Successfully loaded {len(failed_towers)} failed tower geometries.")

        # Step 2: Load facility data
        logger.info("Step 2: Loading facility data...")
        facility_gdf = load_facility_data(
            file_paths=list(config.FACILITY_FILES.values()),
            target_crs=config.CRS
        )
        logger.info(f"Successfully loaded {len(facility_gdf)} facilities across {facility_gdf['type'].nunique()} types.")


        # Step 3: Load population data
        logger.info("Step 3: Loading population data...")
        population_gdf = load_population_data(config.POPULATION_FILE, config.CRS)
        logger.info(f"Loaded {len(population_gdf)} population grid cells.")

        # Step 4: Calculate exclusive coverage areas
        logger.info("Step 4: Calculating exclusive coverage areas...")
        failed_exclusive_coverage = calculate_exclusive_coverage(failed_towers)
        logger.info(f"Calculated exclusive coverage for {len(failed_exclusive_coverage)} towers.")

        # Step 5: Ask user to choose preset or custom weights
        logger.info("Step 5: Getting user-defined or preset weights...")
        user_weights = get_user_weights()
        logger.info(f"Using weights: {user_weights}")

        # Step 6: Rank failed towers
        logger.info("Step 6: Ranking failed towers...")
        tower_scores = rank_failed_towers(
            failed_exclusive_coverage, population_gdf, facility_gdf, user_weights
        )

        # Step 7: Save result
        logger.info("Step 7: Saving ranking result...")
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
