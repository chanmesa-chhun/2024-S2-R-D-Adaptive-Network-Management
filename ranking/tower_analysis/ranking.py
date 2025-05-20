# tower_analysis/ranking.py

import pandas as pd
from tower_analysis.coverage_analysis import (
    count_facilities_within_coverage,
    calculate_population_within_coverage,
)
from tower_analysis import config


def get_user_weights(scenario: str = "Default") -> dict:
    """
    Return the preset weights dict for the given scenario,
    falling back to 'Default' if missing or invalid.
    """
    presets = config.PRESET_WEIGHTS
    return presets.get(scenario, presets["Default"])


def rank_failed_towers(
    failed_exclusive_coverage: dict,
    population_gdf,
    facility_gdf,
    user_weights: dict,
    logger=None,
) -> pd.DataFrame:
    # Validate keys
    for key in ["hospital", "police", "fire_station", "population_scale"]:
        if key not in user_weights or user_weights[key] is None:
            raise ValueError(f"Missing or invalid weight for '{key}'")

    # Count facilities & population
    fac_counts = count_facilities_within_coverage(failed_exclusive_coverage, facility_gdf)
    pop_w, pop_unw = calculate_population_within_coverage(
        failed_exclusive_coverage, population_gdf
    )

    # Assemble scores
    records = []
    for tid, geom in failed_exclusive_coverage.items():
        f = fac_counts.get(tid, {})
        pw = pop_w.get(tid, 0)
        record = {
            "tower_id": tid,
            "police": f.get("police", 0),
            "fire_station": f.get("fire_station", 0),
            "hospital": f.get("hospital", 0),
            "weighted_population": round(pw, 2),
            "unweighted_population": int(pop_unw.get(tid, 0)),
            "score": round(
                f.get("police", 0) * user_weights["police"]
                + f.get("fire_station", 0) * user_weights["fire_station"]
                + f.get("hospital", 0) * user_weights["hospital"]
                + pw * user_weights["population_scale"],
                2,
            ),
        }
        if logger:
            logger.debug(f"Tower {tid} → {record}")
        records.append(record)

    return pd.DataFrame(records).sort_values("score", ascending=False)


def save_ranking_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """Persist the ranking to CSV."""
    df.to_csv(output_path, index=False)
