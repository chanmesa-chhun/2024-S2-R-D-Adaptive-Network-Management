import os
import glob
import geopandas as gpd
import pandas as pd
from collections import defaultdict
from shapely.ops import unary_union
from shapely.validation import make_valid
from tqdm import tqdm
import re
import hashlib
from shapely.prepared import prep
from shapely.geometry import box

from tower_analysis.config import (
    DISSOLVED_SHAPEFILE_DIR, FAILED_CSV, FACILITY_MERGED_FILE, CRS, OUTPUT_DIR
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


# def generate_live_coverage_shapefile(dissolved_dir, failed_csv_path, crs, output_base_dir, logger=None):
#     """
#     Generate a uniquely-named shapefile representing live tower coverage,
#     excluding failed towers listed in the CSV, using fast dissolve.
#     """
#     os.makedirs(output_base_dir, exist_ok=True)

#     # Step 1: Build unique hash key from failed IDs
#     failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
#     hash_key = hashlib.md5(",".join(sorted(failed_ids)).encode()).hexdigest()[:8]
#     output_filename = f"live_network_coverage_{hash_key}.shp"
#     output_path = os.path.join(output_base_dir, output_filename)

#     if os.path.exists(output_path):
#         logger and logger.info(f"[Reuse] Live network coverage already exists: {output_path}")
#         return output_path

#     failed_set = set(failed_ids)
#     live_shps = [
#         os.path.join(dissolved_dir, f)
#         for f in os.listdir(dissolved_dir)
#         if f.endswith("-Dissolved.shp") and f.replace("-Dissolved.shp", "") not in failed_set
#     ]

#     logger and logger.info(f"Found {len(live_shps)} live tower shapefiles to process.")

#     gdfs = []
#     for shp_path in tqdm(live_shps, desc="Loading live towers"):
#         try:
#             gdf = gpd.read_file(shp_path)
#             if gdf.empty:
#                 continue
#             if gdf.crs != crs:
#                 gdf = gdf.to_crs(crs)
#             gdf["dissolve_key"] = 1
#             gdfs.append(gdf[["geometry", "dissolve_key"]])
#         except Exception as e:
#             logger and logger.warning(f"Skipping {shp_path} due to error: {e}")

#     if not gdfs:
#         logger and logger.warning("No valid live tower geometries found.")
#         return output_path

#     combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=crs)
#     dissolved = combined_gdf.dissolve(by="dissolve_key")
#     dissolved.reset_index(drop=True, inplace=True)
#     dissolved.to_file(output_path)
#     logger and logger.info(f"[Generated] Live network coverage saved to {output_path}")
#     return output_path

def filter_uncovered_facilities(live_coverage_file, merged_facility_file, failed_csv_path, crs, output_dir, logger=None):
    """
    Filter facilities not covered by the live tower network using fast spatial checks.

    Parameters:
        live_coverage_file (str): Path to live tower union shapefile.
        merged_facility_file (str): Path to pre-merged facilities.shp.
        failed_csv_path (str): Path to failed_towers.csv for hash-based output naming.
        crs (str): Target CRS.
        output_dir (str): Output directory.
        logger (Logger): Optional logger.

    Returns:
        str: Path to saved uncovered facilities shapefile.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Generate unique output path
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str).tolist()
    hash_key = hashlib.md5(",".join(sorted(failed_ids)).encode()).hexdigest()[:8]
    output_path = os.path.join(output_dir, f"filtered_facilities_{hash_key}.shp")

    if os.path.exists(output_path):
        logger and logger.info(f"[Reuse] Filtered facilities already exists: {output_path}")
        return output_path

    # Load data
    live_gdf = gpd.read_file(live_coverage_file).to_crs(crs)
    facility_gdf = gpd.read_file(merged_facility_file).to_crs(crs)

    # Prepare live coverage geometry
    live_union = prep(live_gdf.unary_union)
    union_bounds = live_gdf.total_bounds  # minx, miny, maxx, maxy
    bbox_geom = box(*union_bounds)

    # First filter by bounding box
    bbox_filtered = facility_gdf[facility_gdf.geometry.intersects(bbox_geom)]

    # Then check actual intersection using prepared geometry
    uncovered_mask = ~bbox_filtered.geometry.apply(live_union.intersects)
    uncovered = bbox_filtered[uncovered_mask]

    # Save result
    uncovered.to_file(output_path)
    logger and logger.info(f"[Generated] Saved {len(uncovered)} uncovered facilities to {output_path}")

    return output_path

# def generate_live_coverage_shapefile(dissolved_dir, failed_csv_path, crs, output_base_dir, logger=None):
#     """
#     Optimized version: Only include live towers whose bounding boxes intersect with the failed tower area.

#     Parameters:
#         dissolved_dir (str): Folder containing dissolved tower shapefiles.
#         failed_csv_path (str): CSV file listing failed tower IDs.
#         crs (str): Coordinate reference system.
#         output_base_dir (str): Folder to store output shapefile.
#         logger (Logger, optional): Logger instance.

#     Returns:
#         str: Path to generated/reused live tower coverage shapefile.
#     """
#     os.makedirs(output_base_dir, exist_ok=True)
#     failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str).tolist()
#     hash_key = hashlib.md5(",".join(sorted(failed_ids)).encode()).hexdigest()[:8]
#     output_filename = f"live_network_coverage_{hash_key}_opt.shp"
#     output_path = os.path.join(output_base_dir, output_filename)

#     if os.path.exists(output_path):
#         logger and logger.info(f"[Reuse] Live network coverage already exists: {output_path}")
#         return output_path

#     # Step 1: Combine all failed tower geometries
#     failed_geoms = []
#     for tower_id in failed_ids:
#         path = os.path.join(dissolved_dir, f"{tower_id}-Dissolved.shp")
#         if os.path.exists(path):
#             gdf = gpd.read_file(path)
#             if gdf.crs != crs:
#                 gdf = gdf.to_crs(crs)
#             failed_geoms.extend(gdf.geometry)

#     if not failed_geoms:
#         logger and logger.warning("No failed tower geometries found.")
#         return output_path

#     # Step 2: Get bounding box of failed region
#     failed_union_bounds = gpd.GeoSeries(failed_geoms).total_bounds
#     minx, miny, maxx, maxy = failed_union_bounds

#     # Step 3: Load live towers only if they intersect with failed bbox
#     live_geoms = []
#     for file in tqdm(os.listdir(dissolved_dir), desc="Filtering live towers"):
#         if not file.endswith("-Dissolved.shp"):
#             continue
#         tower_id = file.replace("-Dissolved.shp", "")
#         if tower_id in failed_ids:
#             continue

#         path = os.path.join(dissolved_dir, file)
#         try:
#             gdf = gpd.read_file(path)
#             if gdf.empty:
#                 continue
#             if gdf.crs != crs:
#                 gdf = gdf.to_crs(crs)
#             geom = gdf.unary_union
#             bx, by, tx, ty = geom.bounds
#             if tx < minx or bx > maxx or ty < miny or by > maxy:
#                 continue  # Skip non-overlapping
#             live_geoms.append(geom)
#         except Exception as e:
#             logger and logger.warning(f"Skipping {file} due to error: {e}")

#     if not live_geoms:
#         logger and logger.warning("No intersecting live towers found.")
#         return output_path

#     # Step 4: Dissolve geometries
#     union_geom = unary_union(live_geoms)
#     gdf_union = gpd.GeoDataFrame(geometry=[union_geom], crs=crs)
#     gdf_union.to_file(output_path)

#     logger and logger.info(f"[Generated] Optimized live coverage saved to {output_path}")
#     return output_path

def generate_live_coverage_shapefile(dissolved_dir, failed_csv_path, crs, output_base_dir, logger=None, batch_size=200):
    """
    Optimized version: Generate a live tower coverage shapefile by performing batched unary_union.

    Parameters:
        dissolved_dir (str): Directory with dissolved tower shapefiles.
        failed_csv_path (str): Path to CSV with failed tower IDs.
        crs (str): CRS to enforce.
        output_base_dir (str): Output folder for live network shapefile.
        logger (Logger, optional): Logger instance.
        batch_size (int): Number of shapefiles per batch for union operation.

    Returns:
        str: Path to the generated or reused shapefile.
    """
    os.makedirs(output_base_dir, exist_ok=True)

    # Hash key for reusability
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
    hash_key = hashlib.md5(",".join(sorted(failed_ids)).encode()).hexdigest()[:8]
    output_filename = f"live_network_coverage_{hash_key}_batched.shp"
    output_path = os.path.join(output_base_dir, output_filename)

    if os.path.exists(output_path):
        if logger:
            logger.info(f"[Reuse] Live network coverage already exists: {output_path}")
        return output_path

    failed_set = set(failed_ids)
    shp_paths = [
        os.path.join(dissolved_dir, f)
        for f in os.listdir(dissolved_dir)
        if f.endswith("-Dissolved.shp") and f.replace("-Dissolved.shp", "") not in failed_set
    ]

    logger and logger.info(f"Filtering {len(shp_paths)} live towers for batch dissolve...")

    geometries = []
    for path in tqdm(shp_paths, desc="Loading live towers"):
        try:
            gdf = gpd.read_file(path)
            if gdf.empty:
                continue
            if gdf.crs != crs:
                gdf = gdf.to_crs(crs)
            geometries.extend(gdf.geometry)
        except Exception as e:
            logger and logger.warning(f"Skipping {path} due to error: {e}")

    if not geometries:
        logger and logger.warning("No valid live tower geometries found.")
        return None

    # Batched unary union
    logger and logger.info("Starting batched unary_union...")
    batch_unions = []
    for i in tqdm(range(0, len(geometries), batch_size), desc="Union batches"):
        batch = geometries[i:i+batch_size]
        batch_union = unary_union(batch)
        batch_unions.append(batch_union)

    logger and logger.info("Final union of batch results...")
    final_union = unary_union(batch_unions)
    union_gdf = gpd.GeoDataFrame(geometry=[final_union], crs=crs)
    union_gdf.to_file(output_path)

    logger and logger.info(f"[Generated] Batched live network coverage saved to {output_path}")
    return output_path