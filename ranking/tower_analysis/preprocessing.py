import os
import glob
import geopandas as gpd
import pandas as pd
from collections import defaultdict
from shapely.ops import unary_union
from tqdm import tqdm
import re

def extract_prefix(filename):
    """
    Extract the common tower prefix from the filename.
    Example: '001-AHPA-L07-1.shp' -> '001-AHPA'
    """
    match = re.match(r"(\d{3}-[A-Z]+)", filename)
    return match.group(1) if match else None

def merge_and_dissolve_shapefiles(raw_shp_dir, output_dir, logger=None):
    """
    Merge and dissolve tower shapefiles grouped by prefix.
    For example, all files with prefix '001-AHPA' will be merged into one dissolved shapefile.
    Skips processing if a dissolved shapefile (with .shp/.shx/.dbf) already exists.

    Parameters:
        raw_shp_dir (str): Path to folder containing raw tower shapefiles.
        output_dir (str): Path to folder where dissolved shapefiles will be saved.
        logger (logging.Logger, optional): Logger for status messages.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Group shapefiles by common prefix
    shp_files = glob.glob(os.path.join(raw_shp_dir, "*.shp"))
    prefix_groups = defaultdict(list)

    for path in shp_files:
        filename = os.path.basename(path)
        prefix = extract_prefix(filename)
        if prefix:
            prefix_groups[prefix].append(path)

    if logger:
        logger.info(f"Found {len(prefix_groups)} unique tower prefixes to process.")

    # Step 2: Merge and dissolve shapefiles for each prefix
    for prefix, files in tqdm(prefix_groups.items(), desc="Preprocessing towers"):
        dissolved_name = f"{prefix}-Dissolved.shp"
        dissolved_path = os.path.join(output_dir, dissolved_name)

        # Skip processing if all associated shapefile components exist
        if all(os.path.exists(dissolved_path.replace(".shp", ext)) for ext in [".shp", ".shx", ".dbf"]):
            if logger:
                logger.info(f"Skipped existing: {dissolved_name}")
            continue

        try:
            gdf_list = [gpd.read_file(f) for f in files]
            merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs=gdf_list[0].crs)
            dissolved_geom = unary_union(merged_gdf.geometry)

            dissolved_gdf = gpd.GeoDataFrame(geometry=[dissolved_geom], crs=merged_gdf.crs)
            dissolved_gdf.to_file(dissolved_path)

            if logger:
                logger.info(f"Generated: {dissolved_name}")

        except Exception as e:
            msg = f"Failed processing {prefix}: {e}"
            if logger:
                logger.error(msg)
            else:
                print(msg)
