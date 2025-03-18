import pandas as pd
from geopy.distance import geodesic

def load_data(population_file, celltower_file):
    # Load population data
    population_df = pd.read_csv(population_file)
    # Load cell tower data
    celltower_df = pd.read_csv(celltower_file)
    return population_df, celltower_df

def calculate_population_within_radius(population_df, celltower_df, radius_km=5):
    results = []
    
    for _, tower in celltower_df.iterrows():
        tower_location = (tower['antlat'], tower['antlng'])
        total_population_2022 = 0
        total_population_2023 = 0
        
        for _, grid in population_df.iterrows():
            grid_location = (grid['Latitude'], grid['Longitude'])
            distance = geodesic(tower_location, grid_location).km
            
            if distance <= radius_km:
                total_population_2022 += grid['PopEst2022']
                total_population_2023 += grid['PopEst2023']
        
        results.append({
            'sitename': tower['sitename'],
            'total_population_2022': total_population_2022,
            'total_population_2023': total_population_2023
        })
    
    return pd.DataFrame(results)

def main():
    # File paths
    population_file = 'population_100m_with_latlon.csv'
    celltower_file = 'prototype2_celltowers.csv'
    
    # Load data
    population_df, celltower_df = load_data(population_file, celltower_file)
    
    # Calculate population within 5km radius for each cell tower
    result_df = calculate_population_within_radius(population_df, celltower_df, radius_km=5)
    
    # Save results
    result_df.to_csv('cell_tower_population.csv', index=False)
    print("Results saved to cell_tower_population.csv")
    
if __name__ == "__main__":
    main()
