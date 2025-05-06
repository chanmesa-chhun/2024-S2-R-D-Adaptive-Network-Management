import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm

from tower_analysis.config import WEIGHTS, OUTPUT_CSV

def load_total_network_coverage(path: str, crs: str):
    """
    Load total network coverage shapefile from disk.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Total network coverage not found at {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf.set_crs(crs, inplace=True)
    elif gdf.crs.to_string() != crs:
        gdf = gdf.to_crs(crs)
    return gdf.unary_union  # Returns a (Multi)Polygon

def calculate_exclusive_coverage(failed_towers, total_network_union):
    """
    Compute exclusive area of each failed tower by subtracting the rest of total network.
    """
    exclusive_areas = {}
    for tower_id, gdf in tqdm(failed_towers.items(), desc="Calculating exclusive coverage"):
        tower_union = gdf.unary_union
        # Exclusive = tower_union - (total_network - tower_union)
        other_coverage = total_network_union.difference(tower_union)
        exclusive = tower_union.difference(other_coverage)
        exclusive_areas[tower_id] = exclusive
    return exclusive_areas

def count_facilities_within_coverage(exclusive_coverage, facility_gdf):
    """
    Count the number of hospitals, police, and fire stations within exclusive coverage.
    """
    counts = {}
    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Counting facilities"):
        within = facility_gdf[facility_gdf.geometry.within(geom)]
        counts[tower_id] = {
            "police": (within["type"] == "police").sum(),
            "fire_station": (within["type"] == "fire_station").sum(),
            "hospital": (within["type"] == "hospital").sum(),
        }
    return counts

def calculate_population_within_coverage(exclusive_coverage, population_gdf):
    """
    Calculate weighted and unweighted population in exclusive coverage areas.
    """
    pop_weighted = {}
    pop_unweighted = {}

    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Calculating population"):
        intersected = gpd.overlay(
            population_gdf,
            gpd.GeoDataFrame(geometry=[geom], crs=population_gdf.crs),
            how='intersection'
        )
        if not intersected.empty:
            intersected["area_ratio"] = intersected.area / intersected.geometry.area
            intersected["weighted_pop"] = intersected["PopEst2023"] * intersected["area_ratio"]
            pop_weighted[tower_id] = intersected["weighted_pop"].sum()
            pop_unweighted[tower_id] = intersected["PopEst2023"].sum()
        else:
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0

    return pop_weighted, pop_unweighted

def rank_failed_towers(failed_towers, population_gdf, facility_gdf, total_network_coverage_path, crs):
    """
    Calculate priority score for each failed tower based on population and facility counts.
    """
    total_network_union = load_total_network_coverage(total_network_coverage_path, crs)
    failed_exclusive_coverage = calculate_exclusive_coverage(failed_towers, total_network_union)

    facility_counts = count_facilities_within_coverage(failed_exclusive_coverage, facility_gdf)
    pop_weighted, pop_unweighted = calculate_population_within_coverage(failed_exclusive_coverage, population_gdf)

    scores = []
    for tower_id in failed_exclusive_coverage:
        facilities = facility_counts.get(tower_id, {})
        pop_w = pop_weighted.get(tower_id, 0)
        pop_unw = pop_unweighted.get(tower_id, 0)
        score = (
            facilities.get("police", 0) * WEIGHTS["police"] +
            facilities.get("fire_station", 0) * WEIGHTS["fire_station"] +
            facilities.get("hospital", 0) * WEIGHTS["hospital"] +
            pop_w * WEIGHTS["population_scale"]
        )
        scores.append({
            "tower_id": tower_id,
            "police": facilities.get("police", 0),
            "fire_station": facilities.get("fire_station", 0),
            "hospital": facilities.get("hospital", 0),
            "weighted_population": pop_w,
            "unweighted_population": pop_unw,
            "score": score
        })

    df = pd.DataFrame(scores)
    return df.sort_values(by="score", ascending=False), failed_exclusive_coverage

def save_ranking_to_csv(df, output_path=OUTPUT_CSV):
    """
    Save the ranking results to a CSV file.
    """
    df.to_csv(output_path, index=False)
    print(f"Ranking results saved to {output_path}")
