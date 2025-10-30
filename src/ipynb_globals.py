"""
This file is for mocking missing globals during tests and local runs

expected use in the first cell:
from src.ipynb_globals import *
this allows both to run as ipynb and as mock

expected use in consequent cells:
import src.ipynb_globals as ig
all global ipynb vars should be re-declared under ig.* for clarity

do not declare variables here, only describe
"""
from src.config.ff_config import FFConfig, FFGlobals, RepConfig  # noqa: F401
from src.helpers.io_helpers import ensure_empty_dir  # noqa: F401
from src.reddyproc.preprocess_rg import prepare_rg  # noqa: F401
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess  # noqa: F401

# only site name like 'tv_fy4_22.14'
# ias_output_prefix: str = 'tv_fy4_22-14'
# config.site_name

# all settings related to reddyproc integration
# config.rep

# site name with years like 'tv_fy4_22.14_2024' or 'tv_fy4_22.14_23-25'
# must be provided by REddyProc internal naming routines
# eddyproc.eddy_out_prefix: str = 'tv_fy4_22-14_2023'

config: FFConfig
gl: FFGlobals
