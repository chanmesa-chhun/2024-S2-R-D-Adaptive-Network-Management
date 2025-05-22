# coverage_analysis.py

import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm


def calculate_exclusive_coverage(coverage_geometries):
    """
    Optimized by spatial index, the union-difference operation is only performed on towers with actual intersections instead of finding all the intersection areas.
    """
    exclusive_coverage = {}
    tower_list = list(coverage_geometries.keys())
    tower_gdfs = [coverage_geometries[k] for k in tower_list]
    
    # Create a GeoDataFrame for spatial indexing
    all_gdf = gpd.GeoDataFrame(
        {'tower_id': tower_list, 'geometry': [gdf.unary_union for gdf in tower_gdfs]}
    )
    all_gdf = all_gdf.set_crs(coverage_geometries[tower_list[0]].crs)
    sindex = all_gdf.sindex

    for idx, row in tqdm(all_gdf.iterrows(), total=len(all_gdf), desc="Calculating exclusive coverage"):
        tower_id = row['tower_id']
        geom = row['geometry']

        # find possible intersections
        possible_idx = list(sindex.intersection(geom.bounds))
        possible = all_gdf.iloc[possible_idx]
        other_geoms = possible[possible['tower_id'] != tower_id]['geometry'].values

        if len(other_geoms) == 0:
            exclusive_geom = geom
        else:
            union_others = gpd.GeoSeries(other_geoms).unary_union
            exclusive_geom = geom.difference(union_others)

        exclusive_coverage[tower_id] = exclusive_geom

    return exclusive_coverage


def count_facilities_within_coverage(exclusive_coverage, facility_gdf):
    counts = {}
    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Counting facilities"):
        within = facility_gdf[facility_gdf.geometry.within(geom)]
        counts[tower_id] = {
            'police': (within['type'] == 'police').sum(),
            'fire_station': (within['type'] == 'fire_station').sum(),
            'hospital': (within['type'] == 'hospital').sum(),
        }
    return counts


def calculate_population_within_coverage(exclusive_coverage, population_gdf):
    """
    For each tower's exclusive area:
    - Calculate weighted population = sum of (area_ratio * PopEst)
    - Calculate unweighted population = sum of unique grids where area_ratio > threshold
    """
    pop_weighted = {}
    pop_unweighted = {}
 
    # --- Prepare required fields ---
    if 'grid_id' not in population_gdf.columns:
        population_gdf['grid_id'] = population_gdf.index.astype(str)
    if 'Shape_Area' not in population_gdf.columns:
        population_gdf['Shape_Area'] = population_gdf.geometry.area
    # Find the population estimate field dynamically
    pop_field_candidates = [c for c in population_gdf.columns if 'PopEst' in c]
    if not pop_field_candidates:
        raise ValueError("No PopEst field (like PopEst2023) found.")
    pop_field = pop_field_candidates[-1]
    crs = population_gdf.crs

    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Calculating population"):
        if geom.is_empty or geom.area == 0:
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0
            continue
 
        # Perform intersection
        try:
            tower_gdf = gpd.GeoDataFrame({'geometry': [geom]}, crs=crs)
            intersection = gpd.overlay(population_gdf, tower_gdf, how='intersection')
        except Exception as e:
            print(f"Warning: overlay failed for tower {tower_id}: {e}")
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0
            continue
 
        if intersection.empty:
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0
            continue
 
        # Calculate area and ratio
        intersection['intersect_area'] = intersection.geometry.area
        intersection['area_ratio'] = intersection['intersect_area'] / intersection['Shape_Area']
        intersection['weighted_pop'] = intersection['area_ratio'] * intersection[pop_field]
 
        # Filter out tiny overlaps
        filtered = intersection[intersection['area_ratio'] > 0.005].copy()
 
        # Weighted population: sum of weighted values
        pop_weighted[tower_id] = filtered['weighted_pop'].sum()
 
        # Unweighted population: sum unique grids
        unique_grids = filtered.drop_duplicates(subset='grid_id')
        pop_unweighted[tower_id] = unique_grids[pop_field].sum()
 
    return pop_weighted, pop_unweighted
