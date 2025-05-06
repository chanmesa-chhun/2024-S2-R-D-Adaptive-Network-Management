### main.py

from tower_analysis.file_utils import load_failed_tower_geometries, load_facility_data, load_population_data
from tower_analysis.coverage_analysis import calculate_exclusive_coverage
from tower_analysis.ranking import rank_failed_towers, save_ranking_to_csv
import os

CRS = "EPSG:2193"

FAILED_TOWER_CSV = "data/failed_towers.csv"
DISSOLVED_DIR = "data/dissolved_coverage"
FACILITY_FILES = [
    "data/facilities/fire_stations.shp",
    "data/facilities/hospitals.shp",
    "data/facilities/police_stations.shp"
]
POPULATION_FILE = "data/population/population_grid.shp"
OUTPUT_CSV = "output/tower_priority_ranking.csv"

def main():
    print("Loading failed towers...")
    failed_towers = load_failed_tower_geometries(DISSOLVED_DIR, FAILED_TOWER_CSV, CRS)

    print("Loading facility data...")
    facility_gdf = load_facility_data(FACILITY_FILES, CRS)

    print("Loading population data...")
    population_gdf = load_population_data(POPULATION_FILE, CRS)

    print("Calculating exclusive coverage areas...")
    failed_exclusive_coverage = calculate_exclusive_coverage(failed_towers)

    print("Ranking failed towers...")
    tower_scores = rank_failed_towers(failed_exclusive_coverage, population_gdf, facility_gdf)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    save_ranking_to_csv(tower_scores, OUTPUT_CSV)

    print(f"Ranking saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
