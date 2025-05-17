import re
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import List, Union
from zipfile import ZipFile


def find_rep_file(path_mask):
    matches = list(Path().glob(path_mask))
    assert len(matches) == 1
    fname = matches[0].name
    prefix = re.match(r"(REddyProc_)(.*)(_\d)", str(matches[0].stem)).group(2)
    return SimpleNamespace(fname=fname, ias_prefix=prefix)