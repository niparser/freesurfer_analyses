"""
Definition of the :class:`StructureManager` class.
"""
import logging

# import warnings
from pathlib import Path
from typing import Union

import pandas as pd
from brain_parts.parcellation.parcellations import Parcellation
from tqdm import tqdm

from freesurfer_analyses.manager import FreesurferManager
from freesurfer_analyses.parcellations.transformations import (
    TransformationManager,
)
from freesurfer_analyses.structure.utils import read_stats_file


class StructureManager(FreesurferManager):
    #: Outputs
    DEFAULT_DESTINATION = "stats"
    DEFAULT_OUTPUT_PATTERN = "{parcellation_scheme}.pickle"

    #: Measures
    CORTICAL_MEASURES = [
        "number_of_vertices",
        "surface_area_mm^2",
        "gray_matter_volume_mm^3",
        "average_thickness_mm",
        "thickness_stddev_mm",
        "integrated_rectified_mean_curvature_mm^-1",
        "integrated_rectified_gaussian_curvature_mm^-2",
        "folding_index",
        "intrinsic_curvature_index",
    ]

    SUBCORTICAL_MEASURES = ["volume", "std", "mean"]

    def __init__(
        self,
        base_dir: Path,
        participant_labels: Union[str, list] = None,
    ) -> None:
        super().__init__(base_dir, participant_labels)
        self.transformation_manager = TransformationManager(
            base_dir, participant_labels
        )
        self.parcellation_manager = Parcellation()

    def generate_rows(
        self,
        source_file: Union[str, Path],
    ) -> pd.MultiIndex:
        """
        Generate target DataFrame's multiindex for participant's rows.

        Parameters
        ----------
        source_file : Union[str, Path]
            Path to a file used as source for Freesurfer's pipeline.

        Returns
        -------
        pd.MultiIndex
            A MultiIndex comprised of participant's label
            and its corresponding sessions.
        """
        source_file = Path(source_file)
        participant_label, session, _ = self.parse_source_file(source_file)
        metrics = set(self.CORTICAL_MEASURES)
        return pd.MultiIndex.from_product(
            [[participant_label], [session], [source_file.name], metrics]
        )

    def build_output_dictionary(
        self,
        source_file: str,
        parcellation_scheme: str,
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

        output_file = (
            source_file
            / self.DEFAULT_DESTINATION
            / self.DEFAULT_OUTPUT_PATTERN.format(
                parcellation_scheme=parcellation_scheme,
            )
        )
        return {"path": output_file, "exists": output_file.exists()}

    def query_measures(self, hemi: str) -> list:
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
        if hemi.lower() in self.HEMISPHERES_LABELS:
            measures = self.CORTICAL_MEASURES
        elif hemi.lower() == "subcortex":
            measures = self.SUBCORTICAL_MEASURES
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

    def run_single_source(
        self,
        source_file: Union[Path, str],
        parcellation_scheme: str,
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
        out_file = (
            source_file
            / self.DEFAULT_DESTINATION
            / self.DEFAULT_OUTPUT_PATTERN.format(
                parcellation_scheme=parcellation_scheme
            )
        )
        if out_file.exists():
            return pd.read_pickle(out_file)
        parcellation_data = self.parcellation_manager.parcellations.get(
            parcellation_scheme
        )
        participant_label, session, source_name = self.parse_source_file(
            source_file
        )
        data = pd.DataFrame(
            index=self.generate_rows(source_file),
            columns=parcellation_data.get("parcels")["Label"].values,
        )
        stats_files = (
            self.transformation_manager.parcellation_manager.run_single_source(
                source_file, parcellation_scheme, force=force
            )
        )
        # return data
        for hemi in self.HEMISPHERES_LABELS:
            logging.info("Re-structuring {}.".format(hemi))
            hemi_data = read_stats_file(
                stats_files.get(hemi).get("path"),
                parcellation_data.get("parcels"),
            )
            data.loc[
                (participant_label, session, source_name, hemi_data.index),
                hemi_data.columns,
            ] = hemi_data.loc[hemi_data.index, hemi_data.columns].values
        data.to_pickle(out_file)
        return data

    def run_single_subject(
        self,
        participant_label: str,
        parcellation_scheme: str,
        session: Union[str, list] = None,
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
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        dict
            A dictionary with keys of available or requested sessions,
            their corresponding source files,
            and paths native parcellated statistics as values.
        """

        sessions = self.validate_session(participant_label, session)
        source_files = []
        data = pd.DataFrame()
        for session in sessions:
            source_files += self.subjects.get(participant_label).get(session)
        for source_file in source_files:
            data = pd.concat(
                [
                    data,
                    self.run_single_source(
                        source_file, parcellation_scheme, force
                    ),
                ]
            )
        return data

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
        data = pd.DataFrame()
        participant_labels = self.validate_participant_label(participant_label)
        for participant_label in tqdm(participant_labels):
            data = pd.concat(
                [
                    data,
                    self.run_single_subject(
                        participant_label, parcellation_scheme, force=force
                    ),
                ]
            )

        return data
