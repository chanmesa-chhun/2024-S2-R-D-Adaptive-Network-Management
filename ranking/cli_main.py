import os
import time
import geopandas as gpd
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
)
import tower_analysis.config as config

def main():
    logger = setup_logger()
    start_time = time.time()

    try:
        # Step 0: Preprocess
        logger.info("Step 0: Preprocessing dissolved shapefiles...")
        merge_and_dissolve_shapefiles(config.RAW_SHP_DIR, config.DISSOLVED_SHAPEFILE_DIR, logger)

        # Step 0.1: Generate/reuse live tower union
        logger.info("Step 0.1: Generating live tower coverage union...")
        t0 = time.time()
        live_coverage_path = generate_live_coverage_shapefile(
            config.DISSOLVED_SHAPEFILE_DIR,
            config.FAILED_CSV,
            config.CRS,
            config.OUTPUT_DIR,
            logger=logger,
            batch_size=200
        )
        logger.info(f"Live coverage generated in {time.time() - t0:.2f}s")

        # Step 0.2: Filter uncovered facilities
        logger.info("Step 0.2: Filtering uncovered facilities...")
        t0 = time.time()
        filtered_facility_file = filter_uncovered_facilities(
            live_coverage_path,
            config.FACILITY_MERGED_FILE,
            config.FAILED_CSV,
            config.CRS,
            config.OUTPUT_DIR,
            logger=logger
        )
        logger.info(f"Facility filtering done in {time.time() - t0:.2f}s")

        # Step 1: Load failed tower geometries
        logger.info("Step 1: Loading failed tower geometries...")
        failed_towers = load_failed_tower_geometries(
            shapefile_dir=config.DISSOLVED_SHAPEFILE_DIR,
            failed_csv_path=config.FAILED_CSV,
            crs=config.CRS
        )
        logger.info(f"Loaded {len(failed_towers)} failed tower geometries.")

        # Step 2: Load filtered facilities
        logger.info("Step 2: Loading filtered facility data...")
        facility_gdf = load_facility_data(
            file_paths=[filtered_facility_file],
            target_crs=config.CRS
        )
        logger.info(f"Loaded {len(facility_gdf)} filtered facilities.")

        # Step 3: Load population grid
        logger.info("Step 3: Loading population data...")
        population_gdf = load_population_data(config.POPULATION_FILE, config.CRS)
        logger.info(f"Loaded {len(population_gdf)} population grid cells.")

       # Step 4: Exclusive coverage using spatial index + batch
        logger.info("Step 4: Calculating exclusive coverage areas (batched with index)...")
        t0 = time.time()
        live_union_geom = gpd.read_file(live_coverage_path).geometry.iloc[0]
        failed_exclusive_coverage = calculate_exclusive_coverage_batch_with_index(
        failed_towers,
        live_union_geom,
        batch_size=20
        )
        logger.info(f"Exclusive coverage calculated in {time.time() - t0:.2f}s")

        # ✅ NEW: Export individual exclusive shapefiles for inspection
        exclusive_output_dir = os.path.join(config.OUTPUT_DIR, "exclusive_areas")
        os.makedirs(exclusive_output_dir, exist_ok=True)

        logger.info(f"Exporting individual exclusive shapefiles to: {exclusive_output_dir}")
        for tower_id, geom in failed_exclusive_coverage.items():
            try:
                gdf = gpd.GeoDataFrame(
                    {"tower_id": [tower_id]}, 
                    geometry=[geom], 
                    crs=config.CRS
                )
                output_path = os.path.join(exclusive_output_dir, f"{tower_id}_exclusive.shp")
                gdf.to_file(output_path)
            except Exception as e:
                logger.warning(f"Failed to export shapefile for tower {tower_id}: {e}")

        # Step 5: Weights
        logger.info("Step 5: Getting weights...")
        user_weights = get_user_weights()
        logger.info(f"Using weights: {user_weights}")

        # Step 6: Ranking
        logger.info("Step 6: Ranking failed towers...")
        t0 = time.time()
        tower_scores = rank_failed_towers(
            failed_exclusive_coverage,
            population_gdf,
            facility_gdf,
            user_weights
        )
        logger.info(f"Ranking completed in {time.time() - t0:.2f}s")

        # Step 7: Save results
        logger.info("Step 7: Saving results...")
        os.makedirs(os.path.dirname(config.OUTPUT_CSV), exist_ok=True)
        save_ranking_to_csv(tower_scores, config.OUTPUT_CSV)
        logger.info(f"Ranking saved to {config.OUTPUT_CSV}")

    except Exception as e:
        logger.exception("An error occurred during execution.")
    finally:
        logger.info(f"Script completed in {time.time() - start_time:.2f} seconds.")
        

if __name__ == "__main__":
    main()