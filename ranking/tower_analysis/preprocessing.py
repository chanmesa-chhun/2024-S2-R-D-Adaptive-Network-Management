import os
import glob
import geopandas as gpd
import pandas as pd
from collections import defaultdict
from shapely.ops import unary_union
from tqdm import tqdm
import re
import hashlib
from tower_analysis.config import (
    DISSOLVED_SHAPEFILE_DIR, FAILED_CSV, FACILITY_FILES, CRS, OUTPUT_DIR
)

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
    Skips processing if dissolved shapefile already exists.

    Parameters:
        raw_shp_dir (str): Path to folder with raw shapefiles.
        output_dir (str): Folder where dissolved shapefiles are saved.
        logger (Logger, optional): Optional logger.
    """
    os.makedirs(output_dir, exist_ok=True)
    shp_files = glob.glob(os.path.join(raw_shp_dir, "*.shp"))
    prefix_groups = defaultdict(list)

    for path in shp_files:
        filename = os.path.basename(path)
        prefix = extract_prefix(filename)
        if prefix:
            prefix_groups[prefix].append(path)

    if logger:
        logger.info(f"Found {len(prefix_groups)} unique tower prefixes to process.")

    for prefix, files in tqdm(prefix_groups.items(), desc="Preprocessing towers"):
        dissolved_name = f"{prefix}-Dissolved.shp"
        dissolved_path = os.path.join(output_dir, dissolved_name)

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


from tqdm import tqdm

def generate_live_coverage_shapefile(dissolved_dir, failed_csv_path, crs, output_base_dir, logger=None):
    """
    Generate a uniquely-named shapefile representing live tower coverage,
    excluding failed towers listed in the CSV, using fast dissolve.
    """
    os.makedirs(output_base_dir, exist_ok=True)

    # Step 1: Build unique hash key from failed IDs
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
    hash_key = hashlib.md5(",".join(sorted(failed_ids)).encode()).hexdigest()[:8]
    output_filename = f"live_network_coverage_{hash_key}.shp"
    output_path = os.path.join(output_base_dir, output_filename)

    if os.path.exists(output_path):
        logger and logger.info(f"[Reuse] Live network coverage already exists: {output_path}")
        return output_path

    failed_set = set(failed_ids)
    live_shps = [
        os.path.join(dissolved_dir, f)
        for f in os.listdir(dissolved_dir)
        if f.endswith("-Dissolved.shp") and f.replace("-Dissolved.shp", "") not in failed_set
    ]

    logger and logger.info(f"Found {len(live_shps)} live tower shapefiles to process.")

    gdfs = []
    for shp_path in tqdm(live_shps, desc="Loading live towers"):
        try:
            gdf = gpd.read_file(shp_path)
            if gdf.empty:
                continue
            if gdf.crs != crs:
                gdf = gdf.to_crs(crs)
            gdf["dissolve_key"] = 1
            gdfs.append(gdf[["geometry", "dissolve_key"]])
        except Exception as e:
            logger and logger.warning(f"Skipping {shp_path} due to error: {e}")

    if not gdfs:
        logger and logger.warning("No valid live tower geometries found.")
        return output_path

    combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=crs)
    dissolved = combined_gdf.dissolve(by="dissolve_key")
    dissolved.reset_index(drop=True, inplace=True)
    dissolved.to_file(output_path)
    logger and logger.info(f"[Generated] Live network coverage saved to {output_path}")
    return output_path

def filter_uncovered_facilities(live_network_coverage_file, facility_files, failed_csv_path, crs, output_base_dir, logger=None):
    """
    Filter out facilities that are already covered by the live tower network.
    Generates a uniquely named filtered facilities shapefile.

    Parameters:
        live_network_coverage_file (str): Path to unioned live coverage shapefile.
        facility_files (list): List of input facility shapefiles.
        failed_csv_path (str): Path to failed towers CSV (used for unique ID generation).
        crs (str): CRS for the output file.
        output_base_dir (str): Directory to store filtered shapefile.
        logger (Logger, optional): Logger.

    Returns:
        str: Path to saved filtered facilities shapefile.
    """
    os.makedirs(output_base_dir, exist_ok=True)
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str).tolist()
    hash_key = hashlib.md5(",".join(sorted(failed_ids)).encode()).hexdigest()[:8]
    output_filename = f"filtered_facilities_{hash_key}.shp"
    output_path = os.path.join(output_base_dir, output_filename)

    if os.path.exists(output_path):
        if logger:
            logger.info(f"[Reuse] Filtered facilities already exists: {output_path}")
        return output_path

    if logger: logger.info(f"Loading live tower coverage from {live_network_coverage_file}")
    live_gdf = gpd.read_file(live_network_coverage_file).to_crs(crs)

    if logger: logger.info("Loading and merging facility shapefiles...")
    facility_gdfs = [gpd.read_file(f) for f in facility_files]
    for gdf in facility_gdfs:
        if 'type' not in gdf.columns and 'facility_t' in gdf.columns:
            gdf['type'] = gdf['facility_t'].str.lower()

    all_facilities = pd.concat(facility_gdfs, ignore_index=True)
    facility_gdf = gpd.GeoDataFrame(all_facilities, crs=facility_gdfs[0].crs)

    if logger: logger.info("Filtering uncovered facilities using spatial join...")
    joined = gpd.sjoin(facility_gdf, live_gdf, how="left", predicate="intersects")
    uncovered = joined[joined['index_right'].isna()].drop(columns=['index_right'])

    if logger: logger.info(f"Saving {len(uncovered)} uncovered facilities to {output_path}")
    uncovered.to_file(output_path)

    return output_path
