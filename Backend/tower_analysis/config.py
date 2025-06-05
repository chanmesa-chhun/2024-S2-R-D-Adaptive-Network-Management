import os

# Get the absolute path of the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Coordinate Reference System used throughout the project (NZGD2000 / NZTM2000)
CRS = "EPSG:2193"

# Directory where dissolved tower coverage shapefiles are stored
DISSOLVED_SHAPEFILE_DIR = os.path.join(BASE_DIR, "..", "data", "dissolved_coverage")

# Directory containing raw tower sector shapefiles (per-band, per-sector)
RAW_SHP_DIR = os.path.join(BASE_DIR, "..", "data", "SHP")

# Path to CSV file listing failed tower IDs
FAILED_CSV = os.path.join(BASE_DIR, "..", "data", "failed_towers", "failed_towers.csv")

# Paths to shapefiles for key facilities: hospitals, fire stations, and police
FACILITY_MERGED_FILE = os.path.join(BASE_DIR, "..", "data", "facilities", "facilities.shp")

# Path to the population grid shapefile
POPULATION_FILE = os.path.join(BASE_DIR, "..", "data", "population", "population.shp")

# Output directory for results
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")

# Output CSV path for tower priority ranking results
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "tower_priority_ranking.csv")

# Optional: prefix range for restricting live tower union (set to None to include all)
# e.g., ("001", "010") means only towers starting with 001 to 010 will be included in union

# Shapefile storing the merged coverage of all non-failed (live) towers
LIVE_NETWORK_COVERAGE_FILE = os.path.join(OUTPUT_DIR, "live_network_coverage.shp")

# Shapefile storing filtered facilities that are not covered by any live tower
FILTERED_FACILITY_FILE = os.path.join(OUTPUT_DIR, "filtered_facilities.shp")

# Preset weights for different disaster scenarios (used in ranking)
PRESET_WEIGHTS = {
    "Default": {
        "hospital": 10,
        "police": 6,
        "fire_station": 8,
        "population_scale": 0.005,
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
    "custom": None  # Used if user manually inputs weights
}