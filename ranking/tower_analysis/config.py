# config.py
# ---------------------------
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CRS = "EPSG:2193"

DISSOLVED_SHAPEFILE_DIR = os.path.join(BASE_DIR, "data", "dissolved_coverage")
FAILED_CSV = os.path.join(BASE_DIR, "data", "failed_towers", "failed_towers.csv")
POPULATION_FILE = os.path.join(BASE_DIR, "data", "population", "population_grid.shp")
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "tower_priority_ranking.csv")
TOTAL_COVERAGE_FILE = os.path.join(BASE_DIR, "output", "total_network_coverage.shp")
FAILED_TOTAL_EXCLUSIVE_FILE = os.path.join(BASE_DIR, "output", "failed_total_exclusive_area.shp")

FACILITY_FILES = [
    "data/facilities/fire_stations.shp",
    "data/facilities/hospitals.shp",
    "data/facilities/police_stations.shp"
]

WEIGHTS = {
    "hospital": 9,
    "police": 5,
    "fire_station": 7,
    "population_scale": 0.00015 * 3,
}

LOG_FILE = os.path.join(BASE_DIR, "output", "process.log")
