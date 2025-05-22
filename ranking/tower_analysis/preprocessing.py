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


def merge_and_dissolve_shapefiles(raw_shp_dir, output_dir, logger=None, prefix_range=None):
    """
    Merge and dissolve tower shapefiles grouped by prefix.
    Only process prefixes within the given range if provided.

    Parameters:
        raw_shp_dir (str): Path to folder with raw shapefiles.
        output_dir (str): Folder where dissolved shapefiles are saved.
        logger (Logger, optional): Optional logger.
        prefix_range (tuple, optional): Tuple (start_prefix, end_prefix), e.g., ("001", "010")
    """
    import os
    import glob
    import geopandas as gpd
    import pandas as pd
    from collections import defaultdict
    from shapely.ops import unary_union
    from tqdm import tqdm
    from .preprocessing import extract_prefix  # make sure this function is accessible

    os.makedirs(output_dir, exist_ok=True)
    shp_files = glob.glob(os.path.join(raw_shp_dir, "*.shp"))
    prefix_groups = defaultdict(list)

    for path in shp_files:
        filename = os.path.basename(path)
        prefix = extract_prefix(filename)
        if not prefix:
            continue
        # Skip if outside of user-defined prefix range
        if prefix_range:
            prefix_numeric = prefix[:3]
            if not (prefix_range[0] <= prefix_numeric <= prefix_range[1]):
                continue
        prefix_groups[prefix].append(path)

    if logger:
        logger.info(f"Found {len(prefix_groups)} tower groups to process (within range).")

    for prefix, files in tqdm(prefix_groups.items(), desc="Preprocessing towers"):
        dissolved_name = f"{prefix}-Dissolved.shp"
        dissolved_path = os.path.join(output_dir, dissolved_name)

        if all(os.path.exists(dissolved_path.replace(".shp", ext)) for ext in [".shp", ".shx", ".dbf"]):
            logger and logger.info(f"Skipped existing: {dissolved_name}")
            continue

        try:
            gdf_list = [gpd.read_file(f) for f in files]
            merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs=gdf_list[0].crs)
            dissolved_geom = unary_union(merged_gdf.geometry)
            dissolved_gdf = gpd.GeoDataFrame(geometry=[dissolved_geom], crs=merged_gdf.crs)
            dissolved_gdf.to_file(dissolved_path)
            logger and logger.info(f"Generated: {dissolved_name}")
        except Exception as e:
            msg = f"Failed processing {prefix}: {e}"
            logger.error(msg) if logger else print(msg)


def generate_live_coverage_shapefile(
    dissolved_dir,
    failed_csv_path,
    crs,
    output_base_dir,
    logger=None,
    batch_size=200,
    prefix_range=None  # Optional: restrict tower prefix range, e.g., ("001", "010")
):
    """
    Generate a shapefile representing the union of all live (non-failed) tower coverage areas.
    Optionally restrict the union to a limited set of tower prefixes to reduce processing time.

    Parameters:
        dissolved_dir (str): Directory containing dissolved tower shapefiles (e.g., '001-AHPA-Dissolved.shp').
        failed_csv_path (str): CSV file containing a 'tower_id' column for failed towers.
        crs (str): Coordinate reference system to enforce (e.g., EPSG:2193).
        output_base_dir (str): Directory to store the generated live coverage shapefile.
        logger (Logger, optional): Logging utility.
        batch_size (int): Number of towers to process per unary_union batch.
        prefix_range (tuple, optional): 2-tuple of (start_prefix, end_prefix) to limit which towers to include.

    Returns:
        str: Path to the generated or reused union shapefile.
    """
    import os
    import hashlib
    import geopandas as gpd
    from shapely.ops import unary_union
    from tqdm import tqdm

    os.makedirs(output_base_dir, exist_ok=True)

    # Load failed tower IDs from CSV
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
    failed_set = set(failed_ids)

    # Generate unique hash key based on sorted failed tower IDs
    prefix_input = f"{prefix_range[0]}-{prefix_range[1]}" if prefix_range else "ALL"
    hash_input = ",".join(sorted(failed_ids)) + f"|PREFIX:{prefix_input}"
    hash_key = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    output_filename = f"live_network_coverage_{hash_key}_batched.shp"
    output_path = os.path.join(output_base_dir, output_filename)

    # If output already exists, reuse it
    shp_required_exts = [".shp", ".shx", ".dbf"]
    if all(os.path.exists(output_path.replace(".shp", ext)) for ext in shp_required_exts):
        logger and logger.info(f"[Reuse] Live network coverage already exists: {output_path}")
        return output_path

    # Filter dissolved tower SHPs (excluding failed towers)
    shp_paths = []
    for f in os.listdir(dissolved_dir):
        if not f.endswith("-Dissolved.shp"):
            continue

        tower_id = f.replace("-Dissolved.shp", "")

        # Skip failed towers
        if tower_id in failed_set:
            continue

        # Apply prefix range restriction if provided
        if prefix_range:
            prefix = tower_id[:3]  # Assume prefix is the first 3 digits
            if not (prefix_range[0] <= prefix <= prefix_range[1]):
                continue

        shp_paths.append(os.path.join(dissolved_dir, f))

    logger and logger.info(f"Selected {len(shp_paths)} live towers for union.")

    # Load geometries from selected tower SHPs
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

    # Perform batched unary union
    logger and logger.info("Starting batched unary_union...")
    batch_unions = []
    for i in tqdm(range(0, len(geometries), batch_size), desc="Union batches"):
        batch = geometries[i:i+batch_size]
        batch_union = unary_union(batch)
        batch_unions.append(batch_union)

    # Final union of all batches
    logger and logger.info("Final union of batch results...")
    final_union = unary_union(batch_unions)

    # Save union result as a single-feature shapefile
    union_gdf = gpd.GeoDataFrame(geometry=[final_union], crs=crs)
    union_gdf.to_file(output_path)
    logger and logger.info(f"[Generated] Live network coverage saved to {output_path}")
    return output_path

