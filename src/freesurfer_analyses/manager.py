from pathlib import Path
from typing import List
from typing import Union

from freesurfer_analyses.utils.utils import apply_bids_filters
from freesurfer_analyses.utils.utils import collect_subjects
from freesurfer_analyses.utils.utils import validate_instantiation


class FreesurferManager:
    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        self.data_grabber = validate_instantiation(self, base_dir)
        self.subjects = collect_subjects(self, participant_labels)

    def get_transforms(
        self,
        participant_label: str,
        bids_filters: dict = None,
        queries: dict = {},
    ) -> dict:
        """
        Locates subject-specific transformation warp from standard (MNI) space
        to native.

        Parameters
        ----------
        participant_label : str
            Specific participant's label to be queried

        Returns
        -------
        dict
            dictionary of paths to MNI-to-native
            and native-to-MNI transforms (.h5)
        """
        transforms = {}
        for transform in self.TRANSFORMS:

            query = dict(subject=participant_label, **queries.get(transform))
            query = apply_bids_filters(query, bids_filters)
            result = self.data_grabber.layout.get(**query)
            transforms[transform] = Path(result[0].path) if result else None
        return transforms

    def get_reference(
        self,
        participant_label: str,
        reference_type: str = "anat",
        bids_filters: dict = None,
        queries: dict = {},
    ) -> Path:
        """
        Locate a reference image

        Parameters
        ----------
        participant_label : str
            Specific participant's label to be queried
        reference_type : str, optional
            Any default available reference types, either "anat" or "dwi",
            by default "anat"
        space : str, optional
            Image's space, by default None
        session : str, optional
            Specific session to be queried, by default None

        Returns
        -------
        Path
            Path to the result reference image.
        """
        query = dict(
            subject=participant_label,
            **queries.get(f"{reference_type}_reference"),
        )
        query = apply_bids_filters(query, bids_filters)
        result = self.data_grabber.layout.get(**query)
        return Path(result[0].path) if result else None

    def get_probseg(
        self,
        participant_label: str,
        tissue_type: str = "GM",
        bids_filters: dict = None,
        queries: dict = None,
    ) -> Path:
        """
        Locates subject's tissue probability segmentations

        Parameters
        ----------
        participant_label : str
            Specific participant's label to be queried
        tissue_type : str, optional
            Tissue to be queried, by default "GM"
        space : str, optional
            Image's space, by default None

        Returns
        -------
        Path
            Path to tissue probability segmentations image
        """
        query = dict(
            subject=participant_label,
            label=tissue_type.upper(),
            **queries.get("probseg"),
        )
        query = apply_bids_filters(query, bids_filters)
        result = self.data_grabber.layout.get(**query)
        return Path(result[0].path) if result else None

    def get_subject_dwi(self, participant_label: str, session: str = None, queries: dict = None) -> List[dict]:
        """
        Locate subject's available preprocessed DWIs and their corresponding
        gradients (.bvec and .bval).

        Parameters
        ----------
        participant_label : str
            Specific participants' labels to be queried
        session : str, optional
            Specific session's ID, by default None

        Returns
        -------
        List[dict]
            A list of dictionary with keys of ["dwi","bvec","bval"] for all
            available DWIs
        """
        query = dict(
            subject=participant_label,
            **queries,
        )
        if session:
            query["session"] = session
        dwi_files = self.data_grabber.layout.get(**query, return_type="file")
        result = []
        for dwi in dwi_files:
            result.append(
                {
                    "dwi": dwi,
                    "bval": self.data_grabber.layout.get_bval(dwi),
                    "bvec": self.data_grabber.layout.get_bvec(dwi),
                    "mask": self.data_grabber.build_path(dwi, {"desc": "brain", "suffix": "mask"}),
                }
            )
        return result
