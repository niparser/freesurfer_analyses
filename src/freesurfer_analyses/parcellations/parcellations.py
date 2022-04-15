"""
Definition of the :class:`NativeParcellation` class.
"""
import logging
import subprocess
from pathlib import Path
from typing import Union

from tqdm import tqdm

from freesurfer_analyses.manager import FreesurferManager
from freesurfer_analyses.parcellations.utils import (
    PARCELLATION_CORTICAL_STATISTICS_CMD,
)
from freesurfer_analyses.parcellations.utils import (
    PARCELLATION_SUBCORTICAL_STATISTICS_CMD,
)

# from freesurfer_analyses.parcellations.utils import PARCALLATION_STATISTICS_CMD # noqa
from freesurfer_analyses.registrations.registrations import RegistrationManager


class ParcellationManager(FreesurferManager):
    #: Stats outputs
    DEFAULT_CORTICAL_STATS_DESTINATION = "stats"
    DEFAULT_CORTICAL_STATS_PATTERN = "{hemi}.{parcellation_scheme}.stats"

    DEFAULT_SUBCORTICAL_STATS_DESTINATION = "stats"
    DEFAULT_SUBCORTICAL_STATS_PATTERN = "subcortex.{parcellation_scheme}.stats"

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        super().__init__(base_dir, participant_labels)
        self.registration_manager = RegistrationManager(
            base_dir, participant_labels
        )

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
        source_file = Path(source_file)
        if hemi in self.HEMISPHERES_LABELS:
            output_file = (
                source_file
                / self.DEFAULT_CORTICAL_STATS_DESTINATION
                / self.DEFAULT_CORTICAL_STATS_PATTERN.format(
                    hemi=hemi, parcellation_scheme=parcellation_scheme
                )
            )
        elif hemi.lower() == "subcortex":
            output_file = (
                source_file
                / self.DEFAULT_SUBCORTICAL_STATS_DESTINATION
                / self.DEFAULT_SUBCORTICAL_STATS_PATTERN.format(
                    parcellation_scheme=parcellation_scheme
                )
            )

        return {"path": output_file, "exists": output_file.exists()}

    def configure_cortex_parcellation_command(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        hemi: str,
    ) -> str:
        """
        Configure the command for cortex parcellation of *parcellation_scheme*
        in *source_file*'s native space.

        Parameters
        ----------
        source_file : Union[str,Path]
            Path to a file used as source for Freesurfer's pipeline.
        parcellation_scheme : str
            Parcellation scheme to parcellate by
        hemi : str
            Hemisphere to be parcellated.

        Returns
        -------
        str
            A string representing the command to be executed.
        """
        source_file = Path(source_file)
        parcellation_lut = self.validate_parcellation(
            parcellation_scheme, "ctab"
        )
        return PARCELLATION_CORTICAL_STATISTICS_CMD.format(
            input_dir=source_file.parent,
            subject_id=source_file.name,
            hemi=hemi,
            parcellation_scheme=parcellation_scheme,
            lut=parcellation_lut,
        ).replace("\n", " ")

    def configure_subcortex_parcellation_command(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
    ) -> str:
        """
        Configure the command for subcortical parcellation of
        *parcellation_scheme* in *source_file*'s native space.

        Parameters
        ----------
        source_file : Union[str,Path]
            Path to a file used as source for Freesurfer's pipeline.
        parcellation_scheme : str
            Parcellation scheme to parcellate by
        hemi : str
            Hemisphere to be parcellated.

        Returns
        -------
        str
            A string representing the command to be executed.
        """
        source_file = Path(source_file)
        parcellation_lut = self.validate_parcellation(
            parcellation_scheme, "gcs_subcortex"
        )
        return PARCELLATION_SUBCORTICAL_STATISTICS_CMD.format(
            input_dir=source_file.parent,
            subject_id=source_file.name,
            parcellation_scheme=parcellation_scheme,
            gca=parcellation_lut,
        ).replace("\n", " ")

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
            self.set_subjects_dir(source_file.parent)
            if hemi in self.HEMISPHERES_LABELS:
                cmd = self.configure_cortex_parcellation_command(
                    source_file, parcellation_scheme, hemi
                )
            elif hemi.lower() == "subcortex":
                cmd = self.configure_subcortex_parcellation_command(
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
            f"""Parcellating {parcellation_scheme}
            in {source_file}'s native space."""
        )
        outputs = {}
        hemispheres = hemi or self.HEMISPHERES_LABELS + self.SUBCORTICAL_LABELS
        if isinstance(hemispheres, str):
            hemispheres = [hemispheres]
        for hemi in hemispheres:
            logging.info("Parcellating {}.".format(hemi))
            outputs[hemi] = self.run_single_hemisphere(
                source_file, parcellation_scheme, hemi, force
            )
        return outputs

    def run_single_subject(
        self,
        participant_label: str,
        parcellation_scheme: str,
        session: Union[str, list] = None,
        hemi: str = None,
        force: bool = False,
    ) -> dict:
        """
        Parcellate all available sessions and Freesurfer derivatives
        of *participant_label* with according to *parcellation_scheme*.

        Parameters
        ----------
        participant_label : str
            A string representing an existing key within *self.parcellation_manager.participants*. # noqa
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        session : Union[str, list], optional
            A string representing an existing key within *self.parcellation_manager.sessions*. # noqa
        hemi : str, optional
            Hemisphere to be parcellated, by default None
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of available or requested sessions,
            their corresponding source files,
            and paths native parcellated statistics as values.
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
                    hemi,
                    force,
                )
        return outputs

    def run_dataset(
        self,
        parcellation_scheme: str,
        participant_label: Union[str, list] = None,
        hemi: str = None,
        force: bool = False,
    ) -> dict:
        """
        Extract segmentation statistics according to *parcellation_scheme*,
        for all available Freesurfer derivatives under *self.subjects*,
        or just those specified by *participant_label*.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        participant_label : Union[str, list], optional
            A string representing an existing key within *self.parcellation_manager.participants*. # noqa
        hemi : str, optional
            Hemisphere to be parcellated, by default None
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of available or requested participants,
            their corresponding sessions and available Freesurfer-processed source files,
            and paths native parcellated statistics as values.
        """
        outputs = {}
        participant_labels = self.validate_participant_label(participant_label)
        for participant_label in tqdm(participant_labels):
            outputs[participant_label] = self.run_single_subject(
                participant_label,
                parcellation_scheme,
                hemi=hemi,
                force=force,
            )

        return outputs
