import re

import numpy as np
import pandas as pd

from src.helpers.pd_helpers import df_ensure_cols_case
from src.ff_logger import ff_log
from src.data_io.csf_cols import COLS_CSF_IMPORT_MAP, \
    COLS_CSF_KNOWN, COLS_CSF_UNUSED_NORENAME_IMPORT, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES
from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.table_loader import load_table_logged
from src.data_io.time_series_utils import df_init_time_draft
from src.ffconfig import FFConfig


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
    if len(config.input_files) != 1:
        raise NotImplementedError(
            'Multiple csf files detected. Multiple run or combining multiple files is not supported yet.')
    fpath = list(config.input_files.keys())[0]
    df = load_table_logged(fpath, header_row=1, skiprows=[2, 3])
    
    df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
    check_csf_col_names(df)
    
    df.rename(columns={'TIMESTAMP': 'TIMESTAMP_STR'}, inplace=True)
    time_col = config.time_col
    df[time_col] = pd.to_datetime(df['TIMESTAMP_STR'], format='%Y-%m-%d %H:%M:%S')
    df = df_init_time_draft(df, time_col)
    
    print('Диапазон времени csf (START): ', df.index[[0, -1]])
    ff_log.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    
    print('Replacing -9999 to np.nan')
    df.replace(-9999, np.nan, inplace=True)
    
    df, biomet_cols_index = import_rename_csf_cols(df, time_col)
    
    has_meteo = True
    return df, time_col, biomet_cols_index, df.index.freq, has_meteo
