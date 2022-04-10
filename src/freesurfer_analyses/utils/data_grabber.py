"""
Definition of the :class:`DataGrabber` class.
"""
from pathlib import Path

from freesurfer_analyses.data.bids import THEBASE_FILTERS
from freesurfer_analyses.utils.bids import apply_bids_filters


class DataGrabber:
    #: Templates
    SUBJECT_TEMPLATE = "sub-"
    SESSION_TEMPLATE = "ses-"

    #: Freesurfer command line parh
    FREESURFER_CMD = "scripts/recon-all.cmd"

    def __init__(
        self, base_dir: Path, bids_filters: dict = THEBASE_FILTERS
    ) -> None:
        self.base_dir = Path(base_dir)
        self.bids_filters = bids_filters

    def query_subjects(self) -> dict:
        """
        Queries a derivatives' directory and locates all available subjects
        and their corresponding sessions.

        Returns
        -------
        dict
            A dictionary with participant labels as keys and available
            sessions as values
        """
        subjects = {}
        for subj in sorted(self.base_dir.glob(f"{self.SUBJECT_TEMPLATE}*")):
            participant_label = subj.name.replace(self.SUBJECT_TEMPLATE, "")
            subjects[participant_label] = {}
            for sess in sorted(subj.glob(f"{self.SESSION_TEMPLATE}*")):
                session_label = sess.name.replace(self.SESSION_TEMPLATE, "")
                subjects[participant_label][
                    session_label
                ] = apply_bids_filters(
                    sess,
                    self.bids_filters,
                )
        return subjects

    @property
    def subjects(self) -> dict:
        return self.query_subjects()
