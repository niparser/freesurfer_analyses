# Cortex mapping
CORTEX_MAPPING_CMD = "mris_ca_label -sdir {input_dir} -l {input_dir}/{subject_id}/label/{hemi}.cortex.label {subject_id} {hemi} {input_dir}/{subject_id}/surf/{hemi}.sphere.reg {parcellation_gcs} {input_dir}/{subject_id}/label/{hemi}.{parcellation_scheme}.annot"  # noqa

# Subcortex mapping
SUBCORTEX_MAPPING_CMD = "mri_ca_label {input_dir}/{subject_id}/mri/brain.mgz {input_dir}/{subject_id}/mri/transforms/talairach.m3z {parcellation_gca} {input_dir}/{subject_id}/mri/{parcellation_scheme}_subcortex.mgz"  # noqa
