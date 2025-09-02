import os
import re
import shutil
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest


'''

@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


@pytest.mark.usefixtures('tmp_path')
@pytest.fixture
def use_fixture_path(tmp_path: Path, src_path: Path):
    assert(src_path.exists())

    shutil.copytree(src_path, tmp_path, dirs_exist_ok=True)
    print('Path before test',  Path().resolve())
    with cwd(tmp_path):
        print('Path during test', Path().resolve())
        yield tmp_path
'''


def find_rep_file(path_mask):
    matches = list(Path().glob(path_mask))
    assert len(matches) == 1
    fpath = matches[0]
    site_id_match = re.match(r"(REddyProc_)(.*)(_\d)", str(matches[0].stem))
    site_id = site_id_match.group(2) if site_id_match else 'unknown_site'
    return SimpleNamespace(fpath=fpath, site_id=site_id)
