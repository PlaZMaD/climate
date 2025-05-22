import re
from pathlib import Path
from types import SimpleNamespace


def find_rep_file(path_mask):
    matches = list(Path().glob(path_mask))
    assert len(matches) == 1
    fname = matches[0].name
    site_id = re.match(r"(REddyProc_)(.*)(_\d)", str(matches[0].stem)).group(2)
    return SimpleNamespace(fname=fname, site_id=site_id)