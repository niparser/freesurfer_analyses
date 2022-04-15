"""
Definition of the :class:`NativeParcellation` class.
"""
import logging
import subprocess

# import warnings
from pathlib import Path
from typing import Union

import pandas as pd
from tqdm import tqdm

from freesurfer_analyses.manager import FreesurferManager

# from freesurfer_analyses.parcellations.utils import PARCALLATION_STATISTICS_CMD # noqa
from freesurfer_analyses.parcellations.parcellations import ParcellationManager
from freesurfer_analyses.parcellations.utils import CORTICAL_STATS_TO_TABLE_CMD
from freesurfer_analyses.parcellations.utils import (
    SUBCORTICAL_STATS_TO_TABLE_CMD,
)


class TransformationManager(FreesurferManager):
    #: Table outputs
    DEFAULT_CORTICAL_TABLES_DESTINATION = "stats"
    DEFAULT_CORTICAL_TABLES_PATTERN = (
        "{hemi}_{measure}.{parcellation_scheme}.csv"
    )

    DEFAULT_SUBCORTICAL_TABLES_DESTINATION = "stats"
    DEFAULT_SUBCORTICAL_TABLES_PATTERN = (
        "{parcellation_scheme}_subcortex_{measure}.csv"
    )
    #: Measures
    CORTICAL_MEASURES = [
        'area',
        'volume',
        'thickness',
        'thicknessstd',
        'thickness.T1',
        'meancurv',
        'gauscurv',
        'foldind',
        'curvind',
    ]

    SUBCORTICAL_MEASURES = ["volume", "std", "mean"]

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        super().__init__(base_dir, participant_labels)
        self.parcellation_manager = ParcellationManager(
            base_dir, participant_labels
        )

    def build_output_dictionary(
        self,
        source_file: str,
        parcellation_scheme: str,
        hemi: str,
        measure: str,
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
        self.check_measure(measure, hemi)
        source_file = Path(source_file)
        if hemi in self.HEMISPHERES_LABELS:
            output_file = (
                source_file
                / self.DEFAULT_CORTICAL_TABLES_DESTINATION
                / self.DEFAULT_CORTICAL_TABLES_PATTERN.format(
                    hemi=hemi,
                    parcellation_scheme=parcellation_scheme,
                    measure=measure,
                )
            )
        elif hemi.lower() in self.SUBCORTICAL_LABELS:
            output_file = (
                source_file
                / self.DEFAULT_SUBCORTICAL_TABLES_DESTINATION
                / self.DEFAULT_SUBCORTICAL_TABLES_PATTERN.format(
                    parcellation_scheme=parcellation_scheme, measure=measure
                )
            )

        return {"path": output_file, "exists": output_file.exists()}

    def configure_cortex_transformation_command(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        measure: str,
        hemi: str,
    ) -> str:
        """
        Configure the command for transformation of cortical parcellation
        (stored as .stats file) to a .csv table.

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
        return CORTICAL_STATS_TO_TABLE_CMD.format(
            input_dir=source_file.parent,
            subject_id=source_file.name,
            hemi=hemi,
            parcellation_scheme=parcellation_scheme,
            measure=measure,
        ).replace("\n", " ")

    def configure_subcortical_transformation_command(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        measure: str,
        stats_file: Union[str, Path],
    ) -> str:
        """
        Configure the command for transformation of cortical parcellation
        (stored as .stats file) to a .csv table.

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
        return SUBCORTICAL_STATS_TO_TABLE_CMD.format(
            subcortex_stats=stats_file,
            input_dir=source_file.parent,
            subject_id=source_file.name,
            parcellation_scheme=parcellation_scheme,
            measure=measure,
        ).replace("\n", " ")

    def validate_measure(self, hemi: str, measure: str = None) -> list:
        """
        Validate the requested measure.

        Parameters
        ----------
        hemi : str
            Hemisphere to be parcellated.
        measure : str
            Measure to be parcellated.

        Returns
        -------
        list
            A list of valid measures.
        """
        if isinstance(measure, str):
            measure = [measure]
        if hemi.lower() in self.HEMISPHERES_LABELS:
            measures = measure or self.CORTICAL_MEASURES
        elif hemi.lower() == "subcortex":
            measures = measure or self.SUBCORTICAL_MEASURES
        [self.check_measure(measure, hemi) for measure in measures]
        return measures

    def check_measure(self, measure: str, hemi: str) -> None:
        """
        Check if the requested measures are valid for the given hemisphere.

        Parameters
        ----------
        measures : str
            measure to be parcellated.
        hemi : str
            Hemisphere to be parcellated.

        Raises
        ------
        ValueError
            If *measure* is not a valid measure for *hemi*.
        """
        if (
            hemi in self.HEMISPHERES_LABELS
            and measure not in self.CORTICAL_MEASURES
        ):
            raise ValueError(
                "Cannot run cortical statistics on {}".format(measure)
            )
        if (
            hemi in self.SUBCORTICAL_LABELS
            and measure not in self.SUBCORTICAL_MEASURES
        ):
            raise ValueError(
                "Cannot run subcortical statistics on {}".format(measure)
            )

    def run_single_hemisphere(
        self,
        source_file: Union[str, Path],
        parcellation_scheme: str,
        hemi: str,
        measure: str,
        force: bool = False,
    ):
        """
        Parcellate *source_file*'s native space by *parcellation_scheme*,
        and transform the resulting .stats file into a .csv one.

        Parameters
        ----------
        source_file : Union[str, Path]
            Path to a file used as source for Freesurfer's pipeline.
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        hemi : str
            Hemisphere to be parcellated.
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        pd.DataFrame
            _description_
        """
        source_file = Path(source_file)
        parcellation_outputs = self.parcellation_manager.run_single_hemisphere(
            source_file, parcellation_scheme, hemi, force
        )
        outputs = self.build_output_dictionary(
            source_file, parcellation_scheme, hemi, measure
        )
        if not outputs["exists"] or force:
            self.set_subjects_dir(source_file.parent)
            if hemi in self.HEMISPHERES_LABELS:
                cmd = self.configure_cortex_transformation_command(
                    source_file, parcellation_scheme, measure, hemi
                )
            elif hemi.lower() == "subcortex":
                cmd = self.configure_subcortical_transformation_command(
                    source_file,
                    parcellation_scheme,
                    measure,
                    parcellation_outputs.get("path"),
                )
            logging.info(f"Running command: {cmd}")
            out = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE
            ).stdout
            logging.info(out.read().decode())
        return outputs

    def run_single_source(
        self,
        source_file: Union[Path, str],
        parcellation_scheme: str,
        hemi: Union[str, list] = None,
        measure: Union[str, list] = None,
        force: str = False,
    ) -> dict:
        """
        Parcellate *source_file*'s native space by *parcellation_scheme*,

        Parameters
        ----------
        source_file : Union[Path, str]
            Path to a file used as source for Freesurfer's pipeline.
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        hemi : Union[str, list], optional
            Hemisphere to be parcellated, by default None
        measure : Union[str, list], optional
            Measure to be parcellated, by default None
        force : str, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of hemispheres and available or requested measures,
        """
        logging.info(
            f"""Parcellating {parcellation_scheme}
            to {source_file}'s native space."""
        )
        outputs = {}
        hemispheres = hemi or self.HEMISPHERES_LABELS + self.SUBCORTICAL_LABELS
        if isinstance(hemispheres, str):
            hemispheres = [hemispheres]
        for hemi in hemispheres:
            outputs[hemi] = {}
            logging.info("Parcellating {}.".format(hemi))
            measures = self.validate_measure(hemi, measure)
            for parameter in measures:
                outputs[hemi][parameter] = self.run_single_hemisphere(
                    source_file, parcellation_scheme, hemi, parameter, force
                )
        return outputs

    def run_single_subject(
        self,
        participant_label: str,
        parcellation_scheme: str,
        session: Union[str, list] = None,
        hemi: str = None,
        measure: str = None,
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
        measure : str, optional
            Measure to be parcellated, by default None
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
                    measure,
                    force,
                )
        return outputs

    def run_dataset(
        self,
        parcellation_scheme: str,
        participant_label: Union[str, list] = None,
        hemi: Union[str, list] = None,
        measure: Union[str, list] = None,
        force: bool = False,
    ) -> pd.DataFrame:
        """
        Extract segmentation statistics according to *parcellation_scheme*,
        for all available Freesurfer derivatives under *self.subjects*,
        or just those specified by *participant_label*.
        Transforms these statistics into a pandas DataFrame.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellation_manager.parcellations*. # noqa
        participant_label : Union[str, list], optional
            A string or list of strings representing Freesurfer's derivatives, by default None. # noqa
        hemi : Union[str, list], optional
            Hemisphere to be parcellated, by default None
        measure : Union[str, list], optional
            Measure to be parcellated, by default None
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        pd.DataFrame
            # A pandas DataFrame with columns:
            # - participant_label
        """
        outputs = {}
        participant_labels = self.validate_participant_label(participant_label)
        for participant_label in tqdm(participant_labels):
            outputs[participant_label] = self.run_single_subject(
                participant_label,
                parcellation_scheme,
                hemi=hemi,
                measure=measure,
                force=force,
            )

        return outputs
