""" 
Currently this is ff aware loader (knows about csf, biomet, fo formats).
Goal is to extract to format unaware utils in time_series_utils.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.config.config_types import InputFileType
from src.data_io.utils.table_loader import load_table_logged
from src.data_io.utils.time_series_utils import repair_time, detect_datetime_format
from src.ff_logger import ff_logger
from src.config.ff_config import FFConfig


def preprocess_time_csf(df: pd.DataFrame, src_time_col, try_fmts, tgt_time_col):
    """ Only init time column, no checks or repairs """
    fmt = detect_datetime_format(df[src_time_col], try_fmts)
    df[tgt_time_col] = pd.to_datetime(df[src_time_col], format=fmt)
    
    df.rename(columns={src_time_col: src_time_col + '_STR'}, inplace=True)
    return df


def preprocess_time_biomet(df: pd.DataFrame, ftype, tgt_time_col):
    """ Only init time column, no checks or repairs """
    return df


def cleanup_df(df: pd.DataFrame, missing_data_codes):
    print(f'Replacing {missing_data_codes} to np.nan')
    # TODO 2 can this be done on file reading, not later?
    # TODO 2 replaces float NOT to np.nan, but to np.float(nan); changing this reqs changing script main routines
    df.replace(to_replace=missing_data_codes, value=np.nan, inplace=True)
    return df


def preload_time_series(fpath: Path, ftype: InputFileType, config: FFConfig) -> pd.DataFrame:
    # TODO 3 # if 'debug' in d_config.keys()
    if ftype == InputFileType.CSF:
        df = load_table_logged(fpath, header_row=1, skiprows=[2, 3])
        df = preprocess_time_csf(df, config.data_import.csf.datetime_col, config.data_import.csf.try_datetime_formats, config.data_import.time_col)
        df = cleanup_df(df, config.data_import.csf.missing_data_codes)
    elif ftype == InputFileType.EDDYPRO_BIOMET:
        # Not switched to use this yet
        df = load_table_logged(fpath, header_row=1)
        df = preprocess_time_biomet(df, ftype, config.data_import.time_col)
        df = cleanup_df(df, config.biomet.missing_data_codes)
    else:
        raise Exception('Unexpected file type')
    
    # TODO 1 abstract ts repair
    # return prepare_time_series_df(df)
    return df


def merge_time_series_biomet(df_orig: pd.DataFrame, df_biomet: pd.DataFrame, time_col: str) -> [pd.DataFrame, bool]:
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null """
    
    df = df_orig.copy()
    same_cols = {col for col in df.columns if col.lower() in df_biomet.columns.str.lower()}
    same_cols = same_cols - {time_col}
    if len(same_cols) > 0:
        ff_logger.warning(f'Duplicate columns {same_cols} on merge with meteo data, using columns from biomet \n')
        df = df.drop(list(same_cols), axis=1)

    df = df.join(df_biomet, how='outer', rsuffix='_meteo')
    df[time_col] = df.index
    df = repair_time(df, time_col, fill_gaps=True)
    
    if df[df_biomet.columns[-1]].isna().sum() == len(df.index):
        print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
        return df, False

    return df, True

