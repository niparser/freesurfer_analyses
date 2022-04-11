import datetime
import logging
from pathlib import Path
from typing import Union

from freesurfer_analyses.utils.utils import LOGGER_CONFIG
from freesurfer_analyses.utils.utils import collect_subjects
from freesurfer_analyses.utils.utils import validate_instantiation


class FreesurferManager:
    BIDS_FILTERS = {"T1w": {"ceagent": "corrected"}}
    LOGGER_FILE = "freesurfer_analyses-{timestamp}.log"

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
        logging_destination: Path = None,
    ) -> None:
        self.data_grabber = validate_instantiation(self, base_dir)
        self.subjects = collect_subjects(self, participant_labels)
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
            ),  # noqa
            **LOGGER_CONFIG,
        )
