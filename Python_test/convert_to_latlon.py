import pandas as pd
from pyproj import Transformer

# Input and output file names
input_file = "population_100m.csv"  # The 100m grid dataset
output_file = "population_100m_with_latlon.csv"  # Output file with lat/lon

# Define coordinate transformation from NZTM2000 (EPSG:2193) to WGS84 (EPSG:4326)
transformer = Transformer.from_crs("EPSG:2193", "EPSG:4326", always_xy=True)

def convert_nztm_to_wgs84(df):
    """
    Converts NZTM2000 coordinates to WGS84 (lat/lon) for Google Maps.

    Parameters:
        df (pd.DataFrame): DataFrame with NZTM2000 (meters) coordinates.

    Returns:
        pd.DataFrame: Updated DataFrame with Longitude and Latitude columns.
    """

    # Convert each row's centroid
    lon_list, lat_list = [], []
    for _, row in df.iterrows():
        lon, lat = transformer.transform(row["CENTROID_X"], row["CENTROID_Y"])
        lon_list.append(lon)
        lat_list.append(lat)

    # Add new Longitude and Latitude columns
    df["Longitude"] = lon_list
    df["Latitude"] = lat_list

    return df

# Load the dataset
try:
    df_100m = pd.read_csv(input_file)

    # Convert coordinates
    df_100m = convert_nztm_to_wgs84(df_100m)

    # Save new dataset
    df_100m.to_csv(output_file, index=False)

    print(f"Conversion complete! New dataset saved as '{output_file}'.")

except FileNotFoundError:
    print(f"Error: The file '{input_file}' was not found. Please ensure it is in the same folder as this script.")
except Exception as e:
    print(f"An error occurred: {e}")
