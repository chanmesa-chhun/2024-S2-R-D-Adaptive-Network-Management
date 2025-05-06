import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.wkt import loads as wkt_loads
from rtree import index
from tqdm import tqdm

# File names for your datasets
population_file = "population_50m.csv"  # 50m grid data with population info
celltower_file = "celltower_data_utm.csv"  # Cell tower data

# Load datasets
df_population = pd.read_csv(population_file)
df_celltower = pd.read_csv(celltower_file)

# Build an R-tree spatial index for the population grid cells
spatial_idx = index.Index()
geometry_map = {}  # Map index to geometry and population data

print("🔍 Building spatial index for population grid...")
for i, row in tqdm(df_population.iterrows(), total=len(df_population)):
    try:
        geom = wkt_loads(row["WKT"])
        spatial_idx.insert(i, geom.bounds)
        geometry_map[i] = (geom, row["PopEst2022"], row["PopEst2023"])
    except Exception as e:
        print(f"Error processing row {i}: {e}")

# Define the coverage radius (e.g., 5000 m for a 5km radius)
coverage_radius = 5000

results = []

print("\n🚀 Calculating cell tower coverage (precise approach)...")
for _, tower in tqdm(df_celltower.iterrows(), total=len(df_celltower)):
    # Create a Shapely point for the tower
    tower_point = Point(tower["utm_easting"], tower["utm_northing"])
    # Create a circle (buffer) for the tower's coverage
    tower_coverage = tower_point.buffer(coverage_radius)

    # Use the spatial index to get candidate grid cells within the bounding box of the coverage circle
    candidate_ids = list(spatial_idx.intersection(tower_coverage.bounds))

    total_population_2022 = 0
    total_population_2023 = 0

    # Option 2: More precise approach using area-weighted population
    for idx in candidate_ids:
        cell_geom, pop_2022, pop_2023 = geometry_map[idx]
        # Calculate the intersection between the cell and the coverage circle
        intersection = cell_geom.intersection(tower_coverage)
        if not intersection.is_empty:
            # Fraction of the cell covered by the tower's coverage circle
            fraction = intersection.area / cell_geom.area
            total_population_2022 += pop_2022 * fraction
            total_population_2023 += pop_2023 * fraction

    results.append({
        "sitename": tower["NAME"],
        "total_population_2022": total_population_2022,
        "total_population_2023": total_population_2023
    })

# Save or display the results
result_df = pd.DataFrame(results)
result_df.to_csv("cell_tower_population_50m_precise.csv", index=False)
print("✅ Coverage calculation complete! Results saved to 'cell_tower_population_50m_precise.csv'.")
