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
    "hospital": 9,        
    "police": 5,          
    "fire_station": 7,    
    "population_scale": 0.00015 * 3,   
}
