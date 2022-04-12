"""
Definition of the :class:`NativeParcellation` class.
"""
import os

# import warnings
from pathlib import Path
from typing import Callable
from typing import Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from freesurfer_analyses.manager import FreesurferManager
from freesurfer_analyses.parcellations.utils import (
    PARCELLATION_CORTICAL_STATISTICS_CMD,
)
from freesurfer_analyses.parcellations.utils import (
    PARCELLATION_SUBCORTICAL_STATISTICS_CMD,
)

# from freesurfer_analyses.parcellations.utils import PARCALLATION_STATISTICS_CMD # noqa
from freesurfer_analyses.registrations.registrations import NativeRegistration


class NativeParcellation(FreesurferManager):
    #: Stats outputs
    DEFAULT_CORTICAL_STATS_DESTINATION = "stats"
    DEFAULT_CORTICAL_STATS_PATTERN = "{hemi}.{parcellation_scheme}.stats"

    DEFAULT_SUBCORTICAL_STATS_DESTINATION = "stats"
    DEFAULT_SUBCORTICAL_STATS_PATTERN = "{parcellation_scheme}_subcortex.stats"

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
        )

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
        )

    def parcellate_single_tensor(
        self,
        parcellation_scheme: str,
        tensor_type: str,
        participant_label: str,
        parcellation_type: str = "whole_brain",
        session: Union[str, list] = None,
        measure: Callable = np.nanmean,
        force: bool = False,
    ) -> pd.DataFrame:
        """
        Parcellate tensor-derived metrics

        Parameters
        ----------
        parcellation_scheme : str
            Parcellation scheme to parcellate by
        tensor_type : str
            Tensor reconstruction method
        participant_label : str
            Specific participant's label
        parcellation_type : str, optional
            Either "gm_cropped" or "whole_brain", by default "gm_cropped"
        session : Union[str, list], optional
            Specific session's label, by default None
        measure : Callable, optional
            Measure for parcellation, by default np.nanmean
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        pd.DataFrame
            A DataFrame with (participant_label,session,tensor_type,metrics)
            as index and (parcellation_scheme,label) as columns
        """
        sessions = self.validate_session(participant_label, session)
        tensors = self.tensor_estimation.run_single_subject(
            participant_label, session, tensor_type
        )
        parcellation_images = self.registration_manager.run_single_subject(
            parcellation_scheme,
            participant_label,
            participant_label,
            session,
            force=force,
        )
        subject_rows = self.generate_rows(
            participant_label, sessions, tensor_type
        )
        subject_data = pd.DataFrame(index=subject_rows)
        for session in sessions:
            rows = self.generate_rows(participant_label, session, tensor_type)
            data = pd.DataFrame(index=rows)
            parcellation = parcellation_images.get(session).get(
                parcellation_type
            )
            output_file = self.build_output_name(
                parcellation_scheme,
                parcellation_type,
                tensor_type,
                parcellation,
                measure,
            )
            if output_file.exists() and not force:
                data = pd.read_pickle(output_file)
                subject_data = pd.concat([subject_data, data])
            for metric, metric_image in (
                tensors.get(session).get(tensor_type)[0].items()
            ):
                key = metric.split("_")[-1]

                tmp_data = self.parcellation_manager.parcellate_image(
                    parcellation_scheme,
                    parcellation,
                    metric_image,
                    key,
                    measure=measure,
                )
                data.loc[
                    (participant_label, session, key),
                    tmp_data.index,
                ] = tmp_data.loc[tmp_data.index]
            data.to_pickle(output_file)
            subject_data = pd.concat([subject_data, data])
        return subject_data

    def parcellate_single_subject(
        self,
        parcellation_scheme: str,
        participant_label: str,
        parcellation_type: str = "whole_brain",
        session: Union[str, list] = None,
        measure: Callable = np.nanmean,
        force: bool = False,
    ) -> pd.DataFrame:
        """
        Perform all parcellation available for a single subject

        Parameters
        ----------
        parcellation_scheme : str
            Parcellation scheme to parcellate by
        participant_label : str
            A single participant's label
        parcellation_type : str, optional
            Either "whole_brain" or "gm_cropped", by default "whole_brain"
        session : Union[str, list], optional
            A specific session's label, by default None
        measure : Callable, optional
            Measure to parcellate by, by default np.nanmean
        force : bool, optional
            Whether to re-write existing files, by default False

        Returns
        -------
        pd.DataFrame
            All subject's availble parcellated data
        """
        data = pd.DataFrame()
        for tensor_type in self.tensor_estimation.TENSOR_TYPES:
            # try:
            tensor_data = self.parcellate_single_tensor(
                parcellation_scheme,
                tensor_type,
                participant_label,
                parcellation_type,
                session,
                measure,
                force,
            )
            tensor_data = pd.concat([tensor_data], keys=[tensor_type])
            data = pd.concat([data, tensor_data])
        return data

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
