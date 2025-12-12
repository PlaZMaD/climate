import re

import numpy as np
import pandas as pd

from src.config.config_types import InputFileType, ImportMode
from src.data_io.biomet_import import import_biomets
from src.data_io.time_series_loader import merge_time_series_biomet, load_ftypes
from src.config.ff_config import ImportConfig
from src.helpers.pd_helpers import df_ensure_cols_case
from src.ff_logger import ff_logger
from src.data_io.csf_cols import COLS_CSF_IMPORT_MAP, \
    COLS_CSF_KNOWN, COLS_CSF_UNUSED_NORENAME_IMPORT, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES


# DONE repair time must be abstracted
# DONE finish transfer to abstract loader


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


def import_rename_csf_cols(df: pd.DataFrame, time_col):
    df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
    check_csf_col_names(df)
    df.rename(columns=COLS_CSF_IMPORT_MAP, inplace=True)
    return df


def import_csf_and_biomet(cfg_import: ImportConfig):
    df = load_ftypes(cfg_import, InputFileType.CSF, import_rename_csf_cols, None)
    
    if cfg_import.import_mode == ImportMode.CSF_AND_BIOMET :
        df_bm = import_biomets(cfg_import)
        df = merge_time_series_biomet(df, df_bm, cfg_import.time_col, cfg_import.time_freq)
            
    # (csf specific) repair postprocessing
    if cfg_import.csf.empty_co2_strg and 'co2_strg' not in df.columns:
        df['co2_strg'] = np.nan
        ff_logger.info('co2_strg not found, adding empty column.')

    return df


