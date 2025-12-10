""" 
Currently this is ff aware loader (knows about csf, biomet, fo formats).
Format unaware utils and helpers are in time_series_utils.py
"""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pandas import Timedelta

from src.config.config_types import InputFileType
from src.data_io.utils.table_loader import load_table_logged
from src.data_io.utils.time_series_utils import repair_check_todel, date_time_parser, datetime_parser, \
    resample_time_series_df, merge_time_series
from src.ff_logger import ff_logger
from src.config.ff_config import ImportConfig, SeparateDateTimeFileConfig, MergedDateTimeFileConfig

PARSED_DATETIME_SUFFIX = '_STR'
MAX_BAD_TIMESTAMPS_PERCENT = 10
MAX_NON_HALF_HOUR_TIMESTAMPS_CROP = 1801


def parse_datetime_col(df: pd.DataFrame, cfg_dt: MergedDateTimeFileConfig, tgt_time_col, pd_to_datetime_errors_arg):
    datetime_col_str = cfg_dt.datetime_col + PARSED_DATETIME_SUFFIX
    
    assert datetime_col_str not in df.columns
    if tgt_time_col in df.columns:
        ff_logger.critical(f'Input data already contains column {tgt_time_col}, '
                           f'which will be overridden by data from {datetime_col_str}')
    
    df.rename(columns={cfg_dt.datetime_col: datetime_col_str}, inplace=True)
    df[tgt_time_col] = datetime_parser(df, datetime_col_str, cfg_dt.try_datetime_formats, pd_to_datetime_errors_arg)
    return df


def parse_date_time_cols(df: pd.DataFrame, cfg_dt: SeparateDateTimeFileConfig, tgt_time_col, pd_to_datetime_errors_arg):
    date_col_str = cfg_dt.date_col + PARSED_DATETIME_SUFFIX
    time_col_str = cfg_dt.time_col + PARSED_DATETIME_SUFFIX
    
    assert date_col_str not in df.columns
    assert time_col_str not in df.columns
    if tgt_time_col in df.columns:
        ff_logger.critical(f'Input data already contains column {tgt_time_col}, '
                           f'which will be overridden by data from {date_col_str} and {time_col_str}')
    
    df.rename(columns={cfg_dt.time_col: time_col_str, cfg_dt.date_col: date_col_str}, inplace=True)
    df[tgt_time_col] = date_time_parser(df, time_col_str, cfg_dt.try_time_formats, date_col_str,
                                        cfg_dt.try_date_formats, pd_to_datetime_errors_arg)
    return df


def cleanup_df(df: pd.DataFrame, missing_data_codes):
    print(f'Replacing {missing_data_codes} to np.nan')
    # TODO 2 can this be done on file reading, not later?
    # TODO 3 replaces float NOT to np.nan, but to np.float(nan)? possibly just different representations?
    df.replace(to_replace=missing_data_codes, value=np.nan, inplace=True)
    return df


def parse_timestamp_cols(df, cfg: SeparateDateTimeFileConfig | MergedDateTimeFileConfig, tgt_time_col):
    """ 
    Initial parse, ensures time exists, has correct type, ensures sort, drops duplicates
    Does not create an index yet, does not guarantee consistent frequency without empty gaps
    """
    
    # TODO 2 test/fix: half of column is one datetime format, another half is another?    
    if isinstance(cfg, MergedDateTimeFileConfig):
        df = parse_datetime_col(df, cfg, tgt_time_col, pd_to_datetime_errors_arg='coerce')
    elif isinstance(cfg, SeparateDateTimeFileConfig):
        df = parse_date_time_cols(df, cfg, tgt_time_col, pd_to_datetime_errors_arg='coerce')
    else:
        assert False
    
    original_size = df.size
    
    def mask_info(mask):
        bad_count = mask.sum()
        bad_percent = 100 * bad_count / mask.size
        return f'{bad_count} ({bad_percent:.1f}%) ' 
    
    # TODO 2 test: bad or missing timestamps
    bad_mask = df[tgt_time_col].isna()
    if bad_mask.any():
        ff_logger.warning(f'{mask_info(bad_mask)} of timestamps are bad and will be removed: \n'
                          f'{df[tgt_time_col][bad_mask]} \n')
        df = df[~bad_mask]
    
    # TODO 3 add test case: 3 same timestamps
    dupe_mask = df[tgt_time_col].duplicated(keep='first')
    if dupe_mask.any():
        ff_logger.warning(f'{mask_info(dupe_mask)} of timestamps are duplicated and will be removed: \n'
                          f'{df[tgt_time_col][dupe_mask]} \n')
        df = df[~dupe_mask]
    
    if 100 * (original_size - df.size) / df.size > MAX_BAD_TIMESTAMPS_PERCENT:
        raise Exception('Too much bad timestamps, file requires manual review.')
    
    # df.loc[5:6, 'datetime'] = df.loc[4:5, 'datetime'][::-1].values
    # TODO 2 test: wrong order
    deltas = df[tgt_time_col] - df[tgt_time_col].shift(1)
    reversed_mask = deltas.values < 0
    if reversed_mask.any():
        ff_logger.warning(f'{mask_info(reversed_mask)} of timestamps are reversed. Data order will be rearranged: \n'
                          f'{df[tgt_time_col][reversed_mask]} \n')
        df = df.sort_values(tgt_time_col).reset_index()
        
    return df


