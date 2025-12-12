from src.data_io.biomet_cols import BIOMET_HEADER_DETECTION_COLS_LOWER
from src.data_io.biomet_import import import_biomets
from src.data_io.biomet_loader_todel import load_biomets_todel
from src.data_io.time_series_loader import merge_time_series_biomet, preload_time_series
from src.data_io.utils.time_series_utils import repair_time, merge_time_series
from src.ff_logger import ff_logger
from src.config.config_types import InputFileType
from src.config.ff_config import ImportConfig


# TODO 1 in the ipynb, u_star is not yet renamed at the next line?
# cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength',
# ppfd_in_1_1_1 will be renamed to ppfd_1_1_1, 


# TODO 1 some renames in the main script are specific to eddypro/biomet files and should not be part of main script anymore?
# if moved, check ias import-export handling stands (or solve with generalised col names preprocess check?)


def import_eddypro_and_biomet(cfg_import: ImportConfig):
    # TODO 1 finish transfer to abstract loader
    
    dfs_fo = {fpath.name: preload_time_series(fpath, ftype, cfg_import)
              for fpath, ftype in cfg_import.input_files.items() if ftype == InputFileType.EDDYPRO_FO}
    
    for fpath, df in dfs_fo.items():
        # TODO 2 extract FO specific renames
        # df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
        # check_csf_col_names(df)
        # df = import_rename_csf_cols(df, cfg_import.time_col)
        df = repair_time(df, cfg_import.time_col, cfg_import.time_freq, fill_gaps=False)
        dfs_fo[fpath] = df
    
    if len(dfs_fo) > 1:
        ff_logger.info('Merging data from files...')
    df_fo = merge_time_series(dfs_fo, cfg_import.time_col, no_duplicate_cols=False)
    if cfg_import.eddypro_fo.repair_time:
        df_fo = repair_time(df_fo, cfg_import.time_col, cfg_import.time_freq, fill_gaps=True)
    
    print('Диапазон времени FullOutput (START): ', df_fo.index[[0, -1]])
    ff_logger.info('Time range: ' + ' - '.join(df_fo.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    data_freq = df_fo.index.freq
    ff_logger.info('Колонки в FullOutput \n'
                   f'{df_fo.columns.values}')

    # TODO 2 final cleanup    
    # bm_paths = [str(fpath) for fpath, ftype in cfg_import.input_files.items() if
    #             ftype == InputFileType.EDDYPRO_BIOMET]
    # df_bm, has_meteo = load_biomets_todel(bm_paths, cfg_import.time_col, data_freq, cfg_import.eddypro_biomet)
    
    df_bm, has_meteo = import_biomets(cfg_import)
    if has_meteo:
        df, has_meteo = merge_time_series_biomet(df_fo, df_bm, cfg_import.time_col, cfg_import.time_freq)
    else:
        df = df_fo
        
    biomet_columns = [col for col in df.columns.str.lower() if col in BIOMET_HEADER_DETECTION_COLS_LOWER]
    has_meteo = len(biomet_columns) > 0
    
    # TODO 2 after merge or after load?
    if df[cfg_import.time_col].isna().sum() > 0:
        raise Exception("Cannot merge time columns during import. Check if years mismatch in different files")
    
    return df, cfg_import.time_col, biomet_columns, df.index.freq, has_meteo