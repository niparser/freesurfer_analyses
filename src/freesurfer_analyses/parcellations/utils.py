#: Parcellation statistics
PARCELLATION_CORTICAL_STATISTICS_CMD = """mris_anatomical_stats -mgz
-cortex {input_dir}/{subject_id}/label/lh.cortex.label
-f {input_dir}/{subject_id}/stats/{hemi}.{parcellation_scheme}.stats
-b -a {input_dir}/{subject_id}/label/{hemi}.{parcellation_scheme}.annot
-c {lut} {subject_id} {hemi} white"""

PARCELLATION_SUBCORTICAL_STATISTICS_CMD = """mri_segstats
--seg {input_dir}/{subject_id}/mri/{parcellation_scheme}_subcortex.mgz
--ctab-gca {gca} --excludeid 0
--sum {input_dir}/{subject_id}/stats/{parcellation_scheme}_subcortex.stats"""


#: Statistics to tables
CORTICAL_STATS_TO_TABLE_CMD = """aparcstats2table --subjects {subject_id}
--hemi {hemi} --parc {parcellation_scheme} --meas {measure}
--tablefile
{input_dir}/{subject_id}/stats/{hemi}_{measure}.{parcellation_scheme}.csv"""

SUBCORTICAL_STATS_TO_TABLE_CMD = """asegstats2table --inputs {subcortex_stats}
--meas {measure}
--tablefile
{input_dir}/{subject_id}/stats/{parcellation_scheme}_subcortex_{measure}.csv
--all-segs"""
