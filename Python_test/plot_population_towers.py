import pandas as pd
import matplotlib.pyplot as plt

# Load datasets
population_file = "population_50m.csv"
celltower_file = "celltower_data_utm.csv"

population_df = pd.read_csv(population_file)
celltower_df = pd.read_csv(celltower_file)

# Plot the data
plt.figure(figsize=(10, 6))
plt.scatter(population_df["CENTROID_X"], population_df["CENTROID_Y"],
            color="blue", s=1, label="Population Grids")

plt.scatter(celltower_df["utm_easting"], celltower_df["utm_northing"], 
            color="red", s=10, label="Cell Towers", marker="x")

plt.xlabel("UTM Easting")
plt.ylabel("UTM Northing")
plt.title("Population Grids vs Cell Towers")
plt.legend()
plt.show()
