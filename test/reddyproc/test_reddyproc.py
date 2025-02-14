import shutil
from collections import namedtuple
from pathlib import Path
import os, sys
from types import SimpleNamespace

import pytest

import src.helpers.os_helpers  # noqa: F401
from src.helpers.io_helpers import ensure_empty_dir
import src.ipynb_globals as ig


@pytest.fixture
def use_r_from_python_env():
    env_folder = os.path.dirname(sys.executable)
    r_folder = str(Path(env_folder) / "Lib/R")
    assert Path(r_folder).exists()
    os.environ['R_HOME'] = r_folder


def test_process(use_r_from_python_env):
    ig.ias_output_prefix = 'tv_fy4'
    ig.reddyproc_filename = 'REddyProc_tv_fy4_2023.txt'

    import src.cells_mirror.cell_reddyproc_process  # noqa: F401
    # import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


def test_draw():
    ig.eddyproc = SimpleNamespace()
    ig.eddyproc.out_info = SimpleNamespace()
    ig.eddyproc.options = SimpleNamespace(is_to_apply_u_star_filtering=True)
    ig.eddyproc.out_info.fnames_prefix = 'tv_fy4_2023'
    ig.eddyproc.out_info.start_year = 2023
    ig.eddyproc.out_info.end_year = 2023
    # ensure_empty_dir('output/reddyproc')
    # shutil.copytree('test/reddyproc/test_process/output_sample', 'output/reddyproc', dirs_exist_ok=True)
    import src.cells_mirror.cell_reddyproc_draw  # noqa: F401

