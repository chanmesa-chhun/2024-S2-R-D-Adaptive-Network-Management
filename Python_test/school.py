import geopandas as gpd
import pandas as pd
from shapely import wkt

# Sample dataset (replace with your file)
data = pd.read_csv("C:\\Users\\mesac\\Downloads\\lds-nz-facilities-CSV\\nz-facilities.csv")

df = pd.DataFrame(data)

# Convert WKT to geometry
df["geometry"] = df["WKT"].apply(wkt.loads)
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:2193")

# Convert to WGS84 (lat/lon)
gdf = gdf.to_crs(epsg=4326)

# Extract centroid lat/lon
gdf["latitude"] = gdf.geometry.centroid.y
gdf["longitude"] = gdf.geometry.centroid.x
gdf["facility_type"] = gdf["use"]

# Save to CSV
gdf[["name", "facility_type", "latitude", "longitude"]].to_csv("schools_with_latlon.csv", index=False)

print(gdf[["name", "facility_type", "latitude", "longitude"]])