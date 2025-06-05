import os
import pandas as pd
import time
from tower_analysis.coverage_analysis import (
    count_facilities_within_coverage,
    calculate_population_within_coverage,
)
from tower_analysis import config


def rank_failed_towers(failed_exclusive_coverage, population_gdf, facility_gdf, weights, logger=None):
    for key in ["hospital", "police", "fire_station", "population_scale"]:
        if key not in weights:
            raise ValueError(f"Missing weight for key: {key}")

    facility_counts = count_facilities_within_coverage(failed_exclusive_coverage, facility_gdf)
    pop_weighted, pop_unweighted = calculate_population_within_coverage(failed_exclusive_coverage, population_gdf)

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

        if logger:
            logger.debug(f"Tower {tower_id} | police: {facilities.get('police', 0)} | "
                         f"fire: {facilities.get('fire_station', 0)} | hospital: {facilities.get('hospital', 0)} | "
                         f"pop_w: {pop_w:.2f} | score: {score:.2f}")

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


def get_user_weights(disaster_type="Default"):
    """
    Return predefined weights based on the selected disaster type.
    Falls back to 'Default' if not found.
    """
    if "Default" not in config.PRESET_WEIGHTS:
        config.PRESET_WEIGHTS["Default"] = {
            "hospital": 10,
            "police": 6,
            "fire_station": 8,
            "population_scale": 0.0005,
        }

    if disaster_type in config.PRESET_WEIGHTS:
        return config.PRESET_WEIGHTS[disaster_type]
    else:
        return config.PRESET_WEIGHTS["Default"]