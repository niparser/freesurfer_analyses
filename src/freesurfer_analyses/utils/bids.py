import re
from pathlib import Path

from freesurfer_analyses.data.bids import BIDS_ENTITIES


def apply_bids_filters(
    base_dir: Path,
    bids_filters: dict = {},
) -> list:
    """
    Iterates over directories under *base_dir* that represent names of inputs
    to *recon-all* pipeline, to locate those that match *bids_filters*

    Parameters
    ----------
    base_dir : Path
        Freesurfer derivatives directory
    bids_filters : dict
        Dictionary with BIDS filters (entities and values)

    Returns
    -------
    list
        List of paths to files that match the filters
    """
    source_data = [i for i in Path(base_dir).glob("anat/*")]
    anatomical_filters = bids_filters.get("anat")
    if not anatomical_filters:
        return source_data
    return [i for i in source_data if match_filters(i, anatomical_filters)]


def match_filters(in_file: Path, bids_filters: dict = {}) -> bool:
    """
    Matches a file with a dictionary of filters.

    Parameters
    ----------
    in_file : Path
        Path to file to be matched
    bids_filters : dict, optional
        Dictionary with BIDS filters (entities and values), by default {}

    Returns
    -------
    bool
        True if the file matches the filters, False otherwise

    Raises
    ------
    ValueError
        If an invalid entity is found in the filters
    """
    flags = {}
    parts = Path(in_file).name.split("_")
    for key, value in bids_filters.items():
        flags[key] = False
        entity = BIDS_ENTITIES.get(key)
        if not entity:
            raise ValueError(f"{key} is not a valid BIDS entity")
        pattern = entity.get("pattern")
        for part in parts:
            if re.match(pattern, part) and part.split("-")[-1] == value:
                flags[key] = True
                break
    return all(flags.values())
