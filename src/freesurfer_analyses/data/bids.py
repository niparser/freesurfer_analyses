BIDS_ENTITIES = {
    "ceagent": {"pattern": "ce-([a-zA-Z0-9]+)"},
    "atlas": {"pattern": "atlas-([a-zA-Z0-9]+)"},
    "roi": {"pattern": "roi-([a-zA-Z0-9]+)"},
    "label": {"pattern": "label-([a-zA-Z0-9]+)"},
    "desc": {"pattern": "desc-([a-zA-Z0-9]+)"},
    "resolution": {"pattern": "res-([a-zA-Z0-9]+)"},
    "from": {"pattern": "(?:^|_)from-([a-zA-Z0-9]+).*xfm"},
    "to": {"pattern": "(?:^|_)to-([a-zA-Z0-9]+).*xfm"},
    "mode": {"pattern": "(?:^|_)mode-([a-zA-Z0-9]+).*xfm"},
    "hemi": {"pattern": "hemi-(L|R)"},
    "den": {"pattern": "den-([a-zA-Z0-9]+)"},
    "model": {"pattern": "model-([a-zA-Z0-9]+)"},
    "subset": {"pattern": "subset-([a-zA-Z0-9]+)"},
    "session": {"pattern": "ses-([a-zA-Z0-9]+)"},
}

THEBASE_FILTERS = {"anat": {"ceagent": "corrected"}}
# flake8: noqa: E501
