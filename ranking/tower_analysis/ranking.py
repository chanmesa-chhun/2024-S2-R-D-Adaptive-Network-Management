import pandas as pd
from tower_analysis.coverage_analysis import (
    count_facilities_within_coverage,
    calculate_population_within_coverage,
)

def rank_failed_towers(failed_exclusive_coverage, population_gdf, facility_gdf, weights):
    facility_counts = count_facilities_within_coverage(failed_exclusive_coverage, facility_gdf)
    pop_weighted, pop_unweighted = calculate_population_within_coverage(failed_exclusive_coverage, population_gdf)

    scores = []
    for tower_id in failed_exclusive_coverage:
        facilities = facility_counts.get(tower_id, {})
        pop_w = pop_weighted.get(tower_id, 0)
        pop_unw = pop_unweighted.get(tower_id, 0)

        score = (
            facilities.get("police", 0) * weights.get("police", 0) +
            facilities.get("fire_station", 0) * weights.get("fire_station", 0) +
            facilities.get("hospital", 0) * weights.get("hospital", 0) +
            pop_w * weights.get("population_scale", 0)
        )

        scores.append({
            "tower_id": tower_id,
            "police": facilities.get("police", 0),
            "fire_station": facilities.get("fire_station", 0),
            "hospital": facilities.get("hospital", 0),
            "weighted_population": pop_w,
            "unweighted_population": pop_unw,
            "score": score
        })

    df = pd.DataFrame(scores)
    return df.sort_values(by="score", ascending=False)

def save_ranking_to_csv(df, output_path):
    df.to_csv(output_path, index=False)


def get_user_weights():
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