def get_ftype_cfg(ftype: InputFileType, cfg_import: ImportConfig) -> SeparateDateTimeFileConfig | MergedDateTimeFileConfig:
    # TODO 1 header_row=1, skiprows=[2, 3]
    cfg_cases = {
        InputFileType.EDDYPRO_FO: cfg_import.eddypro_fo,
        InputFileType.EDDYPRO_BIOMET: cfg_import.eddypro_biomet,
        InputFileType.CSF: cfg_import.csf,
        InputFileType.IAS: cfg_import.ias
    }
    return cfg_cases[ftype]


def load_time_series(fpath: Path, ftype: InputFileType, cfg_import: ImportConfig) -> pd.DataFrame:
    """ 
    Just loads a table and ensures cfg_import.time_col contains actual timestamps 
    This function is a preparation before possible? switching to import class
    Does not yet create an index with guaranteed frequency yet
    """
    
    ff_logger.info('\n' f'Reading {fpath} ...')
        
    # TODO 1 test biomet and ias - final checks before all load happens here   
    load_arg_cases = {
        InputFileType.EDDYPRO_FO: SimpleNamespace(header_row=0, skiprows=[0, 2]),
        InputFileType.EDDYPRO_BIOMET: SimpleNamespace(header_row=0, skiprows=[1]),
        InputFileType.CSF: SimpleNamespace(header_row=1, skiprows=[2, 3]),
        InputFileType.IAS: SimpleNamespace(header_row=0, skiprows=None)
    }
    load_args = load_arg_cases[ftype]
    
    df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=load_args.header_row, skiprows=load_args.skiprows)
    cfg = get_ftype_cfg(ftype, cfg_import)
    df = parse_timestamp_cols(df, cfg, cfg_import.time_col)
    df = cleanup_df(df, cfg.missing_data_codes)
    return df

    
def ff_load_time_series(fpath, ftype, cfg_import, file_checker, col_converter):
    if file_checker:
        assert file_checker(fpath, cfg_import)
    
    df = load_time_series(fpath, ftype, cfg_import)
    
    ftype_name_cases = {        
        InputFileType.EDDYPRO_FO: 'Full Output',
        InputFileType.EDDYPRO_BIOMET: 'Biomet',
        InputFileType.CSF: 'CSF',
        InputFileType.IAS: 'IAS'
    }
    ftype_name = ftype_name_cases[ftype]    
    
    # Диапазон времени и колонки до resample
    first_and_last = df[cfg_import.time_col].iloc[[0, -1]].dt.strftime('%Y-%m-%d %H:%M')
    ff_logger.info(f'Time range in {ftype_name}: ' + ' - '.join(first_and_last))
    ff_logger.info(f'Колонки в {ftype_name}: \n'
                   f'{df.columns.values}')
    # print("Колонки в CSF \n", df_csf.columns.to_list())
    
    df = col_converter(df)
    
    df = resample_time_series_df(df, cfg_import.time_col, cfg_import.time_freq, fill_gaps=False)
    repair_check_todel(df, cfg_import.time_col, cfg_import.time_freq, fill_gaps=False)
    return df


def load_ftypes(cfg_import: ImportConfig, ff_type: InputFileType, col_converter, file_checker) -> pd.DataFrame:
    """ Loads, checks and merges multiple files of specific type 
    :param file_checker: 
    """
    if ff_type == InputFileType.UNKNOWN:
        raise Exception('Unexpected file type')
    
    dfs = {fpath.name: ff_load_time_series(fpath, ftype, cfg_import, file_checker, col_converter)
           for fpath, ftype in cfg_import.input_files.items() if ftype == ff_type}
    
    fcount = len(dfs)
    if fcount > 1:
        ff_logger.info(f'Merging data from {fcount} files...')
    df = merge_time_series(dfs, cfg_import.time_col, no_duplicate_cols=False)
    
    cfg = get_ftype_cfg(ff_type, cfg_import)
    if cfg.repair_time:
        df = resample_time_series_df(df, cfg_import.time_col, cfg_import.time_freq, fill_gaps=True)
        repair_check_todel(df, cfg_import.time_col, cfg_import.time_freq, fill_gaps=True)
    
    return df
    

def merge_time_series_biomet(df_orig: pd.DataFrame, df_biomet: pd.DataFrame, time_col: str, time_freq: Timedelta) -> pd.DataFrame:
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null 
    :param time_freq: 
    """
    
    # TODO 2 move to same function rather than separate biomet?
    df = df_orig.copy()
    
    same_cols = {col for col in df.columns if col.lower() in df_biomet.columns.str.lower()}
    same_cols = same_cols - {time_col}
    if len(same_cols) > 0:
        ff_logger.warning(f'Duplicate columns {same_cols} on merge with meteo data, using columns from biomet \n')
        df = df.drop(list(same_cols), axis=1)
    
    df = df.join(df_biomet, how='outer', rsuffix='_meteo')
    df[time_col] = df.index
    
    df = resample_time_series_df(df, time_col, time_freq, fill_gaps=True)
    repair_check_todel(df, time_col, time_freq, fill_gaps=True)
    
    # TODO 1 should be done before merge?
    if df[df_biomet.columns[-1]].isna().sum() == len(df.index):
        print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
        return df
    
    return df
