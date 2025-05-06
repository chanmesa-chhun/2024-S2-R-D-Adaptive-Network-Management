# file_utils.py

import os
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

def read_failed_towers(failed_csv_path):
    df = pd.read_csv(failed_csv_path)
    return set(df["tower_id"].tolist())

def list_shapefiles_from_dir(directory):
    return [f for f in os.listdir(directory) if f.endswith(".shp")]

def load_failed_tower_geometries(dissolved_dir, failed_csv_path, crs):
    failed_towers = read_failed_towers(failed_csv_path)
    shapefiles = list_shapefiles_from_dir(dissolved_dir)
    geometries = {}

    for shp in shapefiles:
        tower_id = shp.replace("-Dissolved.shp", "")
        if tower_id in failed_towers:
            gdf = gpd.read_file(os.path.join(dissolved_dir, shp))
            if gdf.crs is None:
                gdf = gdf.set_crs(crs)
            elif gdf.crs.to_string() != crs:
                gdf = gdf.to_crs(crs)
            geometries[tower_id] = gdf.unary_union
    return geometries  # Dict[str, shapely.geometry]

def load_all_tower_geometries(dissolved_dir, crs):
    """
    Load all towers (including failed and non-failed) as a GeoDataFrame with tower_id.
    """
    shapefiles = list_shapefiles_from_dir(dissolved_dir)
    rows = []

    for shp in shapefiles:
        tower_id = shp.replace("-Dissolved.shp", "")
        gdf = gpd.read_file(os.path.join(dissolved_dir, shp))
        if gdf.crs is None:
            gdf = gdf.set_crs(crs)
        elif gdf.crs.to_string() != crs:
            gdf = gdf.to_crs(crs)
        for geom in gdf.geometry:
            rows.append({"tower_id": tower_id, "geometry": geom})

    return gpd.GeoDataFrame(rows, crs=crs)

def load_facility_data(facility_paths, target_crs):
    dfs = []
    for path in facility_paths:
        gdf = gpd.read_file(path)
        gdf = gdf.to_crs(target_crs)

        if "facility_t" not in gdf.columns:
            raise ValueError(f"Missing 'facility_t' column in {path}")

        gdf["facility_t"] = gdf["facility_t"].str.lower().str.strip()

        def classify_type(text):
            if "police" in text:
                return "police"
            elif "fire" in text:
                return "fire_station"
            elif "hospital" in text:
                return "hospital"
            else:
                return "other"

        gdf["type"] = gdf["facility_t"].apply(classify_type)
        gdf = gdf[gdf["type"].isin(["police", "fire_station", "hospital"])]
        dfs.append(gdf)

    return gpd.GeoDataFrame(pd.concat(dfs, ignore_index=True), crs=target_crs)

def load_population_data(population_path, target_crs):
    gdf = gpd.read_file(population_path)
    gdf = gdf.to_crs(target_crs)
    if "PopEst2023" not in gdf.columns:
        raise ValueError("Population grid missing 'PopEst2023' column")
    return gdf

def save_failed_total_exclusive_area(failed_exclusive_coverage, dissolved_dir, failed_csv_path, crs):
    """
    Save failed_total_exclusive_area.shp based on total - non_failed coverage.
    """
    output_path = "output/failed_total_exclusive_area.shp"
    total_path = "output/total_network_coverage.shp"
    os.makedirs("output", exist_ok=True)

    print("[INFO] Saving failed_total_exclusive_area...")

    # Load all towers
    all_gdf = load_all_tower_geometries(dissolved_dir, crs)
    failed_ids = read_failed_towers(failed_csv_path)

    # Compute total union
    if os.path.exists(total_path):
        print(" - Using existing total_network_coverage.shp")
        total_union = gpd.read_file(total_path).unary_union
    else:
        print(" - Creating total_network_coverage.shp")
        total_union = all_gdf.unary_union
        gpd.GeoDataFrame(geometry=[total_union], crs=crs).to_file(total_path)
        print(" - Saved to total_network_coverage.shp")

    # Compute non-failed union
    non_failed_gdf = all_gdf[~all_gdf["tower_id"].isin(failed_ids)]
    non_failed_union = non_failed_gdf.unary_union

    # Exclusive = total - non-failed
    failed_exclusive_geom = total_union.difference(non_failed_union)
    result_gdf = gpd.GeoDataFrame({"tower_id": ["FAILED_EXCLUSIVE_AREA"], "geometry": [failed_exclusive_geom]}, crs=crs)

    result_gdf.to_file(output_path)
    print(f"[INFO] Exclusive failed area saved to {output_path}")
