### file_utils.py

import geopandas as gpd
import pandas as pd
import os

def read_failed_towers(failed_csv_path):
    df = pd.read_csv(failed_csv_path)
    return set(df["tower_id"].tolist())

def list_shapefiles_from_dir(directory):
    return [f for f in os.listdir(directory) if f.endswith(".shp")]

def load_failed_tower_geometries(shapefile_dir, failed_csv_path, crs):
    """
    Load dissolved shapefiles for failed towers and ensure all are in the target CRS.

    Parameters:
    - shapefile_dir: directory containing dissolved shapefiles.
    - failed_csv_path: path to CSV file listing failed tower IDs.
    - crs: target coordinate reference system (e.g., 'EPSG:2193').

    Returns:
    - Dictionary of {tower_id: GeoDataFrame} for each failed tower.
    """
    failed_df = pd.read_csv(failed_csv_path)
    failed_tower_ids = failed_df["tower_id"].astype(str).tolist()

    tower_geometries = {}

    for tower_id in failed_tower_ids:
        shapefile_path = os.path.join(shapefile_dir, f"{tower_id}-Dissolved.shp")
        if not os.path.exists(shapefile_path):
            print(f"⚠️ Shapefile not found for tower: {tower_id}")
            continue

        try:
            gdf = gpd.read_file(shapefile_path)
            # Handle CRS safely
            if gdf.crs != crs:
                try:
                    gdf = gdf.to_crs(crs)
                except Exception as e:
                    print(f"❌ CRS transform failed for {tower_id}: {e}")
                    continue
            tower_geometries[tower_id] = gdf
        except Exception as e:
            print(f"❌ Error reading shapefile for {tower_id}: {e}")
            continue

    return tower_geometries

def load_facility_data(file_paths, target_crs):
    """
    Load multiple facility shapefiles, assign 'type' field based on filename,
    ensure CRS consistency, and return as a combined GeoDataFrame.
    
    Parameters:
        file_paths (list): List of paths to facility shapefiles.
        target_crs (str): CRS string, e.g., "EPSG:2193"
    
    Returns:
        GeoDataFrame: Combined and reprojected facility data with 'type' field.
    """
    all_gdfs = []
    for path in file_paths:
        if not os.path.exists(path):
            print(f"⚠️ File not found: {path}")
            continue

        try:
            gdf = gpd.read_file(path)
            if gdf.empty:
                print(f"⚠️ Empty file skipped: {path}")
                continue

            # Extract type from filename, e.g., "fire_stations.shp" → "fire_station"
            facility_type = os.path.splitext(os.path.basename(path))[0].replace("_stations", "").rstrip("s")
            gdf["type"] = facility_type

            # Reproject if necessary
            if gdf.crs is None:
                gdf.set_crs(target_crs, inplace=True)
            elif gdf.crs != target_crs:
                gdf = gdf.to_crs(target_crs)

            all_gdfs.append(gdf)

        except Exception as e:
            print(f"Error reading {path}: {e}")

    if not all_gdfs:
        raise RuntimeError("No valid facility data could be loaded.")

    return gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True), crs=target_crs)

def load_population_data(population_path, target_crs):
    gdf = gpd.read_file(population_path)
    gdf = gdf.to_crs(target_crs)
    if "PopEst2023" not in gdf.columns:
        raise ValueError("Population grid missing 'PopEst2023' column")
    return gdf
