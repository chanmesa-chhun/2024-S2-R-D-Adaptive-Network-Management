import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from tqdm import tqdm


def calculate_exclusive_coverage_against_live(failed_towers_dict, live_union_geom):
    """
    Calculate exclusive coverage for each failed tower by subtracting the live tower coverage.

    Parameters:
        failed_towers_dict (dict): Dictionary of {tower_id: GeoDataFrame}
        live_union_geom (shapely.geometry): Unioned geometry of all live towers

    Returns:
        dict: {tower_id: exclusive geometry not covered by live towers}
    """
    exclusive_coverage = {}
    for tower_id, gdf in tqdm(failed_towers_dict.items(), desc="Calculating exclusive coverage"):
        tower_geom = gdf.unary_union
        exclusive_geom = tower_geom.difference(live_union_geom)
        exclusive_coverage[tower_id] = exclusive_geom
    return exclusive_coverage


def count_facilities_within_coverage(exclusive_coverage, facility_gdf):
    """
    Count facilities of each type within exclusive coverage areas.

    Parameters:
        exclusive_coverage (dict): {tower_id: shapely geometry}
        facility_gdf (GeoDataFrame): Facilities with 'type' column

    Returns:
        dict: {tower_id: {facility_type: count, ...}}
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
    Calculate both weighted and unweighted population within exclusive coverage areas.

    Parameters:
        exclusive_coverage (dict): {tower_id: shapely geometry}
        population_gdf (GeoDataFrame): Population grid with PopEst2023 column

    Returns:
        (dict, dict): weighted and unweighted population per tower_id
    """
    pop_weighted = {}
    pop_unweighted = {}
    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Calculating population"):
        intersected = gpd.overlay(population_gdf, gpd.GeoDataFrame(geometry=[geom], crs=population_gdf.crs), how='intersection')
        if not intersected.empty:
            intersected["area_ratio"] = intersected.area / population_gdf.loc[
                population_gdf.index.isin(intersected.index), "geometry"].area
            intersected["weighted_pop"] = intersected["PopEst2023"] * intersected["area_ratio"]
            pop_weighted[tower_id] = intersected["weighted_pop"].sum()
            pop_unweighted[tower_id] = intersected["PopEst2023"].sum()
        else:
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0
    return pop_weighted, pop_unweighted
