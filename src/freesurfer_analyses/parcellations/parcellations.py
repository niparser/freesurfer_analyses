"""
Definition of the :class:`NativeParcellation` class.
"""
import logging
import os
import subprocess

# import warnings
from pathlib import Path
from typing import Callable
from typing import Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from freesurfer_analyses.manager import FreesurferManager
from freesurfer_analyses.parcellations.utils import CORTICAL_STATS_TO_TABLE_CMD
from freesurfer_analyses.parcellations.utils import (
    PARCELLATION_CORTICAL_STATISTICS_CMD,
)
from freesurfer_analyses.parcellations.utils import (
    PARCELLATION_SUBCORTICAL_STATISTICS_CMD,
)
from freesurfer_analyses.parcellations.utils import (
    SUBCORTICAL_STATS_TO_TABLE_CMD,
)

# from freesurfer_analyses.parcellations.utils import PARCALLATION_STATISTICS_CMD # noqa
from freesurfer_analyses.registrations.registrations import NativeRegistration


class NativeParcellation(FreesurferManager):
    #: Stats outputs
    DEFAULT_CORTICAL_STATS_DESTINATION = "stats"
    DEFAULT_CORTICAL_STATS_PATTERN = "{hemi}.{parcellation_scheme}.stats"

    DEFAULT_SUBCORTICAL_STATS_DESTINATION = "stats"
    DEFAULT_SUBCORTICAL_STATS_PATTERN = "{parcellation_scheme}_subcortex.stats"

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
        self.registration_manager = NativeRegistration(
            base_dir, participant_labels
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

    def generate_rows(
        self,
        participant_label: str,
        session: Union[str, list],
        tensor_type: str,
    ) -> pd.MultiIndex:
        """
        Generate target DataFrame's multiindex for participant's rows.

        Parameters
        ----------
        participant_label : str
            Specific participants' labels
        session : Union[str, list]
            Specific session(s)' labels

        Returns
        -------
        pd.MultiIndex
            A MultiIndex comprised of participant's label
            and its corresponding sessions.
        """
        sessions = self.validate_session(participant_label, session)
        metrics = self.tensor_estimation.METRICS.get(tensor_type)
        return pd.MultiIndex.from_product(
            [[participant_label], sessions, metrics]
        )

    def build_stats_output_dictionary(
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

    def build_table_output_dictionary(
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
        self.validate_measure(hemi, measure)
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
        elif hemi.lower() == "subcortex":
            output_file = (
                source_file
                / self.DEFAULT_SUBCORTICAL_TABLES_DESTINATION
                / self.DEFAULT_SUBCORTICAL_TABLES_PATTERN.format(
                    parcellation_scheme=parcellation_scheme, measure=measure
                )
            )

        return {"path": output_file, "exists": output_file.exists()}

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

    def parcellate_single_hemisphere(
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
        outputs = self.build_stats_output_dictionary(
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

    def parcellate_single_source(
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
            outputs[hemi] = self.parcellate_single_hemisphere(
                source_file, parcellation_scheme, hemi, force
            )
        return outputs

    def validate_measure(self, hemi: str, measure: str) -> None:
        """
        Validate the requested measure.

        Parameters
        ----------
        hemi : str
            Hemisphere to be parcellated.
        measure : str
            Measure to be parcellated.

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
        parcellation_outputs = self.parcellate_single_hemisphere(
            source_file, parcellation_scheme, hemi, force
        )
        outputs = self.build_table_output_dictionary(
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
        measures: Union[str, list] = None,
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
        measures : Union[str, list], optional
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
            if hemi in self.HEMISPHERES_LABELS:
                hemi_measures = measures or self.CORTICAL_MEASURES
            elif hemi.lower() == "subcortex":
                hemi_measures = measures or self.SUBCORTICAL_MEASURES
            for measure in hemi_measures:
                self.validate_measure(hemi, measure)
                outputs[hemi][measure] = self.run_single_hemisphere(
                    source_file, parcellation_scheme, hemi, measure, force
                )
        return outputs

    def parcellate_dataset(
        self,
        parcellation_scheme: str,
        parcellation_type: str = "whole_brain",
        measure: Callable = np.nanmean,
        force: bool = False,
    ) -> pd.DataFrame:
        """
        Iterates over dataset's available participants
        and reconstructs their tensor-derived metrics' data.

        Parameters
        ----------
        parcellation_scheme : str
            Parcellation scheme to parcellate by
        parcellation_type : str, optional
            Either "whole_brain" or "gm_cropped", by default "whole_brain"
        measure : Callable, optional
            Measure to parcellate by, by default np.nanmean
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        pd.DataFrame
            A dataframe describing all dataset's available tensor-derived data.
        """
        data = pd.DataFrame()
        for participant_label in tqdm(self.subjects):
            print(participant_label)
            data = pd.concat(
                [
                    data,
                    self.parcellate_single_subject(
                        parcellation_scheme,
                        participant_label,
                        parcellation_type,
                        measure=measure,
                        force=force,
                    ),
                ]
            )

        return data
