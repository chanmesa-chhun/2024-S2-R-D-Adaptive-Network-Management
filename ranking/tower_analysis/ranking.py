# ranking.py
import pandas as pd
from tower_analysis.coverage_analysis import (
    count_facilities_within_coverage,
    calculate_population_within_coverage,
)

def rank_failed_towers(failed_exclusive_coverage, population_gdf, facility_gdf, weights):
    """
    Rank failed towers based on weighted scores calculated from uncovered facilities and population.

    Parameters:
        failed_exclusive_coverage (dict): {tower_id: geometry} of exclusive areas
        population_gdf (GeoDataFrame): Population shapefile with PopEst2023
        facility_gdf (GeoDataFrame): Facilities within exclusive areas
        weights (dict): Weight config for each feature type and population scale

    Returns:
        DataFrame: Sorted ranking of towers with score and counts
    """
    # Validate weights
    for key in ["hospital", "police", "fire_station", "population_scale"]:
        if key not in weights:
            raise ValueError(f"Missing weight for key: {key}")

    # Count how many facilities each tower covers
    facility_counts = count_facilities_within_coverage(failed_exclusive_coverage, facility_gdf)

    # Calculate how many people each tower covers
    pop_weighted, pop_unweighted = calculate_population_within_coverage(
        failed_exclusive_coverage, population_gdf
    )

    # Compute weighted scores
    scores = []
    for tower_id in failed_exclusive_coverage:
        facilities = facility_counts.get(tower_id, {})
        pop_w = pop_weighted.get(tower_id, 0)
        pop_unw = pop_unweighted.get(tower_id, 0)

        score = (
            facilities.get("police", 0) * weights["police"] +
            facilities.get("fire_station", 0) * weights["fire_station"] +
            facilities.get("hospital", 0) * weights["hospital"] +
            pop_w * weights["population_scale"]
        )

        scores.append({
            "tower_id": tower_id,
            "police": facilities.get("police", 0),
            "fire_station": facilities.get("fire_station", 0),
            "hospital": facilities.get("hospital", 0),
            "weighted_population": round(pop_w, 2),
            "unweighted_population": int(pop_unw),
            "score": round(score, 2)
        })

    df = pd.DataFrame(scores)
    return df.sort_values(by="score", ascending=False)


def save_ranking_to_csv(df, output_path):
    """
    Save the ranking result DataFrame to CSV.

    Parameters:
        df (DataFrame): The ranking DataFrame
        output_path (str): File path to save to
    """
    df.to_csv(output_path, index=False)


def get_user_weights():
    """
    Prompt user to select a disaster type or input custom weights.

    Returns:
        dict: Weight configuration based on user input
    """
    from . import config

    def input_positive_int(prompt):
        while True:
            try:
                value = int(input(prompt))
                if value > 0:
                    return value
                else:
                    print("Please enter a positive integer.")
            except ValueError:
                print("Invalid input. Please enter a positive integer.")

    def input_positive_float(prompt):
        while True:
            try:
                value = float(input(prompt))
                if value > 0:
                    return value
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a positive number.")

    print("\nSelect disaster type:")
    disaster_types = list(config.PRESET_WEIGHTS.keys())
    for i, disaster in enumerate(disaster_types):
        print(f"{i + 1}. {disaster}")

    while True:
        try:
            choice = int(input("Enter the number of the disaster type: "))
            if 1 <= choice <= len(disaster_types):
                selected = disaster_types[choice - 1]
                break
            else:
                print("Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    if selected == "custom":
        print("\nEnter custom positive weights:")
        h = input_positive_int("Weight for hospital: ")
        p = input_positive_int("Weight for police: ")
        f = input_positive_int("Weight for fire station: ")
        pop = input_positive_float("Population scaling factor: ")
        weights = {
            "hospital": h,
            "police": p,
            "fire_station": f,
            "population_scale": pop
        }
    else:
        weights = config.PRESET_WEIGHTS[selected]
        print(f"\nUsing preset weights for {selected}: {weights}")

    return weights
