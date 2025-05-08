import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CRS = "EPSG:2193"

# 原始 shapefile 数据文件夹（新增）
RAW_SHP_DIR = os.path.join(BASE_DIR, "..", "data", "SHP")

# 合并后保存的 shapefile 文件夹
DISSOLVED_SHAPEFILE_DIR = os.path.join(BASE_DIR, "..", "data", "dissolved_coverage")

# 失效基站列表 CSV
FAILED_CSV = os.path.join(BASE_DIR, "..", "data", "failed_towers", "failed_towers.csv")

# 关键设施文件
FACILITY_FILES = {
    "hospital": os.path.join(BASE_DIR, "..", "data", "facilities", "hospitals.shp"),
    "fire_station": os.path.join(BASE_DIR, "..", "data", "facilities", "fire_stations.shp"),
    "police": os.path.join(BASE_DIR, "..", "data", "facilities", "police.shp")
}

# 人口数据
POPULATION_FILE = os.path.join(BASE_DIR, "..", "data", "population", "population.shp")

# 结果输出路径
OUTPUT_CSV = os.path.join(BASE_DIR, "..", "output", "tower_priority_ranking.csv")

# 预设权重配置
PRESET_WEIGHTS = {
    "Tsunami": {
        "hospital": 10,
        "police": 8,
        "fire_station": 9,
        "population_scale": 0.00015 * 3,
    },
    "Wildfire": {
        "hospital": 9,
        "police": 8,
        "fire_station": 10,
        "population_scale": 0.00015 * 3,
    },
    "Earthquake": {
        "hospital": 9,
        "police": 8,
        "fire_station": 10,
        "population_scale": 0.00015 * 3,
    },
    "Flood": {
        "hospital": 10,
        "police": 6,
        "fire_station": 9,
        "population_scale": 0.00015 * 3,
    },
    "Storm": {
        "hospital": 10,
        "police": 7,
        "fire_station": 9,
        "population_scale": 0.00015 * 3,
    },
    "Volcanic Eruption": {
        "hospital": 9,
        "police": 7,
        "fire_station": 10,
        "population_scale": 0.00015 * 3,
    },
    "custom": None
}
