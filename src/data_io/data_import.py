import pandas as pd

from src.data_io.biomet_cols import BIOMET_USED_COLS_LOWER
from src.data_io.utils.time_series_utils import ensure_dfs_same, TEMP_DEBUG_IMPORT
from src.helpers.env_helpers import ENV
from src.helpers.py_collections import format_dict
from src.ff_logger import ff_logger
from src.data_io.csf_import import import_csf_and_biomet
from src.config.config_types import ImportMode, DEBUG_NROWS
from src.data_io.eddypro_import import import_eddypro_and_biomet
from src.data_io.eddypro_loader_todel import load_eddypro_via_bgl_todel
from src.data_io.ias_io import import_iases
from src.config.ff_config import FFConfig


# info on all imports:

# - full output, csf, ias = always 30 min
#   biomet - must be resampled, can not match at all

# TODO 1 test if only WARNING for unknowns
# - OA, V: ff_log.critical() for unknown cols, don't error
#   V: but in IAS, require by specification (due to check instrument)

# V: newly generated cols can be considered same as if imported for simplicity

# - mid-script biomet is replaced with "meteo params" or just col set OA & V:ok
# - OA: 2-4 levels = biomet, eddy (are dupes are possible which damage that way to define specification?)


# TODO 3 consider a table with all simple col ops instead of just untransparent import and export transforms
# problem: Excel vs VCS, use yaml table? csv? ...?
# handling unit/str conversions between import and export if name is same?
# ias check, ias export, ias import, initial script renames, renames during script run (required for export)
# E: unclear if table will help, people may damage it on edits (may be mega-config?)


# FluxFiler.py:
# O: check cell description for logic
# have_* flags:
# were not originally a way to store info which col is generated
# TODO 3 dictionary + optional transform lambda instead? useful to view cols flow,
# flags seems not nessesary or at some places var instead of const fits too, like p_rain = rain
# E: ok, requires prev section edits too, but low benefit

# TODO 1 0.9.4 problem: vpd imported from FO, but ignored?
# TODO 1 QOA ['vpd'] in FO (Pa?) have other units from ['vpd_1_1_1'] in biomet (kPa), but script L2-L4 specs is FO name with biomet units? ias hPa 6-140 ?
# E: 'VPD' could be bad ? should 'VPD_PI_1_1_1'  be imported from IAS? (no VPD)
# DONE OA, V: ias: import VPD_PI and convert (via generalised rename lambda function though)

# DONE logs:  fix log

# TODO 1 config.data_in.input_files = ... will not reset on cell re-run, this damages re-run BADLY, fix
# TODO 1 import must recognise all the files or fail


# TODO 2 QOA are any of these supposed to be known as some format? 
# 'UNNAMED', 'RN_1_1_1', 'LOGGERTEMP', 'SHFSENS3', 'SHF_1_1_1', 'SWIN_1_1_1', 'LOGGERPWR', 'LWOUT_1_1_1', 'SHFSENS2', 'LWIN_1_1_1', 'VIN_1_1_1', 'SHFSENS1', 'SWOUT_1_1_1', 'PPFD_1_1_1'

def import_data(config: FFConfig):
    if config.debug and DEBUG_NROWS:
        config.data_import.debug_nrows = DEBUG_NROWS
    else:
        config.data_import.debug_nrows = None
    
    config.data_import.time_freq = pd.Timedelta(minutes=30)
    
    if config.data_import.import_mode in [ImportMode.EDDYPRO_FO, ImportMode.EDDYPRO_FO_AND_BIOMET]:        
        df = import_eddypro_and_biomet(config.data_import) 
         
        if ENV.LOCAL and TEMP_DEBUG_IMPORT:
            ff_logger.disabled = True    
            df_check = load_eddypro_via_bgl_todel(config.data_import)[0]
            # df_check.rename(columns={'date': 'date_STR', 'time': 'time_STR'}, inplace=True)            
            ensure_dfs_same(df, df_check)
            ff_logger.disabled = False
    
    elif config.data_import.import_mode == ImportMode.IAS:
        df = import_iases(config.data_import)
    elif config.data_import.import_mode in [ImportMode.CSF, ImportMode.CSF_AND_BIOMET]:
        df = import_csf_and_biomet(config.data_import)
    else:
        raise Exception(f"Please double check value of config['mode'], {config['mode']} is probably typo")

    # print('Переменные после загрузки: \n', df.columns.to_list()) # duplicate

    # TODO 1 this ckeck is supposed to never be used, move to subroutine
    if df[config.data_import.time_col].isna().sum() > 0:
        raise Exception("Cannot merge time columns during import. Check if years mismatch in different files")

    # TODO 3 remove whole biomet_cols_index from the script E, OA: ok
    # TODO 1 test: if psn csf + biomet recognised correctly
    biomet_columns = [col for col in df.columns.str.lower() if col in BIOMET_USED_COLS_LOWER]
    has_meteo = len(biomet_columns) > 0
    
    paths = format_dict(config.data_import.input_files, separator=': ')
    ff_logger.info(f'Data imported from files: {paths}' '\n')
       
    return df, biomet_columns, has_meteo
