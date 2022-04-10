from pathlib import Path
from typing import List
from typing import Union

from freesurfer_analyses.utils.utils import apply_bids_filters
from freesurfer_analyses.utils.utils import collect_subjects
from freesurfer_analyses.utils.utils import validate_instantiation


class FreesurferManager:
    BIDS_FILTERS = {"T1w": {"ceagent": "corrected"}}

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        self.data_grabber = validate_instantiation(self, base_dir)
        self.subjects = collect_subjects(self, participant_labels)
