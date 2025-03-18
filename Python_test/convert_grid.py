import pandas as pd

# File names
input_file = "population_250m.csv" # input file name
output_file = "population_100m.csv"

def convert_250m_to_100m(df):
    """
    Converts a dataset from 250m grid resolution to 100m grid resolution.
    
    Parameters:
        df (pd.DataFrame): Original dataset with 250m grid cells.
        
    Returns:
        pd.DataFrame: New dataset with 100m grid cells.
    """

    subdivision_size = 100  # 100m grid size
    original_size = 250  # 250m grid size
    num_subdivisions = 6  # Each 250m cell splits into 6 smaller 100m cells

    new_rows = []

    for _, row in df.iterrows():
        centroid_x, centroid_y = row["CENTROID_X"], row["CENTROID_Y"]
        pop_2022, pop_2023 = row["PopEst2022"], row["PopEst2023"]
        
        # Calculate the min X and min Y (bottom-left corner of 250m grid)
        min_x = centroid_x - (original_size / 2) + (subdivision_size / 2)
        min_y = centroid_y - (original_size / 2) + (subdivision_size / 2)

        # Create 6 smaller 100m x 100m grids within the 250m grid
        for i in range(2):  # Two along X-axis
            for j in range(3):  # Three along Y-axis
                new_x = min_x + (i * subdivision_size)
                new_y = min_y + (j * subdivision_size)
                
                # Generate new GridID
                new_grid_id = f"E{int(new_x)}N{int(new_y)}"

                # Create new WKT MULTIPOLYGON
                new_wkt = f"MULTIPOLYGON ((({new_x - 50} {new_y - 50}, {new_x - 50} {new_y + 50}, {new_x + 50} {new_y + 50}, {new_x + 50} {new_y - 50}, {new_x - 50} {new_y - 50})))"

                # Proportionally distribute population estimates
                new_pop_2022 = pop_2022 / num_subdivisions
                new_pop_2023 = pop_2023 / num_subdivisions

                # Append new row
                new_rows.append({
                    "WKT": new_wkt,
                    "GridID": new_grid_id,
                    "CENTROID_X": new_x,
                    "CENTROID_Y": new_y,
                    "PopEst2022": new_pop_2022,
                    "PopEst2023": new_pop_2023,
                    "Shape_Length": 400  # 100m grid has a perimeter of 400m
                })

    # Convert to DataFrame
    return pd.DataFrame(new_rows)

# Load the dataset from CSV
try:
    df_250m = pd.read_csv(input_file)

    # Convert 250m grid to 100m grid
    df_100m = convert_250m_to_100m(df_250m)

    # Save new dataset to a CSV file
    df_100m.to_csv(output_file, index=False)

    print(f"Conversion complete! New dataset saved as '{output_file}'.")

except FileNotFoundError:
    print(f"Error: The file '{input_file}' was not found. Please ensure it is in the same folder as this script.")
except Exception as e:
    print(f"An error occurred: {e}")
