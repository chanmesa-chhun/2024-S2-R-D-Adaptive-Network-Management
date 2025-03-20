import pandas as pd
from pyproj import Transformer

# File names
input_file = "ranKH.SITES.csv"  # Your original cell tower data file
output_file = "celltower_data_utm.csv"  # Clean output file with .csv extension

# Set up the transformer:
# Source CRS: NZMG (EPSG:27200)
# Target CRS: NZTM2000 (EPSG:2193)
transformer = Transformer.from_crs("EPSG:27200", "EPSG:2193", always_xy=True)

# Load the cell tower data
df = pd.read_csv(input_file)

def convert_coords(row):
    try:
        # Convert the LONGITUDE and LATITUDE values (assumed to be in NZMG)
        lon = float(row["LONGITUDE"])
        lat = float(row["LATITUDE"])
        utm_easting, utm_northing = transformer.transform(lon, lat)
        return pd.Series({"utm_easting": utm_easting, "utm_northing": utm_northing})
    except Exception as e:
        print(f"Error converting row for NAME {row['NAME']}: {e}")
        return pd.Series({"utm_easting": None, "utm_northing": None})

# Apply conversion to each row
df[['utm_easting', 'utm_northing']] = df.apply(convert_coords, axis=1)

# Keep only the NAME and the new coordinate columns
df_clean = df[['NAME', 'utm_easting', 'utm_northing']]

# Remove duplicates that have the same NAME and coordinates
df_clean = df_clean.drop_duplicates(subset=["NAME", "utm_easting", "utm_northing"], keep="first")

# Save the cleaned DataFrame to a new CSV file
df_clean.to_csv(output_file, index=False)

print(f"Transformation complete! Clean file saved as '{output_file}'.")
