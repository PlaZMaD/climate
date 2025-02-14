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

reddyproc_daily_sums_units = {'NEE_f': 'gC_m-2_day-1', 'NEE_uStar_f': 'gC_m-2_day-1',
                              'LE_f': 'Wm-2', 'H_f': 'Wm-2', 'Rg_f': 'Wm-2',
                              'Tair_f': 'degC', 'Tsoil_f': 'degC',
                              'rH_f': '%', 'VPD_f': 'hPa', 'Ustar_f': 'ms-1', 'CH4flux_f': 'mg_m-2_d-1'}