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
from typing import Optional, Tuple

from tower_analysis.config import (
    DISSOLVED_SHAPEFILE_DIR,
    FAILED_CSV,
    FACILITY_MERGED_FILE,
    CRS,
    OUTPUT_DIR,
)


def extract_prefix(filename: str) -> Optional[str]:
    """
    Extract the common tower prefix from the filename.
    Example: '001-AHPA-L07-1.shp' -> '001-AHPA'
    """
    match = re.match(r"(\d{3}-[A-Z]+)", filename)
    return match.group(1) if match else None


def merge_and_dissolve_shapefiles(
    raw_shp_dir: str,
    output_dir: str,
    logger=None,
    prefix_range: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Merge and dissolve tower shapefiles grouped by prefix.
    If prefix_range is provided, only prefixes whose numeric code
    falls within [lo, hi] will be processed.

    Skips processing if dissolved shapefile already exists.
    """
    os.makedirs(output_dir, exist_ok=True)
    shp_files = glob.glob(os.path.join(raw_shp_dir, "*.shp"))
    prefix_groups = defaultdict(list)

    for path in shp_files:
        filename = os.path.basename(path)
        prefix = extract_prefix(filename)
        if prefix:
            # Filter by prefix_range if given
            if prefix_range:
                lo, hi = prefix_range
                try:
                    code = int(prefix.split('-')[0])
                except ValueError:
                    continue
                if code < lo or code > hi:
                    continue
            prefix_groups[prefix].append(path)

    if logger:
        logger.info(f"Found {len(prefix_groups)} unique tower prefixes to process (prefix_range={prefix_range}).")

    for prefix, files in tqdm(prefix_groups.items(), desc="Preprocessing towers"):
        dissolved_name = f"{prefix}-Dissolved.shp"
        dissolved_path = os.path.join(output_dir, dissolved_name)

        # Skip if all shapefile components exist
        if all(os.path.exists(dissolved_path.replace('.shp', ext)) for ext in ['.shp', '.shx', '.dbf']):
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


def generate_live_coverage_shapefile(
    dissolved_dir: str,
    failed_csv_path: str,
    crs: str,
    output_base_dir: str,
    logger=None,
    batch_size: int = 200,
    prefix_range: Optional[Tuple[int, int]] = None,
) -> Optional[str]:
    """
    Optimized version: Generate a live tower coverage shapefile by performing batched unary_union.
    If prefix_range is provided, only dissolved files whose prefix code is in range
    are included in the union.
    """
    os.makedirs(output_base_dir, exist_ok=True)

    # Hash key for caching
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
    hash_key = hashlib.md5(
        ",".join(sorted(failed_ids)).encode()
    ).hexdigest()[:8]
    output_filename = f"live_network_coverage_{hash_key}_batched.shp"
    output_path = os.path.join(output_base_dir, output_filename)

    if os.path.exists(output_path):
        if logger:
            logger.info(f"[Reuse] Live network coverage already exists: {output_path}")
        return output_path

    failed_set = set(failed_ids)
    all_files = [f for f in os.listdir(dissolved_dir) if f.endswith("-Dissolved.shp")]
    shp_paths = []
    for f in all_files:
        prefix = f.replace("-Dissolved.shp", "")
        try:
            code = int(prefix.split('-')[0])
        except ValueError:
            continue
        if prefix_range and (code < prefix_range[0] or code > prefix_range[1]):
            continue
        if prefix not in failed_set:
            shp_paths.append(os.path.join(dissolved_dir, f))

    logger and logger.info(f"Filtering {len(shp_paths)} live towers (prefix_range={prefix_range}).")

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

    logger and logger.info("Starting batched unary_union...")
    batch_unions = []
    for i in tqdm(range(0, len(geometries), batch_size), desc="Union batches"):
        batch = geometries[i : i + batch_size]
        batch_unions.append(unary_union(batch))

    logger and logger.info("Final union of batch results...")
    final_union = unary_union(batch_unions)
    union_gdf = gpd.GeoDataFrame(geometry=[final_union], crs=crs)
    union_gdf.to_file(output_path)

    logger and logger.info(f"[Generated] Batched live network coverage saved to {output_path}")
    return output_path


def filter_uncovered_facilities(
    live_coverage_path: str,
    facility_path: str,
    failed_csv_path: str,
    crs: str,
    output_dir: str,
    logger=None,
) -> str:
    """
    Filter facilities not covered by live towers. Output file is hash-based for reusability.
    """
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
    hash_input = "|".join([
        live_coverage_path,
        facility_path,
        ",".join(sorted(failed_ids)),
    ])
    hash_key = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    output_filename = f"filtered_facilities_{hash_key}.shp"
    output_path = os.path.join(output_dir, output_filename)

    if os.path.exists(output_path):
        logger and logger.info(f"[Reuse] Filtered facilities exist: {output_path}")
        return output_path

    live_gdf = gpd.read_file(live_coverage_path)
    fac_gdf = gpd.read_file(facility_path)
    if fac_gdf.crs != crs:
        fac_gdf = fac_gdf.to_crs(crs)
    if live_gdf.crs != crs:
        live_gdf = live_gdf.to_crs(crs)

    covered = gpd.sjoin(fac_gdf, live_gdf, predicate="within", how="inner")
    uncovered = fac_gdf[~fac_gdf.index.isin(covered.index)]

    if uncovered.empty:
        logger and logger.warning("No uncovered facilities found.")
    else:
        logger and logger.info(f"{len(uncovered)} uncovered facilities identified.")

    uncovered.to_file(output_path)
    logger and logger.info(f"[Generated] Saved to {output_path}")

    return output_path
