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
from pathlib import Path
from types import SimpleNamespace
from typing import List

# only site name like 'tv_fy4_22.14'
# ias_output_prefix: str = 'tv_fy4_22-14'
ias_output_prefix: str

# all settings related to reddyproc integration
eddyproc: SimpleNamespace

# site name with years like 'tv_fy4_22.14_2024' or 'tv_fy4_22.14_23-25'
# must be provided by REddyProc internal naming routines
# eddyproc.eddy_out_prefix: str = 'tv_fy4_22-14_2023'


arc_exclude_files: List[Path]
