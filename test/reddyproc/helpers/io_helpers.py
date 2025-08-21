import re
from pathlib import Path
from types import SimpleNamespace


def find_rep_file(path_mask):
    matches = list(Path().glob(path_mask))
    assert len(matches) == 1
    fpath = matches[0].name
    site_id_match = re.match(r"(REddyProc_)(.*)(_\d)", str(matches[0].stem))
    site_id = site_id_match.group(2) if site_id_match else 'unknown_site'
    return SimpleNamespace(fpath=fpath, site_id=site_id)
