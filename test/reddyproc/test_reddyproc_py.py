# to run test directly from cmd:
# py -m pytest -s test/reddyproc/test_reddyproc_py.py::test_process

from pathlib import Path
import logging  # noqa: F401
import pytest

import src.helpers.os_helpers  # noqa: F401
from src.config.ff_config import FFConfig, RepOutInfo, FFGlobals, RepConfig, InfoConfig
from src.helpers.env_helpers import setup_r_env
from test.reddyproc.helpers.io_helpers import find_rep_file


@pytest.fixture
def use_r_from_python_env():
    # logging.basicConfig(level=logging.DEBUG, force=True)
    # logging.getLogger().setLevel(logging.DEBUG)
    setup_r_env(Path('.'))
    
    # from rpy2 import robjects
    # robjects.r("ip = as.data.frame(installed.packages()[,c(1,3:4)]); ip = ip[is.na(ip$Priority),1:2,drop=FALSE];print(ip)")
    # robjects.r('remove.packages("REddyProc_1.3.3")')
    # robjects.r("install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = 'binary')")
    # robjects.r('remove.packages("REddyProc 1.3.2")')
    # robjects.r("install.packages('https://cran.r-project.org/bin/windows/contrib/4.2/REddyProc_1.3.3.zip', repos = NULL, type = 'binary')")


def test_process(use_r_from_python_env):
    rep_input_file = find_rep_file('output/*REddyProc*.txt')
    
    import test.ipynb_globals as ig
    ig.gl = FFGlobals(
        rep_level3_fpath=rep_input_file.fpath,
        out_dir=Path('output'),
        input_dir=Path('.'),
        repo_dir=Path('.'),
    )
    
    ig.config = FFConfig.model_construct(
        version='0.0.0',
        metadata=InfoConfig.model_construct(site_name=rep_input_file.site_id)
    )
    
    import test.cells_mirror.cell_reddyproc_process  # noqa: F401
    # import src.cells_mirror.cell_reddyproc_draw  # noqa: F401
    pass


def test_draw():
    import test.ipynb_globals as ig
    ig.config = FFConfig.model_construct(
        version='0.0.0',
        reddyproc=RepConfig(is_to_apply_u_star_filtering=True, output_dir='output/reddyproc'),
    )
    
    ig.gl = FFGlobals(
        out_dir=Path('output'),
        rep_out_info=RepOutInfo(fnames_prefix='tv_fy4_2023', start_year=2023, end_year=2023),
        input_dir=Path('.'),
        repo_dir=Path('.'),
    )
    # ensure_empty_dir('output/reddyproc')
    # shutil.copytree('test/reddyproc/test_process/output_sample', 'output/reddyproc', dirs_exist_ok=True)
    import test.cells_mirror.cell_reddyproc_draw  # noqa: F401
