import re

import numpy as np
import pandas as pd

from src.config.config_types import InputFileType, ImportMode
from src.data_io.biomet_loader import load_biomet
from src.data_io.eddypro_loader import load_biomets
from src.data_io.utils.time_series_utils import datetime_parser, merge_time_series
from src.data_io.time_series_loader import preload_time_series, repair_time, merge_time_series_biomet
from src.config.ff_config import FFConfig
from src.helpers.pd_helpers import df_ensure_cols_case
from src.ff_logger import ff_logger
from src.data_io.csf_cols import COLS_CSF_IMPORT_MAP, \
    COLS_CSF_KNOWN, COLS_CSF_UNUSED_NORENAME_IMPORT, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES
from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS

# DONE repair time must be abstracted


def check_csf_col_names(df: pd.DataFrame):
    print('Переменные в csf: \n', df.columns.to_list())
    
    known_csf_cols = COLS_CSF_KNOWN
    df = df_ensure_cols_case(df, known_csf_cols, ignore_missing=True)
    
    unknown_cols = df.columns.difference(known_csf_cols)
    if len(unknown_cols) > 0:
        msg = 'Неизвестные CSF переменные: \n', str(unknown_cols)
        ff_logger.warning(msg)
        # raise NotImplementedError(msg)
    
    unused_cols = df.columns.intersection(COLS_CSF_UNUSED_NORENAME_IMPORT)
    if len(unused_cols) > 0:
        # TODO 3 lang: localize properly, remove prints (ff_log.* goes to stdout too)
        # log - english only? OA: ok
        # TODO QOA 3 lang: print may be too only english for simplicity?
        print('Переменные, которые не используются в скрипте (присутствуют только в загрузке - сохранении): \n',
              unused_cols.to_list())
        # ff_log.warning('Unused vars (only save-loaded): \n' + str(unused_cols.to_list()))


def import_rename_csf_cols(df: pd.DataFrame, time_col):
    df.rename(columns=COLS_CSF_IMPORT_MAP, inplace=True)
    # print('Переменные после загрузки: \n', df.columns.to_list()) # duplicate
    
    return df


def regex_fix_col_names(df: pd.DataFrame, regex_map: dict[str, str]):
    rename_map = {}
    for expr, tgt_name in regex_map.items():
        for col in df.columns:
            match = re.match(expr, col)
            if not match:
                continue
            if col in rename_map:
                ff_logger.warning(f'Column {col} matches regex rename patterns twice or more: {rename_map} and {expr}.')
            rename_map[col] = tgt_name
    
    df.rename(columns=rename_map, inplace=True)
    if len(rename_map) > 0:
        print(f'Columns were renamed by next regex match: {rename_map}')
    else:
        print('No regex rename matches found.')
    
    return df


def import_csf(config: FFConfig):
    # TODO 1 finish transfer to abstract loader

    dfs_csf = {fpath.name: preload_time_series(fpath, ftype, config) 
               for fpath, ftype in config.input_files.items() if ftype == InputFileType.CSF}

    for fpath, df in dfs_csf.items():
        df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
        check_csf_col_names(df)        
        df = import_rename_csf_cols(df, config.time_col)
        df = repair_time(df, config.time_col, fill_gaps=False)
        dfs_csf[fpath] = df
       
    if len(dfs_csf) > 1:
        ff_logger.info('Merging data from files...')
    df_csf = merge_time_series(dfs_csf, config.time_col, no_duplicate_cols=False)
    if config.csf.repair_time:
        df_csf = repair_time(df_csf, config.time_col, fill_gaps=True)

    print('Диапазон времени csf (START): ', df_csf.index[[0, -1]])
    ff_logger.info('Time range: ' + ' - '.join(df_csf.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    data_freq = df_csf.index.freq
    ff_logger.info('Колонки в CSF \n'
                   f'{df_csf.columns.values}')
    # print("Колонки в CSF \n", df_csf.columns.to_list())
      
    bm_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET]
    df_bm, has_meteo = load_biomets(bm_paths, config.time_col, data_freq, config.eddypro_biomet)
                  
    if has_meteo:
        df, has_meteo = merge_time_series_biomet(df_csf, df_bm, config.time_col)
    else:
        df = df_csf
            
    # repair postprocessing
    if config.csf.empty_co2_strg and 'co2_strg' not in df.columns:
        df['co2_strg'] = np.nan
        ff_logger.info('co2_strg not found, adding empty column.')
    
    # csf can also contain meteo columns        
    # biomet_columns = df_bm.columns.str.lower()    
    known_meteo_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
    biomet_columns = df.columns.intersection(known_meteo_cols)
    
    # TODO 2 after merge or after load?
    if df[config.time_col].isna().sum() > 0:
        raise Exception("Cannot merge time columns during import. Check if years mismatch in different files")
    
    return df, config.time_col, biomet_columns, df.index.freq, has_meteo


