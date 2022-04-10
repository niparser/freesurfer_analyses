QUERIES = dict(
    mni2native={
        "from": "MNI152NLin2009cAsym",
        "to": "T1w",
        "mode": "image",
        "suffix": "xfm",
    },
    native2mni={
        "from": "T1w",
        "to": "MNI152NLin2009cAsym",
        "mode": "image",
        "suffix": "xfm",
    },
    anat_reference={
        "desc": "preproc",
        "suffix": "T1w",
        "datatype": "anat",
        "space": None,
        "extension": ".nii.gz",
    },
    dwi_reference={
        "desc": "preproc",
        "datatype": "dwi",
        "suffix": "dwi",
        "space": "T1w",
        "extension": ".nii.gz",
    },
    probseg={"suffix": "probseg"},
)

#: Naming
DEFAULT_PARCELLATION_NAMING = dict(space="T1w", suffix="dseg", desc="")

#: Types of transformations
TRANSFORMS = ["mni2native", "native2mni"]

#: Default probability segmentations' threshold
PROBSEG_THRESHOLD = 0.01
