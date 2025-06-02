# tower_analysis/config.py

import os

# Base directory of this module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Coordinate Reference System (NZTM2000)
CRS = "EPSG:2193"

# Input paths
RAW_SHP_DIR            = os.path.join(BASE_DIR, "..", "data", "SHP")
DISSOLVED_SHAPEFILE_DIR = os.path.join(BASE_DIR, "..", "data", "dissolved_coverage")
FAILED_CSV             = os.path.join(BASE_DIR, "..", "data", "failed_towers", "failed_towers.csv")
FACILITY_MERGED_FILE   = os.path.join(BASE_DIR, "..", "data", "facilities", "facilities.shp")
POPULATION_FILE        = os.path.join(BASE_DIR, "..", "data", "population", "population.shp")

# Output dirs & files
OUTPUT_DIR                  = os.path.join(BASE_DIR, "..", "output")
OUTPUT_CSV                  = os.path.join(OUTPUT_DIR, "tower_priority_ranking.csv")
LIVE_NETWORK_COVERAGE_FILE  = os.path.join(OUTPUT_DIR, "live_network_coverage.shp")
FILTERED_FACILITY_FILE      = os.path.join(OUTPUT_DIR, "filtered_facilities.shp")

# Preset weights for different disaster scenarios
PRESET_WEIGHTS = {
    "Default": {
        "hospital": 10,
        "police": 6,
        "fire_station": 8,
        "population_scale": 0.0005,
    },
    "Tsunami": {
        "hospital": 10,
        "police": 8,
        "fire_station": 9,
        "population_scale": 0.0015 * 3,
    },
    "Wildfire": {
        "hospital": 9,
        "police": 8,
        "fire_station": 10,
        "population_scale": 0.0015 * 3,
    },
    "Earthquake": {
        "hospital": 9,
        "police": 8,
        "fire_station": 10,
        "population_scale": 0.0015 * 3,
    },
    "Flood": {
        "hospital": 10,
        "police": 6,
        "fire_station": 9,
        "population_scale": 0.0015 * 3,
    },
    "Storm": {
        "hospital": 10,
        "police": 7,
        "fire_station": 9,
        "population_scale": 0.0015 * 3,
    },
    "Volcanic Eruption": {
        "hospital": 9,
        "police": 7,
        "fire_station": 10,
        "population_scale": 0.0015 * 3,
    },
    "custom": None,
}
