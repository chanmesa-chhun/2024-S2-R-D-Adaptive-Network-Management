import geopandas as gpd
from shapely.ops import unary_union
from shapely.prepared import prep
from tqdm import tqdm


def calculate_exclusive_coverage_batch_with_index(failed_towers_dict, live_union_geom, batch_size=10):
    """
    Calculate exclusive coverage for each failed tower using spatial index and batched difference.

    Parameters:
        failed_towers_dict (dict): {tower_id: GeoDataFrame}
        live_union_geom (shapely.geometry): Union of all live towers
        batch_size (int): Number of towers per batch for union and processing

    Returns:
        dict: {tower_id: exclusive geometry not covered by live towers}
    """
    exclusive_coverage = {}

    failed_ids = list(failed_towers_dict.keys())
    failed_geoms = [gdf.unary_union for gdf in failed_towers_dict.values()]
    crs = list(failed_towers_dict.values())[0].crs

    failed_gdf = gpd.GeoDataFrame({
        "tower_id": failed_ids,
        "geometry": failed_geoms
    }, crs=crs)

    prepared_live = prep(live_union_geom)

    for i in tqdm(range(0, len(failed_gdf), batch_size), desc="Batched exclusive coverage"):
        batch = failed_gdf.iloc[i:i + batch_size]
        for idx, row in batch.iterrows():
            tower_id = row["tower_id"]
            geom = row["geometry"]

            if prepared_live.intersects(geom):
                exclusive = geom.difference(live_union_geom)
            else:
                exclusive = geom

            exclusive_coverage[tower_id] = exclusive

    return exclusive_coverage


def count_facilities_within_coverage(exclusive_coverage, facility_gdf):
    """
    Count facilities of each type within exclusive coverage areas using spatial index.

    Parameters:
        exclusive_coverage (dict): {tower_id: shapely geometry}
        facility_gdf (GeoDataFrame): Facilities with 'type' column

    Returns:
        dict: {tower_id: {facility_type: count, ...}}
    """
    counts = {}
    sindex = facility_gdf.sindex

    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Counting facilities"):
        possible_matches_idx = list(sindex.intersection(geom.bounds))
        candidates = facility_gdf.iloc[possible_matches_idx]
        within = candidates[candidates.geometry.within(geom)]

        counts[tower_id] = {
            "police": (within["type"] == "police").sum(),
            "fire_station": (within["type"] == "fire_station").sum(),
            "hospital": (within["type"] == "hospital").sum(),
        }
    return counts


def calculate_population_within_coverage(exclusive_coverage, population_gdf):
    """
    Calculate weighted and unweighted population for each failed tower's exclusive area.

    Parameters:
        exclusive_coverage (dict): {tower_id: shapely geometry}
        population_gdf (GeoDataFrame): Population grid with 'PopEst2023' column

    Returns:
        (dict, dict): weighted and unweighted population per tower_id
    """
    # Ensure original grid area is preserved for weighting
    if "orig_area" not in population_gdf.columns:
        population_gdf = population_gdf.copy()
        population_gdf["orig_area"] = population_gdf.geometry.area

    pop_weighted = {}
    pop_unweighted = {}

    sindex = population_gdf.sindex  # spatial index for quick candidate selection

    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Calculating population"):
        # Select candidates via spatial index
        candidate_idx = list(sindex.intersection(geom.bounds))
        candidates = population_gdf.iloc[candidate_idx]

        # Perform precise geometry intersection
        intersection = gpd.overlay(
            candidates,
            gpd.GeoDataFrame(geometry=[geom], crs=population_gdf.crs),
            how="intersection"
        )

        if not intersection.empty:
            intersection["intersect_area"] = intersection.geometry.area
            intersection["area_ratio"] = intersection["intersect_area"] / intersection["orig_area"]
            intersection["weighted_pop"] = intersection["PopEst2023"] * intersection["area_ratio"]

            pop_weighted[tower_id] = intersection["weighted_pop"].sum()
            pop_unweighted[tower_id] = intersection["PopEst2023"].sum()
        else:
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0

    return pop_weighted, pop_unweighted