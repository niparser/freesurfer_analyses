import logging
from pathlib import Path
from typing import Union

from freesurfer_analyses.utils.data_grabber import DataGrabber
from freesurfer_analyses.utils.messages import MISSING_DATAGRABBER

LOGGER_CONFIG = dict(
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)


def validate_instantiation(
    instance: object,
    base_dir: Path = None,
    data_grabber: DataGrabber = None,
) -> DataGrabber:
    """
    Validates the instansitation of *NativeParcellation* object with base
    directory or DataGrabber instance.

    Parameters
    ----------
    base_dir : Path, optional
        A base directory of *dmriprep*'s derivatives, by default None
    data_grabber : DataGrabber, optional
        A DataGrabber instance, already instansiated with a *base_dir*, by
        default None

    Returns
    -------
    DataGrabber
        An instansiated DataGrabber
    """
    if isinstance(data_grabber, DataGrabber):
        return data_grabber
    if base_dir:
        return DataGrabber(base_dir)
    raise ValueError(MISSING_DATAGRABBER.format(object_name=instance.__name__))


def collect_subjects(
    instance: object,
    participant_labels: Union[str, list] = None,
) -> dict:
    """
    Queries available sessions for *participant_labels*.

    Parameters
    ----------
    participant_labels : Union[str, List], optional
        Specific participants' labels to be queried, by default None

    Returns
    -------
    dict
        A dictionary with participant labels as keys and available
         sessions as values
    """
    if not participant_labels:
        return instance.data_grabber.subjects

    if isinstance(participant_labels, str):
        participant_labels = [participant_labels]
    return {
        participant_label: instance.data_grabber.subjects.get(
            participant_label
        )
        for participant_label in participant_labels
    }
