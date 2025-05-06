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
