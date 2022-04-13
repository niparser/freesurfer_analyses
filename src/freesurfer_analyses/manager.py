import datetime
import logging
import os
from pathlib import Path
from typing import Union

from brain_parts.parcellation.parcellations import (
    Parcellation as parcellation_manager,
)

from freesurfer_analyses.utils.utils import LOGGER_CONFIG
from freesurfer_analyses.utils.utils import collect_subjects
from freesurfer_analyses.utils.utils import validate_instantiation


class FreesurferManager:
    BIDS_FILTERS = {"T1w": {"ceagent": "corrected"}}
    LOGGER_FILE = "freesurfer_analyses-{timestamp}.log"

    #: Hemispheres
    HEMISPHERES_LABELS = ["lh", "rh"]
    SUBCORTICAL_LABELS = ["subcortex"]

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
        logging_destination: Path = None,
    ) -> None:
        self.data_grabber = validate_instantiation(self, base_dir)
        self.subjects = collect_subjects(self, participant_labels)
        self.parcellation_manager = parcellation_manager()
        self.initiate_logging(logging_destination)

    def initiate_logging(self, logging_destination: Path = None) -> None:
        """
        Initiates logging.

        Parameters
        ----------
        logging_destination : Path, optional
            A path to a file where the logging will be saved, by default None
        """
        logging_destination = (
            Path(logging_destination)
            if logging_destination
            else self.data_grabber.base_dir / "log"
        )
        logging_destination.mkdir(exist_ok=True)
        timestamp = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")
        logging.basicConfig(
            filename=str(
                logging_destination
                / self.LOGGER_FILE.format(timestamp=timestamp)
            ),
            **LOGGER_CONFIG,
        )

    def set_subjects_dir(self, subjects_dir: Path) -> None:
        """
        Set the enviorment variable SUBJECTS_DIR

        Parameters
        ----------
        subjects_dir : Path
            Path to the subjects' directory
        """
        os.environ["SUBJECTS_DIR"] = str(subjects_dir)

    def validate_parcellation(
        self, parcellation_scheme: str, key: str
    ) -> Path:
        """
        Validate that *parcellation scheme* has a valid *key*.

        Parameters
        ----------
        parcellation_scheme : str
            Parcellation scheme to be validated.
        key : str
            Key to be validated.

        Returns
        -------
        Path
            Path to the parcellation scheme.

        Raises
        ------
        ValueError
            If *parcellation scheme* has no *key*.
        """
        parcellation_key = self.parcellation_manager.parcellations.get(
            parcellation_scheme
        ).get(key)
        if not parcellation_key:
            raise ValueError(
                f"No available {key} was found for {parcellation_scheme}."
            )
        return Path(parcellation_key)

    def validate_session(
        self, participant_label: str, session: Union[str, list] = None
    ) -> list:
        """
        Validates session's input type (must be list)

        Parameters
        ----------
        participant_label : str
            Specific participants' labels
        session : Union[str, list], optional
            Specific session(s)' labels, by default None

        Returns
        -------
        list
            Either specified or available session(s)' labels
        """
        if session:
            if isinstance(session, str):
                sessions = [session]
            elif isinstance(session, list):
                sessions = session
        else:
            sessions = self.subjects.get(participant_label)
        return sessions

    def validate_participant_label(self, participant_label: str) -> list:
        """
        Validates participant's label.

        Parameters
        ----------
        participant_label : str
            Specific participant's label

        Returns
        -------
        list
            Either specified or available participant's labels
        """
        if participant_label:
            if isinstance(participant_label, str):
                participant_labels = [participant_label]
            elif isinstance(participant_label, list):
                participant_labels = participant_label
        else:
            participant_labels = list(sorted(self.subjects.keys()))
        return participant_labels

    def build_output_dictionary(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        hemi: str,
    ) -> dict:
        """
        Build a dictionary with the following structure:
        {"path":path to the output file, "exists":True/False}

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        source_file : str
            Path to a file used as source for Freesurfer's pipeline.
        hemi : str
            Hemisphere to be parcellated.

        Returns
        -------
        dict
            A dictionary with keys of "path" and "exists" and corresponding values.
        """
        pass
