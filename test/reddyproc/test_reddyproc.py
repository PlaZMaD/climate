import shutil
from collections import namedtuple
from pathlib import Path
import os, sys
from types import SimpleNamespace

import pytest

import src.helpers.os_helpers  # noqa: F401
from reddyproc.helpers.io_helpers import find_rep_file
from src.helpers.io_helpers import ensure_empty_dir
import src.ipynb_globals as ig


@pytest.fixture
def use_r_from_python_env():
    env_folder = os.path.dirname(sys.executable)
    r_folder = str(Path(env_folder) / "Lib/R")
    assert Path(r_folder).exists()
    os.environ['R_HOME'] = r_folder

    # from rpy2 import robjects
    # robjects.r("ip = as.data.frame(installed.packages()[,c(1,3:4)]); ip = ip[is.na(ip$Priority),1:2,drop=FALSE];print(ip)")
    # robjects.r('remove.packages("REddyProc_1.3.3")')
    # robjects.r("install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = 'binary')")
    # robjects.r('remove.packages("REddyProc 1.3.2")')
    # robjects.r("install.packages('https://cran.r-project.org/bin/windows/contrib/4.2/REddyProc_1.3.3.zip', repos = NULL, type = 'binary')")



def test_process(use_r_from_python_env):
    # ig.ias_output_prefix = 'kr_tur'
    # ig.reddyproc_filename = 'REddyProc.txt'
    rep_input_file = find_rep_file('output/*REddyProc*.txt')
    ig.reddyproc_filename = rep_input_file.fname
    ig.ias_output_prefix = rep_input_file.ias_prefix

    import src.cells_mirror.cell_reddyproc_process  # noqa: F401
    # import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


def test_draw():
    ig.eddyproc = SimpleNamespace()
    ig.eddyproc.out_info = SimpleNamespace()
    ig.eddyproc.options = SimpleNamespace(is_to_apply_u_star_filtering=False)
    ig.eddyproc.out_info.fnames_prefix = 'tv_fy4_2023'
    ig.eddyproc.out_info.start_year = 2023
    ig.eddyproc.out_info.end_year = 2023
    # ensure_empty_dir('output/reddyproc')
    # shutil.copytree('test/reddyproc/test_process/output_sample', 'output/reddyproc', dirs_exist_ok=True)
    import src.cells_mirror.cell_reddyproc_draw  # noqa: F401

