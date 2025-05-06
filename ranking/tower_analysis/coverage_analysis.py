import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm
import os

def calculate_exclusive_coverage(failed_coverage_dict, total_network_union):
    """
    For each failed tower, calculate its exclusive area by subtracting total network coverage (excluding itself).
    """
    exclusive_coverage = {}
    for tower_id, geom in tqdm(failed_coverage_dict.items(), desc="Calculating exclusive coverage"):
        # Remove coverage of all others (i.e., total network - this tower)
        other_coverage = total_network_union.difference(geom)
        exclusive = geom.difference(other_coverage)
        exclusive_coverage[tower_id] = exclusive
    return exclusive_coverage


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


def save_total_and_failed_exclusive_areas(all_towers_gdf, failed_ids, output_dir):
    """
    Save union of all towers' coverage, and the failed towers' total exclusive area
    (difference between total coverage and non-failed tower coverage).
    This function is for reference/visualization, not used in ranking.
    """
    os.makedirs(output_dir, exist_ok=True)

    total_path = os.path.join(output_dir, "total_network_coverage.shp")
    failed_exclusive_path = os.path.join(output_dir, "failed_total_exclusive_area.shp")

    # 1. Save total coverage
    if os.path.exists(total_path):
        print("total_network_coverage already exists.")
        total_union = gpd.read_file(total_path).unary_union
    else:
        print("Creating total_network_coverage...")
        total_union = all_towers_gdf.unary_union
        gpd.GeoDataFrame(geometry=[total_union], crs=all_towers_gdf.crs).to_file(total_path)
        print("total_network_coverage created.")

    # 2. Non-failed union
    non_failed_gdf = all_towers_gdf[~all_towers_gdf['tower_id'].isin(failed_ids)]
    non_failed_union = non_failed_gdf.unary_union

    # 3. Exclusive failed area = total - non-failed
    failed_exclusive_geom = total_union.difference(non_failed_union)
    gpd.GeoDataFrame(geometry=[failed_exclusive_geom], crs=all_towers_gdf.crs).to_file(failed_exclusive_path)
    print("failed_total_exclusive_area saved.")
