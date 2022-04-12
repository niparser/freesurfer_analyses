"""
Definition of the :class:`NativeRegistration` class.
"""
import logging
import subprocess
from pathlib import Path
from typing import Tuple
from typing import Union

from tqdm import tqdm

from freesurfer_analyses.manager import FreesurferManager
from freesurfer_analyses.registrations.utils import CORTEX_MAPPING_CMD
from freesurfer_analyses.registrations.utils import SUBCORTEX_MAPPING_CMD


class NativeRegistration(FreesurferManager):
    #: Outputs
    DEFAULT_CORTICAL_OUTPUT_DESTINATION = "label"
    DEFAULT_CORTICAL_OUTPUT_PATTERN = "{hemi}.{parcellation_scheme}.annot"

    DEFAULT_SUBCORTICAL_OUTPUT_DESTINATION = "mri"
    DEFAULT_SUBCORTICAL_OUTPUT_PATTERN = "{parcellation_scheme}_subcortex.mgz"

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        super().__init__(base_dir, participant_labels)

    def get_participant_label_and_session(
        self, source_file: str
    ) -> Tuple[str, str]:
        """
        Get participant label and session from *source_file*.

        Parameters
        ----------
        source_file : str
            Path to a file.

        Returns
        -------
        Tuple[str, str]
            A tuple of participant label and session.
        """
        participant_label, session = Path(source_file).name.split("_")[:2]
        return participant_label, session

    def build_output_dictionary(
        self,
        source_file: str,
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
        if hemi in self.HEMISPHERES_LABELS:
            output_file = (
                source_file
                / self.DEFAULT_CORTICAL_OUTPUT_DESTINATION
                / self.DEFAULT_CORTICAL_OUTPUT_PATTERN.format(
                    hemi=hemi, parcellation_scheme=parcellation_scheme
                )
            )
        elif hemi.lower() == "subcortex":
            output_file = (
                source_file
                / self.DEFAULT_SUBCORTICAL_OUTPUT_DESTINATION
                / self.DEFAULT_SUBCORTICAL_OUTPUT_PATTERN.format(
                    parcellation_scheme=parcellation_scheme
                )
            )

        return {"path": output_file, "exists": output_file.exists()}

    def configure_cortex_mapping_command(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        hemi: str,
        seed: int = 42,
    ) -> str:
        """
        Configure the command for cortex mapping of *parcellation_scheme* to *source_file*'s native space.

        Parameters
        ----------
        source_file : Union[str, Path]
            Path to a file used as source for Freesurfer's pipeline.
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        hemi : str
            Hemisphere to be parcellated.
        """
        hemi_parcellation = self.parcellation_manager.parcellations.get(
            parcellation_scheme
        ).get("gcs")
        if not hemi_parcellation:
            raise ValueError(
                f"""No {parcellation_scheme} parcellation scheme found
                for {hemi} hemisphere."""
            )
        return CORTEX_MAPPING_CMD.format(
            input_dir=source_file.parent,
            subject_id=source_file.name,
            hemi=hemi,
            parcellation_gcs=hemi_parcellation.format(hemi=hemi),
            parcellation_scheme=parcellation_scheme,
            seed=seed,
        )

    def configure_subcortex_mapping_command(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
    ):
        """
        Configure the command for sub-cortical mapping of *parcellation_scheme* to *source_file*'s native space.

        Parameters
        ----------
        source_file : Union[str, Path]
            Path to a file used as source for Freesurfer's pipeline.
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        """
        subcortical_parcellation = self.parcellation_manager.parcellations.get(
            parcellation_scheme
        ).get("gcs_subcortex")
        if not subcortical_parcellation:
            raise ValueError(
                f"""No {parcellation_scheme} parcellation scheme found
                for the sub-cortex."""
            )
        return SUBCORTEX_MAPPING_CMD.format(
            input_dir=source_file.parent,
            subject_id=source_file.name,
            parcellation_gca=subcortical_parcellation,
            parcellation_scheme=parcellation_scheme,
        )

    def run_single_hemisphere(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        hemi: str,
        force: bool = False,
    ):
        """
        Register *parcellation_scheme* to *source_file*'s native space.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        source_file : Union[str,Path]
            Path to a file used as source for Freesurfer's pipeline.
        hemi : str
            Hemisphere to be parcellated.
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of "anat" and available or requested sessions,
            and corresponding natice parcellations as keys.
        """
        source_file = Path(source_file)
        outputs = self.build_output_dictionary(
            source_file, parcellation_scheme, hemi
        )
        if not outputs["exists"] or force:
            if hemi in self.HEMISPHERES_LABELS:
                cmd = self.configure_cortex_mapping_command(
                    source_file, parcellation_scheme, hemi
                )
            elif hemi.lower() == "subcortex":
                cmd = self.configure_subcortex_mapping_command(
                    source_file, parcellation_scheme
                )
            logging.info(f"Running command: {cmd}")
            out = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE
            ).stdout
            logging.info(out.read().decode())
        return outputs

    def run_single_source(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        hemi: Union[str, list] = None,
        force: str = False,
    ):
        """
        Register *parcellation_scheme* to *source_file*'s native space.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        source_file : Union[str,Path]
            Path to a file used as source for Freesurfer's pipeline.
        hemi : Union[str, list], optional
            Hemisphere to be parcellated, by default None

        Returns
        -------
        dict
            A dictionary with keys of "anat" and available or requested sessions,
            and corresponding natice parcellations as keys.
        """
        logging.info(
            f"""Registering {parcellation_scheme}
            to {source_file}'s native space."""
        )
        outputs = {}
        hemispheres = hemi or self.HEMISPHERES_LABELS + self.SUBCORTICAL_LABELS
        if isinstance(hemispheres, str):
            hemispheres = [hemispheres]
        for hemi in hemispheres:
            logging.info("Registering {} hemisphere.".format(hemi))
            outputs[hemi] = self.run_single_hemisphere(
                source_file, parcellation_scheme, hemi, force
            )
        return outputs

    def run_single_subject(
        self,
        parcellation_scheme: str,
        participant_label: str,
        session: Union[str, list] = None,
        hemi: str = None,
        force: bool = False,
    ) -> dict:
        """
        Register *parcellation_scheme* to *participant_label*'s native space.

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
        sessions = self.validate_session(participant_label, session)
        for session in sessions:
            outputs[session] = {}
            source_files = self.subjects.get(participant_label).get(session)
            for source_file in source_files:
                outputs[session][source_file.name] = self.run_single_source(
                    source_file,
                    parcellation_scheme,
                    hemi=hemi,
                    force=force,
                )
        return outputs

    def run_dataset(
        self,
        parcellation_scheme: str,
        participant_label: Union[str, list] = None,
        hemi: str = None,
        force: bool = False,
    ):
        native_parcellations = {}
        if participant_label:
            if isinstance(participant_label, str):
                participant_labels = [participant_label]
            elif isinstance(participant_label, list):
                participant_labels = participant_label
        else:
            participant_labels = list(sorted(self.subjects.keys()))
        for participant_label in tqdm(participant_labels):
            native_parcellations[participant_label] = self.run_single_subject(
                parcellation_scheme,
                participant_label,
                hemi=hemi,
                force=force,
            )
        return native_parcellations
