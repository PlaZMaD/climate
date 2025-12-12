from src.data_io.biomet_import import import_biomets
from src.data_io.time_series_loader import merge_time_series_biomet, load_ftypes
from src.ff_logger import ff_logger
from src.config.config_types import InputFileType, ImportMode
from src.config.ff_config import ImportConfig


# TODO 1 in the ipynb, u_star is not yet renamed at the next line?
# cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength',
# ppfd_in_1_1_1 will be renamed to ppfd_1_1_1, 


def import_rename_fo_cols(df, time_col):
    # TODO 1 some renames in the main script are specific to eddypro/biomet files and should not be part of main script anymore?
    # if moved, check ias import-export handling stands (or solve with generalised col names preprocess check?)
    # TODO 2 extract FO specific renames
    # df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
    # check_csf_col_names(df)
    # df = import_rename_csf_cols(df, cfg_import.time_col)
    
    return df


def import_eddypro_and_biomet(cfg_import: ImportConfig):
    df = load_ftypes(cfg_import, InputFileType.EDDYPRO_FO, import_rename_fo_cols, None)
    
    if cfg_import.import_mode == ImportMode.EDDYPRO_FO_AND_BIOMET:
        df_bm = import_biomets(cfg_import)
        df = merge_time_series_biomet(df, df_bm, cfg_import.time_col, cfg_import.time_freq)
    
    return df