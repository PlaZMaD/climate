""" 
Currently this is ff aware loader (knows about csf, biomet, fo formats).
Goal is to extract to format unaware utils in time_series_utils.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.config.config_types import InputFileType
from src.data_io.utils.table_loader import load_table_logged
from src.data_io.utils.time_series_utils import repair_time, detect_datetime_format, date_time_parser, datetime_parser
from src.ff_logger import ff_logger
from src.config.ff_config import ImportConfig, SeparateDateTimeFileConfig, MergedDateTimeFileConfig


PARSED_DATETIME_SUFFIX = '_STR'


def parse_datetime_col(df: pd.DataFrame, cfg_dt: MergedDateTimeFileConfig, tgt_time_col):   
    datetime_col_str = cfg_dt.datetime_col + PARSED_DATETIME_SUFFIX
    
    assert datetime_col_str not in df.columns    
    if tgt_time_col in df.columns:
        ff_logger.critical(f'Input data already contains column {tgt_time_col}, '
                           f'which will be overridden by data from {datetime_col_str}') 
    
    df.rename(columns={cfg_dt.datetime_col: datetime_col_str}, inplace=True)    
    df[tgt_time_col] = datetime_parser(df, datetime_col_str, cfg_dt.try_datetime_formats)    
    return df


def parse_date_time_cols(df: pd.DataFrame, cfg_dt: SeparateDateTimeFileConfig, tgt_time_col):   
    date_col_str = cfg_dt.date_col + PARSED_DATETIME_SUFFIX
    time_col_str = cfg_dt.time_col + PARSED_DATETIME_SUFFIX
    
    assert date_col_str not in df.columns
    assert time_col_str not in df.columns
    if tgt_time_col in df.columns:
        ff_logger.critical(f'Input data already contains column {tgt_time_col}, '
                           f'which will be overridden by data from {date_col_str} and {time_col_str}') 
    
    df.rename(columns={cfg_dt.time_col: time_col_str, cfg_dt.date_col: date_col_str}, inplace=True)
    df[tgt_time_col] = date_time_parser(df,
                                        time_col_str, cfg_dt.try_time_formats,
                                        date_col_str, cfg_dt.try_date_formats)    
    return df


def cleanup_df(df: pd.DataFrame, missing_data_codes):
    print(f'Replacing {missing_data_codes} to np.nan')
    # TODO 2 can this be done on file reading, not later?
    # TODO 2 replaces float NOT to np.nan, but to np.float(nan); changing this reqs changing script main routines
    df.replace(to_replace=missing_data_codes, value=np.nan, inplace=True)
    return df


def preload_time_series(fpath: Path, ftype: InputFileType, cfg_import: ImportConfig) -> pd.DataFrame:
    cfg_csf = cfg_import.csf
    cfg_bm = cfg_import.eddypro_biomet
    cfg_fo = cfg_import.eddypro_fo
    cfg_ias = cfg_import.ias    
    
    # TODO 1 test biomet and ias - final checks before all load happens here
    if ftype == InputFileType.CSF:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=1, skiprows=[2, 3])
        df = parse_datetime_col(df, cfg_csf, cfg_import.time_col)
        df = cleanup_df(df, cfg_csf.missing_data_codes)
    elif ftype == InputFileType.EDDYPRO_BIOMET:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=0, skiprows=[1])
        df = parse_datetime_col(df, cfg_bm, cfg_import.time_col)
        df = cleanup_df(df, cfg_bm.missing_data_codes)
    elif ftype == InputFileType.EDDYPRO_FO:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=0, skiprows=[0, 2])
        df = parse_date_time_cols(df, cfg_fo, cfg_import.time_col)
        df = cleanup_df(df, cfg_fo.missing_data_codes)
    elif ftype == InputFileType.IAS:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=0)
        df = parse_datetime_col(df, cfg_ias, cfg_import.time_col)
        df = cleanup_df(df, cfg_ias.missing_data_codes)        
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
