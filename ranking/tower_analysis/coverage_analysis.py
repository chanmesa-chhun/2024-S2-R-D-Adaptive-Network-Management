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

    all_gdf = gpd.GeoDataFrame({'tower_id': tower_list, 'geometry': [gdf.unary_union for gdf in tower_gdfs]})
    all_gdf = all_gdf.set_crs(coverage_geometries[tower_list[0]].crs)

    sindex = all_gdf.sindex

    for idx, row in tqdm(all_gdf.iterrows(), total=len(all_gdf), desc="Calculating exclusive coverage"):
        tower_id = row['tower_id']
        geom = row['geometry']

        # find possible intersections
        possible_matches_idx = list(sindex.intersection(geom.bounds))
        possible_matches = all_gdf.iloc[possible_matches_idx]

        other_geoms = possible_matches[possible_matches['tower_id'] != tower_id]['geometry'].values

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
            "police": (within["type"] == "police").sum(),
            "fire_station": (within["type"] == "fire_station").sum(),
            "hospital": (within["type"] == "hospital").sum(),
        }
    return counts

def calculate_population_within_coverage(exclusive_coverage, population_gdf):
    pop_weighted = {}
    pop_unweighted = {}
    for tower_id, geom in tqdm(exclusive_coverage.items(), desc="Calculating population"):
        intersected = gpd.overlay(population_gdf, gpd.GeoDataFrame(geometry=[geom], crs=population_gdf.crs), how='intersection')
        if not intersected.empty:
            intersected["area_ratio"] = intersected.area / population_gdf.loc[population_gdf.index.isin(intersected.index), "geometry"].area
            intersected["weighted_pop"] = intersected["PopEst2023"] * intersected["area_ratio"]
            pop_weighted[tower_id] = intersected["weighted_pop"].sum()
            pop_unweighted[tower_id] = intersected["PopEst2023"].sum()
        else:
            pop_weighted[tower_id] = 0
            pop_unweighted[tower_id] = 0
    return pop_weighted, pop_unweighted