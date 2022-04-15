from pathlib import Path
from typing import Union

import pandas as pd
from freesurfer_stats import CorticalParcellationStats


def read_stats_file(
    stats_file: Union[Path, str],
    target_parcels: pd.DataFrame,
    label_column: str = "FS_name",
) -> pd.DataFrame:
    """
    Reads a stats file and returns a dataframe with the values of the
    stats file for each parcel in the target_parcels dataframe.
    """
    stats_file = Path(stats_file)
    if not stats_file.exists():
        raise FileNotFoundError(f"{stats_file} does not exist.")
    # Read the stats file
    stats_df = CorticalParcellationStats.read(
        stats_file
    ).structural_measurements
    # Transform ROI names to corresponding labels
    stats_df["Label"] = (
        target_parcels.set_index(label_column)
        .loc[stats_df["structure_name"].values, "Label"]
        .values
    )
    # Drop the structure name column
    stats_df = stats_df.drop(columns=["structure_name"])
    stats_df.set_index("Label", inplace=True)
    return stats_df.transpose()
