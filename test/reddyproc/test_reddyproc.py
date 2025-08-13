from types import SimpleNamespace

import pytest

import src.helpers.os_helpers  # noqa: F401
import src.ipynb_globals as ig
from src.helpers.env_helpers import setup_r_env
from test.reddyproc.helpers.io_helpers import find_rep_file


@pytest.fixture
def use_r_from_python_env():
    setup_r_env()

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
    ig.rep_input_fpath = rep_input_file.fpath
    ig.ias_output_prefix = rep_input_file.site_id

    import src.cells_mirror.cell_reddyproc_process  # noqa: F401
    # import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


def test_draw():
    ig.rep = SimpleNamespace()
    ig.rep.out_info = SimpleNamespace()
    ig.rep.options = SimpleNamespace(is_to_apply_u_star_filtering=True)
    ig.rep.out_info.fnames_prefix = 'tv_fy4_2023'
    ig.rep.out_info.start_year = 2023
    ig.rep.out_info.end_year = 2023
    # ensure_empty_dir('output/reddyproc')
    # shutil.copytree('test/reddyproc/test_process/output_sample', 'output/reddyproc', dirs_exist_ok=True)
    import src.cells_mirror.cell_reddyproc_draw  # noqa: F401
