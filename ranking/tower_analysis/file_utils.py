import geopandas as gpd
import pandas as pd
import os
from tower_analysis.config import FILTERED_FACILITY_FILE, FACILITY_MERGED_FILE

def load_failed_tower_geometries(shapefile_dir, failed_csv_path, crs):
    """
    Load dissolved coverage shapefiles for failed towers listed in a CSV file.

    Returns:
        dict: {tower_id: GeoDataFrame}
    """
    failed_ids = pd.read_csv(failed_csv_path)['tower_id'].astype(str).tolist()
    tower_geometries = {}

    for tower_id in failed_ids:
        filename = f"{tower_id}-Dissolved.shp"
        path = os.path.join(shapefile_dir, filename)
        if not os.path.exists(path):
            print(f"Warning: Shapefile for tower {tower_id} not found at {path}.")
            continue
        try:
            gdf = gpd.read_file(path)
            if gdf.crs and gdf.crs != crs:
                gdf = gdf.to_crs(crs)
            elif not gdf.crs:
                gdf.set_crs(crs, inplace=True)
            tower_geometries[tower_id] = gdf
        except Exception as e:
            print(f"Error reading shapefile {filename}: {e}")

    return tower_geometries


def load_facility_data(file_paths, target_crs):
    """
    Load the pre-merged facilities.shp with standardized 'type' field.

    Parameters:
        file_paths (list): Expect a single path: merged facilities file
        target_crs (str): Target coordinate reference system (e.g. EPSG:2193)

    Returns:
        GeoDataFrame
    """
    if not file_paths or not os.path.exists(file_paths[0]):
        raise FileNotFoundError("Merged facility file not found.")

    gdf = gpd.read_file(file_paths[0])

    # Assume it’s already cleaned, just check CRS
    if gdf.crs and gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)
    elif not gdf.crs:
        gdf.set_crs(target_crs, inplace=True)

    if 'type' not in gdf.columns:
        raise ValueError("Expected 'type' column missing from facilities file.")

    return gdf


def load_population_data(population_path, target_crs):
    """
    Load population grid shapefile and convert to target CRS.
    """
    gdf = gpd.read_file(population_path)
    # 1) Raw CRS check
    print("🔍 raw pop_gdf.crs:", gdf.crs)

    # 2) Reproject
    if gdf.crs and gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)
    elif not gdf.crs:
        gdf.set_crs(target_crs, inplace=True)

    # 3) Post-reproject check & sample area
    print("🔍 reprojected pop_gdf.crs:", gdf.crs)
    print("🔍 sample cell area (m²):", gdf.geometry.iloc[0].area)

    return gdf
