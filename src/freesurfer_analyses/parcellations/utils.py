#: Parcellation statistics
PARCALLATION_STATISTICS_CMD = "mris_anatomical_stats -mgz -cortex {input_dir}/{subject_id}/label/lh.cortex.label -f {input_dir}/{subject_id}/stats/{hemi}.{parcellation_scheme}.stats -b -a {input_dir}/{subject_id}/label/{hemi}.{parcellation_scheme}.annot -c {lut} {subject_id} {hemi} white"
