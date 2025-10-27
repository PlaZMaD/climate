import re

import numpy as np
import pandas as pd

from src.data_io.data_import_modes import InputFileType, ImportMode
from src.data_io.biomet_loader import load_biomet
from src.data_io.utils.time_series_utils import datetime_parser
from src.data_io.time_series_loader import preload_time_series, repair_time, merge_time_series_biomet
from src.ff_config import FFConfig
from src.helpers.pd_helpers import df_ensure_cols_case
from src.ff_logger import ff_log
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
        ff_log.warning(msg)
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
    
    known_meteo_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
    biomet_cols_index = df.columns.intersection(known_meteo_cols)
    return df, biomet_cols_index


def regex_fix_col_names(df: pd.DataFrame, regex_map: dict[str, str]):
    rename_map = {}
    for expr, tgt_name in regex_map.items():
        for col in df.columns:
            match = re.match(expr, col)
            if not match:
                continue
            if col in rename_map:
                ff_log.warning(f'Column {col} matches regex rename patterns twice or more: {rename_map} and {expr}.')
            rename_map[col] = tgt_name
    
    df.rename(columns=rename_map, inplace=True)
    if len(rename_map) > 0:
        print(f'Columns were renamed by next regex match: {rename_map}')
    else:
        print('No regex rename matches found.')
    
    return df


def import_csf(config: FFConfig):
    # TODO 1 finish transfer to abstract loader
    # biomets = {k: v for k, v in config.input_files.items() if v == InputFileType.EDDYPRO_BIOMET}
    csfs = {k: v for k, v in config.input_files.items() if v == InputFileType.CSF}

    
    if len(csfs) != 1:
        raise NotImplementedError(
            'Multiple csf files detected. Multiple run or combining multiple files is not supported yet.')
    
    df_csf = [preload_time_series(fpath, ftype, config) for fpath, ftype in csfs.items()][0]

    if config.csf.repair_time:
        df_csf = repair_time(df_csf, config.time_col)
    print('Диапазон времени csf (START): ', df_csf.index[[0, -1]])
    ff_log.info('Time range for full_output: ' + ' - '.join(df_csf.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    data_freq = df_csf.index.freq
    
    c_bm = config.eddypro_biomet
    bm_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET]
    has_meteo = (config.import_mode == ImportMode.CSF_AND_BIOMET)
    if has_meteo:
        bg_bm_config = {
            'path': bm_paths,
            'debug': False,
            '-9999_to_nan': '-9999' in c_bm.missing_data_codes,
            'time': {
                'column_name': config.time_col,
                'converter': lambda x: datetime_parser(x, c_bm.datetime_col, c_bm.try_datetime_formats)
            },
            'repair_time': c_bm.repair_time,
        }
        df_biomet = load_biomet(bg_bm_config, data_freq)
    else:
        df_biomet = None
       
       
    df_csf = regex_fix_col_names(df_csf, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
    check_csf_col_names(df_csf)        
    df_csf, biomet_cols_index = import_rename_csf_cols(df_csf, config.time_col)
    
    
    # TODO 1 switch to abstract merge + abstract loader instead of csf and biomet specific 
    # df = merge_time_series(dfs, df_biomet)
    print("Колонки в CSF \n", df_csf.columns.to_list())        
    if has_meteo:
        print("Колонки в метео \n", df_biomet.columns.to_list())
        df, has_meteo = merge_time_series_biomet(df_csf, df_biomet, config.time_col)
    else:
        df = df_csf
    
    biomet_columns = []
    if has_meteo:
        biomet_columns = df_biomet.columns.str.lower()
        
    # TODO 2 after merge or after load?
    if df[config.time_col].isna().sum() > 0:
        raise Exception("Cannot merge time columns during import. Check if years mismatch in different files")
    
    return df, config.time_col, biomet_cols_index, df.index.freq, has_meteo


