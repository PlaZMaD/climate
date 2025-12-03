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


# TODO 1 config.data_in.input_files = ... will not reset on cell re-run, this damages re-run BADLY, fix
# TODO 1 import must recognise all the files or fail


# TODO 2 QOA are any of these supposed to be known as some format? 
# 'UNNAMED', 'RN_1_1_1', 'LOGGERTEMP', 'SHFSENS3', 'SHF_1_1_1', 'SWIN_1_1_1', 'LOGGERPWR', 'LWOUT_1_1_1', 'SHFSENS2', 'LWIN_1_1_1', 'VIN_1_1_1', 'SHFSENS1', 'SWOUT_1_1_1', 'PPFD_1_1_1'

def import_data(config: FFConfig):
    if config.debug and DEBUG_NROWS:
        config.data_import.debug_nrows = DEBUG_NROWS
    else:
        config.data_import.debug_nrows = None
    
    if config.data_import.import_mode in [ImportMode.EDDYPRO_FO, ImportMode.EDDYPRO_FO_AND_BIOMET]:
        res = load_eddypro_via_bgl_todel(config.data_import)
        
        # TODO 2 switch to abstract loader, ensure this check does not find errors, merge all loaders 
        if ENV.LOCAL:
            res_test_check = import_eddypro_and_biomet(config.data_import)
            res_test_check[0].rename(columns={'date_STR': 'date', 'time_STR': 'time'}, inplace=True)
            assert (res_test_check[0].columns == res[0].columns).all()
            
            check_same = res_test_check[0].compare(res[0])
            assert len(check_same) == 0    
    
    elif config.data_import.import_mode == ImportMode.IAS:
        res = import_iases(config.data_import)
    elif config.data_import.import_mode in [ImportMode.CSF, ImportMode.CSF_AND_BIOMET]:
        res = import_csf_and_biomet(config.data_import)
    else:
        raise Exception(f"Please double check value of config['mode'], {config['mode']} is probably typo")
    
    paths = format_dict(config.data_import.input_files, separator=': ')
    # DONE logs:  fix log
    ff_logger.info(f'Data imported from files: {paths} \n')
       
    return res