def filter_uncovered_facilities(live_coverage_path, facility_path, failed_csv_path, crs, output_dir, logger=None):
    """
    Filter facilities not covered by live towers. Output file is hash-based for reusability.
    """
    # Generate unique hash based on input content
    failed_ids = pd.read_csv(failed_csv_path)["tower_id"].astype(str)
    hash_input = "|".join([
        live_coverage_path,
        facility_path,
        ",".join(sorted(failed_ids))
    ])
    hash_key = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    output_filename = f"filtered_facilities_{hash_key}.shp"
    output_path = os.path.join(output_dir, output_filename)

    if os.path.exists(output_path):
        logger and logger.info(f"[Reuse] Filtered facilities exist: {output_path}")
        return output_path

    # Load and align CRS
    live_gdf = gpd.read_file(live_coverage_path)
    fac_gdf = gpd.read_file(facility_path)
    if fac_gdf.crs != crs:
        fac_gdf = fac_gdf.to_crs(crs)
    if live_gdf.crs != crs:
        live_gdf = live_gdf.to_crs(crs)

    # Check uncovered via spatial join
    covered = gpd.sjoin(fac_gdf, live_gdf, predicate="within", how="inner")
    uncovered = fac_gdf[~fac_gdf.index.isin(covered.index)]

    if uncovered.empty:
        logger and logger.warning("No uncovered facilities found.")
    else:
        logger and logger.info(f"{len(uncovered)} uncovered facilities identified.")

    uncovered.to_file(output_path)
    logger and logger.info(f"[Generated] Saved to {output_path}")

    return output_path

def get_prefix_bounds(dissolved_dir):
    """
    Get the minimum and maximum 3-digit prefix from existing dissolved SHP files.
    """
    prefixes = []
    for f in os.listdir(dissolved_dir):
        if f.endswith("-Dissolved.shp") and len(f) >= 3:
            prefix = f[:3]
            if prefix.isdigit():
                prefixes.append(prefix)
    if not prefixes:
        return "000", "999"
    return min(prefixes), max(prefixes)


def prompt_prefix_range(min_prefix, max_prefix):
    """
    Prompt the user for a valid 3-digit prefix start and end value.
    Empty input will fallback to min or max prefix.
    """
    while True:
        prefix_start = input(f"Enter prefix start (or press Enter for {min_prefix}): ").strip()
        prefix_end = input(f"Enter prefix end (or press Enter for {max_prefix}): ").strip()

        if prefix_start and not prefix_start.isdigit():
            print("⚠️ Invalid input: prefix start must be a number.")
            continue
        if prefix_end and not prefix_end.isdigit():
            print("⚠️ Invalid input: prefix end must be a number.")
            continue

        prefix_start = prefix_start.zfill(3) if prefix_start else min_prefix
        prefix_end = prefix_end.zfill(3) if prefix_end else max_prefix

        if prefix_start > prefix_end:
            print(f"⚠️ Invalid range: start '{prefix_start}' is greater than end '{prefix_end}'.")
            continue

        return prefix_start, prefix_end
