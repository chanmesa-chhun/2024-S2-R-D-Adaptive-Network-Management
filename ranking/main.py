# main.py
import geopandas as gpd
import os
import time
from tower_analysis.file_utils import (
    load_failed_tower_geometries,
    load_all_tower_geometries,
    load_facility_data,
    load_population_data,
)
from tower_analysis.coverage_analysis import (
    calculate_exclusive_coverage,
    count_facilities_within_coverage,
    calculate_population_within_coverage,
    save_total_and_failed_exclusive_areas,
)
from tower_analysis.ranking import rank_failed_towers, save_ranking_to_csv

# ====== Configuration ======
CRS = "EPSG:2193"

FAILED_TOWER_CSV = "data/failed_towers.csv"
DISSOLVED_DIR = "data/dissolved_coverage"
FACILITY_FILES = [
    "data/facilities/fire_stations.shp",
    "data/facilities/hospitals.shp",
    "data/facilities/police_stations.shp"
]
POPULATION_FILE = "data/population/population_grid.shp"
OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "tower_priority_ranking.csv")
TOTAL_NETWORK_COVERAGE_PATH = os.path.join(OUTPUT_DIR, "total_network_coverage.shp")

def main():
    start = time.time()
    print("[INFO] Loading all tower geometries...")
    all_towers_gdf = load_all_tower_geometries(DISSOLVED_DIR, CRS)

    print("[INFO] Loading failed towers...")
    failed_towers = load_failed_tower_geometries(DISSOLVED_DIR, FAILED_TOWER_CSV, CRS)

    print("[INFO] Loading facility data...")
    facility_gdf = load_facility_data(FACILITY_FILES, CRS)

    print("[INFO] Loading population data...")
    population_gdf = load_population_data(POPULATION_FILE, CRS)

    print("[INFO] Preparing total network coverage union...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(TOTAL_NETWORK_COVERAGE_PATH):
        print(" - Using existing total_network_coverage.shp")
        total_union = gpd.read_file(TOTAL_NETWORK_COVERAGE_PATH).unary_union
    else:
        print(" - Creating total_network_coverage.shp")
        total_union = all_towers_gdf.unary_union
        gpd.GeoDataFrame(geometry=[total_union], crs=CRS).to_file(TOTAL_NETWORK_COVERAGE_PATH)

    print("[INFO] Calculating exclusive coverage areas (new logic)...")
    failed_exclusive_coverage = calculate_exclusive_coverage(failed_towers, total_union)

    print("[INFO] Ranking failed towers...")
    tower_scores = rank_failed_towers(failed_exclusive_coverage, population_gdf, facility_gdf)

    print("[INFO] Saving ranking CSV...")
    save_ranking_to_csv(tower_scores, OUTPUT_CSV)

    print("[INFO] Saving failed_total_exclusive_area...")
    failed_ids = list(failed_towers.keys())
    save_total_and_failed_exclusive_areas(all_towers_gdf, failed_ids, OUTPUT_DIR)

    print(f"[INFO] All done! Time elapsed: {time.time() - start:.2f} seconds")

if __name__ == "__main__":
    main()
