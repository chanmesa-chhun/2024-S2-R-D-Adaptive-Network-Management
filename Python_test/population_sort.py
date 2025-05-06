import pandas as pd

# File name of your cell tower coverage results
input_file = "cell_tower_population_50m_precise.csv"

# Read the CSV file
df = pd.read_csv(input_file)

# Sort the DataFrame by 'total_population_2023' in descending order
df_sorted = df.sort_values("total_population_2023", ascending=False)

# Display the sorted DataFrame
print(df_sorted.to_string(index=False))