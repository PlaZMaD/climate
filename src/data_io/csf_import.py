import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.data_import_modes import InputFileType, ImportMode
from src.data_io.eddypro_loader import datetime_converter, load_biomet
from src.data_io.time_series_loader import preload_time_series, repair_time
from src.ffconfig import FFConfig
from src.helpers.pd_helpers import df_ensure_cols_case
from src.ff_logger import ff_log
from src.data_io.csf_cols import COLS_CSF_IMPORT_MAP, \
    COLS_CSF_KNOWN, COLS_CSF_UNUSED_NORENAME_IMPORT, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES
from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.time_series_utils import df_init_time_draft


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
        print('Переменные, которые не используются в тетради (присутствуют только в загрузке - сохранении): \n',
              unused_cols.to_list())
        ff_log.warning('Unsupported by notebook csf vars (only save loaded): \n' + str(unused_cols.to_list()))


def import_rename_csf_cols(df: pd.DataFrame, time_col):
    df.rename(columns=COLS_CSF_IMPORT_MAP, inplace=True)
    print('Переменные после загрузки: \n', df.columns.to_list())
    
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
    
    df = [preload_time_series(fpath, ftype, config) for fpath, ftype in csfs.items()][0]

    # TODO 1 repair time must be abstracted
    df = df_init_time_draft(df, config.time_col)    
    print('Диапазон времени csf (START): ', df.index[[0, -1]])
    ff_log.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    data_freq = df.index.freq
    
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
                'converter': lambda x: datetime_converter(x, datetime_col=c_bm.datetime_col,
                                                          datetime_formats=c_bm.try_datetime_formats)
            },
            'repair_time': c_bm.repair_time,
        }
        biomet_df = load_biomet(bg_bm_config, data_freq)
    else:
        biomet_df = None
       
       
    df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
    check_csf_col_names(df)
        
    df, biomet_cols_index = import_rename_csf_cols(df, config.time_col)
    
    
    # TODO 1 imvore merge
    # df = merge_time_series(dfs, biomet_df)
    print("Колонки в FullOutput \n", df.columns.to_list())
    if has_meteo:
        print("Колонки в метео \n", biomet_df.columns.to_list())
    
    # merge into common DataFrame
    if has_meteo:
        df = df.join(biomet_df, how='outer', rsuffix='_meteo')
        df[config.time_col] = df.index
        df = repair_time(df, config.time_col)
        if df[biomet_df.columns[-1]].isna().sum() == len(df.index):
            print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
            has_meteo = False
    
    # reddyproc requires 3 months
    if config.debug:
        df = df[0: min(31 * 3 * 24 * 2, len(df))]
    
    biomet_columns = []
    if has_meteo:
        biomet_columns = biomet_df.columns.str.lower()
        
        
        
    
    return df, config.time_col, biomet_cols_index, df.index.freq, has_meteo
