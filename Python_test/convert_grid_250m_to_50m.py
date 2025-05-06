import pandas as pd
from tqdm import tqdm

# File names
input_file = "population_250m.csv"  # 250m grid file
output_file = "population_50m.csv"  # output file for 50m grid

def convert_250m_to_50m(df):
    """
    Converts a dataset from 250m grid resolution to 50m grid resolution.
    Each 250m square is divided evenly into 25 (5x5) squares.
    Population estimates are evenly distributed to each 50m square.
    """
    new_rows = []
    original_size = 250  # original square side length in meters
    new_size = 50        # new square side length in meters
    subdivisions = original_size // new_size  # should be 5

    # Wrap the iteration over rows with tqdm for progress display.
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Converting 250m to 50m grids"):
        centroid_x = row["CENTROID_X"]
        centroid_y = row["CENTROID_Y"]
        pop_2022 = row["PopEst2022"]
        pop_2023 = row["PopEst2023"]

        # Calculate the bottom-left (BL) corner of the 250m square.
        bl_x = centroid_x - (original_size / 2)
        bl_y = centroid_y - (original_size / 2)

        # Loop through subdivisions (5 per axis => 25 cells)
        for i in range(subdivisions):  # along the x-axis
            for j in range(subdivisions):  # along the y-axis
                # Calculate bottom-left of the new 50m cell
                new_bl_x = bl_x + i * new_size
                new_bl_y = bl_y + j * new_size

                # Calculate top-right of the new cell
                new_tr_x = new_bl_x + new_size
                new_tr_y = new_bl_y + new_size

                # Calculate new cell centroid
                new_centroid_x = new_bl_x + new_size / 2
                new_centroid_y = new_bl_y + new_size / 2

                # Generate new GridID (using integer values of the centroid)
                new_grid_id = f"E{int(new_centroid_x)}N{int(new_centroid_y)}"

                # Create the new WKT for the 50m square polygon.
                new_wkt = (
                    f"MULTIPOLYGON ((({new_bl_x} {new_bl_y}, "
                    f"{new_bl_x} {new_tr_y}, "
                    f"{new_tr_x} {new_tr_y}, "
                    f"{new_tr_x} {new_bl_y}, "
                    f"{new_bl_x} {new_bl_y})))"
                )

                # Evenly distribute the population from the original square to the 25 new cells.
                new_pop_2022 = pop_2022 / (subdivisions * subdivisions)
                new_pop_2023 = pop_2023 / (subdivisions * subdivisions)

                new_rows.append({
                    "WKT": new_wkt,
                    "GridID": new_grid_id,
                    "CENTROID_X": new_centroid_x,
                    "CENTROID_Y": new_centroid_y,
                    "PopEst2022": new_pop_2022,
                    "PopEst2023": new_pop_2023,
                    "Shape_Length": new_size * 4  # perimeter of the new 50m square (50*4=200)
                })

    return pd.DataFrame(new_rows)

try:
    # Load the 250m grid data
    df_250m = pd.read_csv(input_file)
    
    # Convert to 50m grid cells
    df_50m = convert_250m_to_50m(df_250m)
    
    # Save the resulting DataFrame to CSV
    df_50m.to_csv(output_file, index=False)
    print(f"Conversion complete! New dataset saved as '{output_file}'.")
    
except FileNotFoundError:
    print(f"Error: The file '{input_file}' was not found. Please ensure it is in the same folder as this script.")
except Exception as e:
    print(f"An error occurred: {e}")
