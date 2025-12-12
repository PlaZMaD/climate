""" 
Currently this is ff aware loader (knows about csf, biomet, fo formats).
Format unaware utils and helpers are in time_series_utils.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from pandas import Timedelta

from src.config.config_types import InputFileType
from src.data_io.utils.table_loader import load_table_logged
from src.data_io.utils.time_series_utils import repair_time, date_time_parser, datetime_parser, get_freq
from src.ff_logger import ff_logger
from src.config.ff_config import ImportConfig, SeparateDateTimeFileConfig, MergedDateTimeFileConfig, InputFileConfig

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
    
    # TODO 2 test: bad or missing timestamps
    bad_mask = df[tgt_time_col].isna()
    if bad_mask.any():
        bad_percent = 100 * bad_mask.sum() / bad_mask.size
        ff_logger.warning(f'{bad_percent}% of timestamps are bad and will be removed: \n'
                          f'{df[tgt_time_col][bad_mask]} \n')
        df = df[~bad_mask]
    
    # TODO 2 test: duplicate timestamps
    dupe_mask = df[tgt_time_col].duplicated(keep='first')
    if dupe_mask.any():
        bad_percent = 100 * dupe_mask.sum() / dupe_mask.size
        ff_logger.warning(f'{bad_percent}% of timestamps are duplicated and will be removed: \n'
                          f'{df[tgt_time_col][dupe_mask]} \n')
        df = df[~dupe_mask]
    
    if 100 * (original_size - df.size) / df.size > MAX_BAD_TIMESTAMPS_PERCENT:
        raise Exception('Too much bad timestamps, file requires manual review.')
    
    # df.loc[5:6, 'datetime'] = df.loc[4:5, 'datetime'][::-1].values
    # TODO 2 test: wrong order
    deltas = df[tgt_time_col] - df[tgt_time_col].shift(1)
    reversed_mask = deltas.values < 0
    if reversed_mask.any():
        bad_percent = 100 * reversed_mask.sum() / reversed_mask.size
        ff_logger.warning(f'{bad_percent}% of timestamps are reversed. Data order will be rearranged: \n'
                          f'{df[tgt_time_col][reversed_mask]} \n')
        df = df.sort_values(tgt_time_col).reset_index()
    return df


def resample_time_series_df(df: pd.DataFrame, time_col: str, tgt_freq: pd.Timedelta):
    """:param tgt_freq: if None, frequency will be sort of detected from the first 100 rows"""

    # TODO 2 test/fix: irregular frequency timestamps (05:00 05:07, 05:30, 05:37, 06:00, ...)
    # TODO 2 test/fix: resample 1m -> 30m, 2h -> 30m ? 
    # TODO 1 currently 1m -> 30m is done by deleting 29 vals, but should be done by mean 0m..30m -> 30m or? 0m, 30m..59m -> 30m or? 0m
     
    df = df.set_index(time_col, drop=False)
    assert not df.index.duplicated(keep='first').any()
        
    # TODO 1 QOA test: shouldn't start/end time errors be not allowed at all?
    idx_src: pd.Series = pd.to_datetime(df[time_col], errors='coerce')
    assert idx_src.isna().sum() == 0
    
    # TODO 1 test index order failures
    index_start = idx_src.min()
    first_index = idx_src.iloc[0]
    if first_index != index_start:
        ff_logger.warning(
            f'First time entry {first_index} is not the earliest {index_start}. Using the earliest. Time order is incorrect.')
    
    index_end = idx_src.max()
    last_index = idx_src.iloc[-1]
    if last_index != index_end:
        ff_logger.warning(
            f'Last time entry {last_index} is not the oldest {index_end}. Using the oldest. Time order is incorrect.')

    src_data_freq = get_freq(df, time_col)
    if not tgt_freq:
        tgt_freq = src_data_freq
        # src_data_freq.astype('timedelta64[h]')

    # TODO 1 just deleting starting and ending chunks is wrong, resampling may be required like (:37m + :59m) -> :59m    
    idx_fix = idx_src.sort_values()
    assert tgt_freq.seconds < 3600
    fits_half_hour_mask = idx_fix.dt.minute % (tgt_freq.seconds // 60) == 0
    
    # TODO 1 do actual correct resampling later
    # max_crop = min(MAX_NON_HALF_HOUR_TIMESTAMPS_CROP, df.size // 3)
    # if reversed_mask.any():
    #     bad_percent = 100 * reversed_mask.sum / reversed_mask.size
    #     ff_logger.warning()
    
    idx_fix = idx_fix[fits_half_hour_mask]
    half_hour_index_start = idx_fix.min()
    half_hour_index_end = idx_fix.max()
    idx_rebuild = pd.date_range(start=half_hour_index_start, end=half_hour_index_end, freq=tgt_freq)
    
    # just an additional check of timestamp integrity before resampling    
    idx_check = pd.date_range(start=half_hour_index_start, end=half_hour_index_end, freq=src_data_freq)
    abnormal_values = idx_fix.index.difference(idx_src)
    abnormal_count = len(abnormal_values)    
    if abnormal_count > 1:
        raise Exception(f'Time index contains irregular values not fitting to frequency: {abnormal_values}.')
    elif abnormal_count == 1:
        ff_logger.warning(
            f'Time index contains irregular value not matching to the original frequency: {abnormal_values}. Value excluded.')
      
    df_fixed = pd.DataFrame(index=idx_rebuild).join(df, how='left')    
    assert isinstance(df_fixed.index, pd.DatetimeIndex)    
    # na in time_col is valid only in case of expanded series, i.e. if original file had deleted time points
    idx_fix = (df_fixed.index == df_fixed[time_col]) | df_fixed[time_col].isna()
    assert idx_fix.all()
    
    # can be useful not to fill to indicate where data was missing in the source files
    # df_fixed[time_col] = df_fixed.index    
    return df_fixed


def preload_time_series(fpath: Path, ftype: InputFileType, cfg_import: ImportConfig) -> pd.DataFrame:
    """ 
    Just loads a table and ensures cfg_import.time_col contains actual timestamps 
    This function is a preparation before possible? switching to import class
    Does not yet create an index with guaranteed frequency yet
    """
    
    cfg: SeparateDateTimeFileConfig | MergedDateTimeFileConfig
    
    # TODO 1 test biomet and ias - final checks before all load happens here
    if ftype == InputFileType.CSF:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=1, skiprows=[2, 3])
        cfg = cfg_import.csf
    elif ftype == InputFileType.EDDYPRO_BIOMET:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=0, skiprows=[1])
        cfg = cfg_import.eddypro_biomet
    elif ftype == InputFileType.EDDYPRO_FO:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=0, skiprows=[0, 2])
        cfg = cfg_import.eddypro_fo
    elif ftype == InputFileType.IAS:
        df = load_table_logged(fpath, nrows=cfg_import.debug_nrows, header_row=0)
        cfg = cfg_import.ias
    else:
        raise Exception('Unexpected file type')
    
    df = parse_timestamp_cols(df, cfg, cfg_import.time_col)
    df = cleanup_df(df, cfg.missing_data_codes)
    df = resample_time_series_df(df, cfg_import.time_col, cfg_import.time_freq)
    return df


def merge_time_series_biomet(df_orig: pd.DataFrame, df_biomet: pd.DataFrame, time_col: str, time_freq: Timedelta) -> [
    pd.DataFrame, bool]:
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null 
    :param time_freq: 
    """
    
    df = df_orig.copy()
    same_cols = {col for col in df.columns if col.lower() in df_biomet.columns.str.lower()}
    same_cols = same_cols - {time_col}
    if len(same_cols) > 0:
        ff_logger.warning(f'Duplicate columns {same_cols} on merge with meteo data, using columns from biomet \n')
        df = df.drop(list(same_cols), axis=1)
    
    df = df.join(df_biomet, how='outer', rsuffix='_meteo')
    df[time_col] = df.index
    df = repair_time(df, time_col, time_freq, fill_gaps=True)
    
    if df[df_biomet.columns[-1]].isna().sum() == len(df.index):
        print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
        return df, False
    
    return df, True
