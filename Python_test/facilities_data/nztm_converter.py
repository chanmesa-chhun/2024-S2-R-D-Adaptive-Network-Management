import pandas as pd
from pyproj import Transformer

# File names
input_file = "firestation_data.csv"       # Data file with lat/lon in WGS84
output_file = "firestation_data_nztm.csv"   # Output file with converted NZTM2000 coordinates

# Set up the transformer:
# Source CRS: WGS84 (EPSG:4326)
# Target CRS: NZTM2000 (EPSG:2193)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:2193", always_xy=True)

# Load the data
df = pd.read_csv(input_file)

# Debug: Print original columns
print("Original columns:", df.columns.tolist())

# Strip extra whitespace from headers
df.columns = df.columns.str.strip()

# Debug: Print cleaned column names
print("Cleaned columns:", df.columns.tolist())

# Rename columns to match desired names
df = df.rename(columns={
    "Name": "name",
    "Type": "facility_type",
    "Latitude": "latitude",
    "Longitude": "longitude"
})

# Debug: Verify renaming
print("Renamed columns:", df.columns.tolist())

def convert_coords(row):
    try:
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        utm_easting, utm_northing = transformer.transform(lon, lat)
        return pd.Series({"utm_easting": utm_easting, "utm_northing": utm_northing})
    except Exception as e:
        # Using .get to provide a default if the key doesn't exist
        print(f"Error converting row for {row.get('name', 'unknown')}: {e}")
        return pd.Series({"utm_easting": None, "utm_northing": None})

# Apply conversion to each row
df[['utm_easting', 'utm_northing']] = df.apply(convert_coords, axis=1)

# Keep desired columns (if you want to keep more info, adjust as necessary)
df_clean = df[['name', 'facility_type', 'latitude', 'longitude', 'utm_easting', 'utm_northing']]

# Save the cleaned DataFrame to a new CSV file
df_clean.to_csv(output_file, index=False)

print(f"Transformation complete! Clean file saved as '{output_file}'.")
