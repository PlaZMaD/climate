
from src.config.config_types import InputFileType
from src.config.ff_config import ImportConfig
from src.data_io.biomet_loader_todel import load_biomets_todel
from src.data_io.time_series_loader import load_ftypes
from src.data_io.utils.time_series_utils import ensure_dfs_same, TEMP_DEBUG_IMPORT
from src.ff_logger import ff_logger
from src.helpers.env_helpers import ENV

# TODO 1 support biomet ~ with separate time date cols


def import_rename_biomet_cols(df, time_col):
    # TODO 2 extract biomet specific renames
    # df = regex_fix_col_names(df, COLS_BIOMET_TO_SCRIPT_U_REGEX_RENAMES)
    # check_biomet_col_names(df)    
    return df


def import_biomets(cfg_import: ImportConfig):  
    df = load_ftypes(cfg_import, InputFileType.EDDYPRO_BIOMET, import_rename_biomet_cols, None)
    df2 = load_ftypes(cfg_import, InputFileType.EDDYPRO_BIOMET_2, import_rename_biomet_cols, None)
    
    if ENV.LOCAL and TEMP_DEBUG_IMPORT:
        ff_logger.disabled = True
        # TODO 1 cleanup, ensure freq
        bm_paths = [str(fpath) for fpath, ftype in cfg_import.input_files.items() if
                    ftype == InputFileType.EDDYPRO_BIOMET]
        df_check, _ = load_biomets_todel(bm_paths, cfg_import.time_col, cfg_import.time_freq, cfg_import.eddypro_biomet)
        
        df.rename(columns={'TIMESTAMP_1_STR': 'TIMESTAMP_1'}, inplace=True)
        ensure_dfs_same(df, df_check)
        ff_logger.disabled = False

    return df

