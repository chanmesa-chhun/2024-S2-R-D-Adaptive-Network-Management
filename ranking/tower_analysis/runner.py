import os
from typing import List

from tower_analysis.file_utils import (
    load_failed_tower_geometries,
    load_facility_data,
    load_population_data,
)
from tower_analysis.coverage_analysis import calculate_exclusive_coverage
from tower_analysis.ranking import rank_failed_towers, save_ranking_to_csv

# Default configuration constants
CRS = "EPSG:2193"
FAILED_TOWER_CSV = "data/failed_towers.csv"
DISSOLVED_DIR = "data/dissolved_coverage"
FACILITY_FILES = [
    "data/facilities/fire_stations.shp",
    "data/facilities/hospitals.shp",
    "data/facilities/police_stations.shp",
]
POPULATION_FILE = "data/population/population_grid.shp"
OUTPUT_CSV = "output/tower_priority_ranking.csv"


def run_pipeline(
    failed_csv_path: str,
    dissolved_dir: str = DISSOLVED_DIR,
    facility_files: List[str] = FACILITY_FILES,
    pop_file: str = POPULATION_FILE,
    out_csv: str = OUTPUT_CSV,
    crs: str = CRS,
) -> str:
    """
    Executes the full tower ranking pipeline:
      1. Load failed tower geometries
      2. Load facility data (fire, hospitals, police)
      3. Load population grid data
      4. Compute exclusive coverage areas
      5. Rank towers and save results to CSV

    Args:
        failed_csv_path: Path to the CSV of failed towers (uploaded by user)
        dissolved_dir: Directory containing dissolved coverage shapefiles
        facility_files: List of facility shapefile paths
        pop_file: Path to population grid shapefile
        out_csv: Output CSV path for the final ranking
        crs: Coordinate reference system string

    Returns:
        The path to the saved CSV file
    """
    # 1) Load geometries of failed towers
    failed_towers = load_failed_tower_geometries(dissolved_dir, failed_csv_path, crs)

    # 2) Load facility data (fire stations, hospitals, police stations)
    facility_gdf = load_facility_data(facility_files, crs)

    # 3) Load population data
    population_gdf = load_population_data(pop_file, crs)

    # 4) Calculate exclusive coverage for each failed tower
    failed_exclusive_coverage = calculate_exclusive_coverage(failed_towers)

    # 5) Rank failed towers with population & facility weighting
    tower_scores = rank_failed_towers(failed_exclusive_coverage, population_gdf, facility_gdf)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    # Save ranking results to CSV
    save_ranking_to_csv(tower_scores, out_csv)

    return out_csv
