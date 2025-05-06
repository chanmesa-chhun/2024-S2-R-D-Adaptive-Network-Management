import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CRS = "EPSG:2193"

DISSOLVED_SHAPEFILE_DIR = os.path.join(BASE_DIR, "..", "data", "dissolved_coverage")

FAILED_CSV = os.path.join(BASE_DIR, "..", "data", "failed_towers", "failed_towers.csv")

FACILITY_FILES = {
    "hospital": os.path.join(BASE_DIR, "..", "data", "facilities", "hospitals.shp"),
    "fire_station": os.path.join(BASE_DIR, "..", "data", "facilities", "fire_stations.shp"),
    "police": os.path.join(BASE_DIR, "..", "data", "facilities", "police.shp")
}

POPULATION_FILE = os.path.join(BASE_DIR, "..", "data", "population", "population.shp")

OUTPUT_CSV = os.path.join(BASE_DIR, "..", "output", "tower_priority_ranking.csv")

WEIGHTS = {
    "hospital": 9,        # 每个 hospital +9 分
    "police": 5,          # 每个 police station +5 分
    "fire_station": 7,    # 每个 fire station +7 分
    "population_scale": 0.0015,   # 人口加权比例（人口数 * 0.0015）
}

# import os

# # Base directory
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # CRS
# CRS = "EPSG:2193"

# # Input paths
# FAILED_CSV = os.path.join(BASE_DIR, "C:\Users\Jeremy\Desktop\COMP703\2degrees North island data\failed_towers", "data", "failed_towers.csv")
# RAW_SHP_DIR = os.path.join(BASE_DIR, "C:\Users\Jeremy\Desktop\COMP703\2degrees North island data\SHP", "data", "raw_shapefiles")
# MERGED_DIR = os.path.join(BASE_DIR, "..", "data", "merged_output")
# DISSOLVED_DIR = os.path.join(BASE_DIR, "..", "data", "dissolved_output")
# POPULATION_SHP = os.path.join(BASE_DIR, "C:\Users\Jeremy\Desktop\COMP703\2degrees North island data\SHP", "data", "new-zealand-estimated-resident-population-grid-250-metre.shp")
# FACILITY_SHP = os.path.join(BASE_DIR, "C:\Users\Jeremy\Desktop\COMP703\2degrees North island data\SHP", "data", "facilities.shp")

# # Output paths
# LIVE_COVERAGE_PATH = os.path.join(BASE_DIR, "..", "output", "live_network_coverage.shp")
# OUTPUT_RANKING_CSV = os.path.join(BASE_DIR, "..", "output", "ranking.csv")