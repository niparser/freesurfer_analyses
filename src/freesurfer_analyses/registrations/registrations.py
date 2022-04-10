"""
Definition of the :class:`NativeRegistration` class.
"""
from pathlib import Path
from typing import Tuple
from typing import Union

import nibabel as nib
from brain_parts.parcellation.parcellations import (
    Parcellation as parcellation_manager,
)
from nilearn.image.resampling import resample_to_img
from nipype.interfaces.base import TraitError
from tqdm import tqdm

from dmriprep_analyses.manager import DmriprepManager
from dmriprep_analyses.registrations.messages import REFERENCE_FILE_MISSING
from dmriprep_analyses.registrations.utils import DEFAULT_PARCELLATION_NAMING
from dmriprep_analyses.registrations.utils import PROBSEG_THRESHOLD
from dmriprep_analyses.registrations.utils import QUERIES
from dmriprep_analyses.registrations.utils import TRANSFORMS


class NativeRegistration(DmriprepManager):
    QUERIES = QUERIES

    #: Naming
    DEFAULT_PARCELLATION_NAMING = DEFAULT_PARCELLATION_NAMING

    #: Types of transformations
    TRANSFORMS = TRANSFORMS

    #: Default probability segmentations' threshold
    PROBSEG_THRESHOLD = PROBSEG_THRESHOLD

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        super().__init__(base_dir, participant_labels)
        self.parcellation_manager = parcellation_manager()

    def initiate_subject(self, participant_label: str) -> Tuple[dict, Path, Path]:
        """
        Query initially-required patricipant's files

        Parameters
        ----------
        participant_label : str
            Specific participant's label to be queried

        Returns
        -------
        Tuple[dict,Path,Path]
            A tuple of required files for parcellation registration.
        """
        return [
            grabber(participant_label, queries=self.QUERIES)
            for grabber in [
                self.get_transforms,
                self.get_reference,
                self.get_probseg,
            ]
        ]

    def build_output_dictionary(
        self,
        parcellation_scheme: str,
        reference: Path,
        reference_type: str,
    ) -> dict:
        """
        Based on a *reference* image,
        reconstruct output names for native parcellation naming.

        Parameters
        ----------
        reference : Path
            The reference image.
        reference_type : str
            The reference image type (either "anat" or "dwi")

        Returns
        -------
        dict
            A dictionary with keys of "whole-brain" and "gm-cropped" and their
            corresponding paths
        """
        basic_query = dict(
            atlas=parcellation_scheme,
            resolution=reference_type,
            **self.DEFAULT_PARCELLATION_NAMING.copy(),
        )
        outputs = dict()
        for key, label in zip(["whole_brain", "gm_cropped"], ["", "GM"]):
            query = basic_query.copy()
            query["label"] = label
            outputs[key] = self.data_grabber.build_path(reference, query)
        return outputs

    def register_to_anatomical(
        self,
        parcellation_scheme: str,
        participant_label: str,
        probseg_threshold: float = None,
        force: bool = False,
    ) -> dict:
        """
        Register a *parcellation scheme* from standard to native anatomical space. # noqa

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*.
        participant_label : str
            Specific participant's label
        probseg_threshold : float, optional
            Threshold for probability segmentation masking, by default None
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of "whole_brain" and "gm_cropped" native-spaced parcellation schemes.
        """
        transforms, reference, gm_probseg = self.initiate_subject(participant_label)
        whole_brain, gm_cropped = [
            self.build_output_dictionary(parcellation_scheme, reference, "anat").get(key) for key in ["whole_brain", "gm_cropped"]
        ]
        self.parcellation_manager.register_parcellation_scheme(
            parcellation_scheme,
            participant_label,
            reference,
            transforms.get("mni2native"),
            whole_brain,
            force=force,
        )
        self.parcellation_manager.crop_to_probseg(
            parcellation_scheme,
            participant_label,
            whole_brain,
            gm_probseg,
            gm_cropped,
            masking_threshold=probseg_threshold or self.PROBSEG_THRESHOLD,
            force=force,
        )
        return whole_brain, gm_cropped

    def register_dwi(
        self,
        parcellation_scheme: str,
        participant_label: str,
        session: str,
        anatomical_whole_brain: Path,
        anatomical_gm_cropped: Path,
        force: bool = False,
    ):
        """
        Resample parcellation scheme from anatomical to DWI space.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        participant_label : str
            Specific participant's label
        anatomical_whole_brain : Path
            Participant's whole-brain parcellation scheme in anatomical space
        anatomical_gm_cropped : Path
            Participant's GM-cropped parcellation scheme in anatomical space
        force : bool, optional
            Whether to re-write existing files, by default False
        """
        reference = self.get_reference(
            participant_label,
            "dwi",
            {"session": session},
            queries=self.QUERIES,
        )
        if not reference:
            raise FileNotFoundError(REFERENCE_FILE_MISSING.format(participant_label=participant_label))
        whole_brain, gm_cropped = [
            self.build_output_dictionary(parcellation_scheme, reference, "dwi").get(key) for key in ["whole_brain", "gm_cropped"]
        ]
        for source, target in zip(
            [anatomical_whole_brain, anatomical_gm_cropped],
            [whole_brain, gm_cropped],
        ):
            if not target.exists() or force:
                img = resample_to_img(str(source), str(reference), interpolation="nearest")
                nib.save(img, target)

        return whole_brain, gm_cropped

    def run_single_subject(
        self,
        parcellation_scheme: str,
        participant_label: str,
        session: Union[str, list] = None,
        probseg_threshold: float = None,
        force: bool = False,
    ) -> dict:
        """


        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        participant_label : str
            Specific participant's label
        session : Union[str, list], optional
            Specific sessions available for *participant_label*, by default None # noqa
        probseg_threshold : float, optional
            Threshold for probability segmentation masking, by default None
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of "anat" and available or requested sessions,
            and corresponding natice parcellations as keys.
        """
        outputs = {}
        anat_whole_brain, anat_gm_cropped = self.register_to_anatomical(parcellation_scheme, participant_label, probseg_threshold, force)
        outputs["anat"] = {
            "whole_brain": anat_whole_brain,
            "gm_cropped": anat_gm_cropped,
        }
        sessions = self.subjects.get(participant_label) or session
        if isinstance(sessions, str):
            sessions = [sessions]
        for session in sessions:
            whole_brain, gm_cropped = self.register_dwi(
                parcellation_scheme,
                participant_label,
                session,
                anat_whole_brain,
                anat_gm_cropped,
                force,
            )
            outputs[session] = {
                "whole_brain": whole_brain,
                "gm_cropped": gm_cropped,
            }
        return outputs

    def run_dataset(
        self,
        parcellation_scheme: str,
        participant_label: Union[str, list] = None,
        probseg_threshold: float = None,
        force: bool = False,
    ):
        """
        Register *parcellation_scheme* to all available (or requested) subjects' native space.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        participant_label : Union[str, list], optional
            Specific subject/s within the dataset to run, by default None
        probseg_threshold : float, optional
            Threshold for probability segmentation masking, by default None
        force : bool, optional
            Whether to remove existing products and generate new ones, by default False # noqa
        """
        native_parcellations = {}
        if participant_label:
            if isinstance(participant_label, str):
                participant_labels = [participant_label]
            elif isinstance(participant_label, list):
                participant_labels = participant_label
        else:
            participant_labels = list(sorted(self.subjects.keys()))
        for participant_label in tqdm(participant_labels):
            try:
                native_parcellations[participant_label] = self.run_single_subject(
                    parcellation_scheme,
                    participant_label,
                    probseg_threshold=probseg_threshold,
                    force=force,
                )
            except (FileNotFoundError, TraitError):
                continue
        return native_parcellations
