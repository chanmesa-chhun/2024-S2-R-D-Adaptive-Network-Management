# file_utils.py
import geopandas as gpd
import pandas as pd
import os
from tower_analysis.config import FILTERED_FACILITY_FILE

def load_failed_tower_geometries(shapefile_dir, failed_csv_path, crs):
    """
    Load dissolved coverage shapefiles for failed towers listed in a CSV file.

    Parameters:
        shapefile_dir (str): Path to the directory with dissolved tower shapefiles.
        failed_csv_path (str): Path to the CSV file listing failed tower IDs.
        crs (str): Target coordinate reference system (e.g., EPSG:2193).

    Returns:
        dict: Mapping from tower ID to corresponding GeoDataFrame of dissolved coverage.
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
    Load and merge facility shapefiles, reprojecting to a target CRS.
    If a pre-filtered facility shapefile exists (excluding live-covered areas), use it.

    Parameters:
        file_paths (list): List of paths to facility shapefiles.
        target_crs (str): Target coordinate reference system.

    Returns:
        GeoDataFrame: Combined facility data in target CRS.
    """
    if os.path.exists(FILTERED_FACILITY_FILE):
        facility_gdf = gpd.read_file(FILTERED_FACILITY_FILE)
        if facility_gdf.crs and facility_gdf.crs != target_crs:
            facility_gdf = facility_gdf.to_crs(target_crs)
        elif not facility_gdf.crs:
            facility_gdf.set_crs(target_crs, inplace=True)

        # Ensure 'type' column exists
        if 'type' not in facility_gdf.columns and 'facility_t' in facility_gdf.columns:
            facility_gdf["facility_t"] = facility_gdf["facility_t"].str.lower().str.strip()
            facility_gdf["type"] = facility_gdf["facility_t"].apply(
                lambda x: "hospital" if "hospital" in x else
                          "fire_station" if "fire" in x else
                          "police" if "police" in x else "other"
            )

        return facility_gdf

    all_facilities = []
    for path in file_paths:
        gdf = gpd.read_file(path)
        if gdf.crs and gdf.crs != target_crs:
            gdf = gdf.to_crs(target_crs)
        elif not gdf.crs:
            gdf.set_crs(target_crs, inplace=True)

        facility_type = os.path.splitext(os.path.basename(path))[0].lower()
        gdf['type'] = facility_type
        all_facilities.append(gdf)

    combined = gpd.GeoDataFrame(pd.concat(all_facilities, ignore_index=True), crs=target_crs)
    return combined

def load_population_data(population_path, target_crs):
    """
    Load population grid shapefile and convert to target CRS.

    Parameters:
        population_path (str): Path to the population shapefile.
        target_crs (str): Target coordinate reference system.

    Returns:
        GeoDataFrame: Population data in target CRS.
    """
    gdf = gpd.read_file(population_path)
    if gdf.crs and gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)
    elif not gdf.crs:
        gdf.set_crs(target_crs, inplace=True)
    return gdf
