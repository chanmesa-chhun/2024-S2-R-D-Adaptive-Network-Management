### file_utils.py

import geopandas as gpd
import pandas as pd
import os

def read_failed_towers(failed_csv_path):
    df = pd.read_csv(failed_csv_path)
    return set(df["tower_id"].tolist())

def list_shapefiles_from_dir(directory):
    return [f for f in os.listdir(directory) if f.endswith(".shp")]

def load_failed_tower_geometries(dissolved_dir, failed_csv_path, crs):
    failed_towers = read_failed_towers(failed_csv_path)
    shapefiles = list_shapefiles_from_dir(dissolved_dir)
    gdfs = {}

    for shp in shapefiles:
        tower_name = shp.replace("-Dissolved.shp", "")
        if tower_name in failed_towers:
            gdf = gpd.read_file(os.path.join(dissolved_dir, shp))
            if gdf.crs is None:
                gdf = gdf.set_crs(crs)
            elif gdf.crs.to_string() != crs:
                gdf = gdf.to_crs(crs)
            gdfs[tower_name] = gdf

    return gdfs

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
