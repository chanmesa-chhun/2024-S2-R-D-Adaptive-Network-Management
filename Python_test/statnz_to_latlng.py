import csv
from pyproj import Transformer

# Create a Transformer that converts from EPSG:2193 (NZTM2000) to EPSG:4326 (WGS84)
transformer = Transformer.from_crs("EPSG:2193", "EPSG:4326", always_xy=True)

input_file = 'population_250m.csv'
output_file = 'population_250m_latlng.csv'

with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', newline='', encoding='utf-8') as outfile:

    reader = csv.DictReader(infile)
    # Add "lat" and "lng" to the list of fields
    fieldnames = reader.fieldnames + ["lat", "lng"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        # Parse EPSG:2193 coordinates (e.g., "CENTROID_X" and "CENTROID_Y")
        x_2193 = float(row["CENTROID_X"])
        y_2193 = float(row["CENTROID_Y"])

        # Transform from NZTM (x,y) to WGS84 (lng, lat)
        lng, lat = transformer.transform(x_2193, y_2193)

        # Add lat and lng to the row
        row["lat"] = lat
        row["lng"] = lng

        # Write the updated row to the new CSV
        writer.writerow(row)

print(f"Conversion complete! New file saved as {output_file}.")
