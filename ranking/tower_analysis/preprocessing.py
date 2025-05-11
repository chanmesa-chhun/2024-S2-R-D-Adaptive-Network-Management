# preprocessing.py
import os
import glob
import geopandas as gpd
import pandas as pd
from collections import defaultdict
from shapely.ops import unary_union
from tqdm import tqdm
import re
from tower_analysis.config import (
    DISSOLVED_SHAPEFILE_DIR, FAILED_CSV, FACILITY_FILES, CRS
)


def extract_prefix(filename):
    match = re.match(r"(\d{3}-[A-Z]+)", filename)
    return match.group(1) if match else None


def merge_and_dissolve_shapefiles(raw_shp_dir, output_dir, logger=None):
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


import os
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

def generate_live_coverage_shapefile(dissolved_dir, failed_csv_path, output_path, crs, logger=None):
    """
    Generate a unioned shapefile representing the total coverage area of live towers.
    These are towers not listed in the failed CSV, using already dissolved shapefiles.

    Parameters:
        dissolved_dir (str): Directory containing *-Dissolved.shp files.
        failed_csv_path (str): CSV file listing failed tower IDs.
        output_path (str): Path to save the unioned live network coverage shapefile.
        crs (str): Target coordinate reference system (e.g., "EPSG:2193").
        logger (Logger, optional): Logger for status messages.
    """
    if os.path.exists(output_path):
        if logger:
            logger.info(f"Live tower coverage already exists: {output_path}")
        return

    # Load failed tower IDs
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str).tolist()
    geometries = []

    # Loop through dissolved shapefiles
    for filename in os.listdir(dissolved_dir):
        if filename.endswith("-Dissolved.shp"):
            tower_id = filename.replace("-Dissolved.shp", "")
            if tower_id in failed_ids:
                continue

            path = os.path.join(dissolved_dir, filename)
            try:
                gdf = gpd.read_file(path)
                if gdf.empty:
                    continue

                # Ensure CRS is set and correct
                if gdf.crs is None:
                    gdf.set_crs(crs, inplace=True)
                elif gdf.crs != crs:
                    gdf = gdf.to_crs(crs)

                geometries.extend(gdf.geometry)

                if logger:
                    logger.info(f"Included {tower_id} for live coverage.")

            except Exception as e:
                if logger:
                    logger.warning(f"Skipping {filename} due to error: {e}")

    # Union and export
    if geometries:
        unioned_geom = unary_union(geometries)
        union_gdf = gpd.GeoDataFrame(geometry=[unioned_geom], crs=crs)
        union_gdf.to_file(output_path)
        if logger:
            logger.info(f"Saved live network coverage to {output_path}")
    else:
        if logger:
            logger.warning("No valid geometries found for live tower coverage.")




def filter_uncovered_facilities(live_network_coverage_file, facility_files, output_facility_file, logger=None):
    if logger: logger.info(f"Loading live tower coverage from {live_network_coverage_file}")
    live_gdf = gpd.read_file(live_network_coverage_file)

    if logger: logger.info("Loading and merging facility shapefiles...")
    facility_gdfs = [gpd.read_file(f) for f in facility_files]
    all_facilities = pd.concat(facility_gdfs, ignore_index=True)
    facility_gdf = gpd.GeoDataFrame(all_facilities, crs=facility_gdfs[0].crs)

    if logger: logger.info("Filtering uncovered facilities using spatial join...")
    joined = gpd.sjoin(facility_gdf, live_gdf, how="left", predicate="intersects")

    uncovered = joined[joined['index_right'].isna()].drop(columns=['index_right'])

    if logger: logger.info(f"Saving {len(uncovered)} uncovered facilities to {output_facility_file}")
    uncovered.to_file(output_facility_file)

    return output_facility_file
