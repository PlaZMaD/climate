""" pandas level utilities (ff unaware) """

import numpy as np
import pandas as pd
from pandas import Timedelta

from src.ff_logger import ff_logger
from src.helpers.py_collections import ensure_list, format_dict

# DONE repair time also repairs file gaps
# DONE rework repair_time with separation of checks, repairs, and standard routines E: ok
# DONE checks now work in all files, for example, dupe timestamps in biomet are logged

DETECT_DATETIME_CHUNKS = 12


# TODO 2 ensure this check does not find errors in all examples and cleanup
TEMP_DEBUG_IMPORT = True
def ensure_dfs_same(df1: pd.DataFrame, df2: pd.DataFrame):
    assert (df1.columns == df2.columns).all()    
    check_same = df1.compare(df2)
    assert len(check_same) == 0


def format_year_interval(from_year: int, to_year: int):
    # 2022, 2022 -> 2022 
    # 2023, 2025 -> 23-25
    if from_year == to_year:
        return f'from_year'
    else:
        return f'{from_year % 100}-{to_year % 100}'


def get_freq(df: pd.DataFrame, time_col: str) -> Timedelta:
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null """
    # TODO QE 2 why get_freq (freq guess from file) was even required? why not to directly sample 30min? 
    #  which freqs were encountered apart from 30m and 1m?

    start_offset = 1
    window_sz = 5
    max_search_windows = 20
   
    if len(df) < window_sz + start_offset:
        raise Exception(f'Need at least {window_sz} rows in data to detect table datetime frequency.')
    
    n_windows_max = (len(df) - start_offset) // window_sz
    n_windows = min(n_windows_max, max_search_windows)
    
    deltas = df[time_col] - df[time_col].shift(1)
    for window_idx in range(0, n_windows):
        ws = start_offset + window_idx * window_sz
        window_deltas = deltas[ws: ws + window_sz].values
        
        freq_guess = window_deltas[0]
        if freq_guess and np.all(window_deltas == freq_guess) and isinstance(freq_guess, np.timedelta64):
            return Timedelta(freq_guess)
    raise Exception('Unexpected or unordered time column contents: cannot detect frequency.')


def repair_check_todel(df: pd.DataFrame, time_col: str, time_freq: Timedelta, fill_gaps: bool):
    if not TEMP_DEBUG_IMPORT:
        return 
    # TODO 1 test each routine here on all inputs to ensure this funciton can be finally deleted
    df_check = df.copy()
    
    if not time_freq:
        time_freq = get_freq(df_check, time_col)
    
    df_check = df_check.set_index(time_col, drop=False)
    tmp_index = df_check.index.copy()
    df_check = df_check[~df_check.index.duplicated(keep='first')]
    
    if not tmp_index.equals(df_check.index):
        ff_logger.warning(f'Duplicated time indexes! check lines: {tmp_index[tmp_index.duplicated()]}')

    # TODO 1 after merge, can duplicate timestamps occur? will freq be saved?
    coerced_index: pd.Series = pd.to_datetime(df_check[time_col], errors='coerce')    
    valid_index = coerced_index.dropna()
    
    index_start = valid_index.min()
    first_index = valid_index.iloc[0]
    if first_index != index_start:
        ff_logger.warning(f'First time entry {first_index} is not the earliest {index_start}. Using the earliest. Time order is incorrect.')

    index_end = valid_index.max()
    last_index = valid_index.iloc[-1]
    if last_index != index_end:
        ff_logger.warning(f'Last time entry {last_index} is not the oldest {index_end}. Using the oldest. Time order is incorrect.')
        
    index_rebuild = pd.date_range(start=index_start, end=index_end, freq=time_freq)  
    abnormal_values = valid_index.index.difference(index_rebuild)
    abnormal_count = len(abnormal_values)
    
    if abnormal_count > 1:
        raise Exception(f'Time index contains irregular values not fitting to frequency: {abnormal_values}.')
    elif abnormal_count == 1:
        ff_logger.warning(f'Time index contains irregular value not matching to frequency: {abnormal_values}. Value excluded.')

    if not fill_gaps:
        # drop all points outside freq (1:00, 1:30, 2:00 - ok, 1:31 - drop)
        # will also drop freq
        index_rebuild = index_rebuild.intersection(valid_index)
            
    df_fixed = pd.DataFrame(index=index_rebuild)
    df_fixed = df_fixed.join(df_check, how='left')
    
    assert isinstance(df_fixed.index, pd.DatetimeIndex)
    # na is valid only in case of expanded series, i.e. if original file had deleted time points
    idx = (df_fixed.index == df_fixed[time_col]) | df_fixed[time_col].isna()
    assert idx.all()
    
    # TODO 1 is this required?
    # df_fixed[time_col] = df_fixed.index
    
    ensure_dfs_same(df, df_fixed)


def resample_time_series_df(df: pd.DataFrame, time_col: str, tgt_freq: pd.Timedelta, fill_gaps=True) -> pd.DataFrame:
    """
    Ensures that timestamps drop on tgt_freq in each day 
    :param tgt_freq: if None, frequency will be sort of detected from the first 100 rows
    :param fill_gaps: if False, rows with missing timestamps will be added
    """
    
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
    
    # TODO 1 better way to init freqs from files?
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
    if not fill_gaps:
        idx_rebuild = idx_rebuild.intersection(idx_fix)        
    
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

    # TODO 1 is this required?
    # can be useful not to fill to indicate where data was missing in the source files
    # df_fixed[time_col] = df_fixed.index    
    return df_fixed


'''
def prepare_time_series_df(df: pd.DataFrame, time_col, repair_time, target_freq) -> pd.DataFrame:
    rows = dict(df)     
    for key, item in rows.items():

        # if not item.index.is_monotonic_increasing:
        #     print(f'WARNING the time-index is not monotonic for {key}!')
        # Проверяем время на монотонность
        item.dropna(how='all', axis=0, inplace=True)
        correct_number_of_time_entries = pd.date_range(item[time_col].iloc[0], item[time_col].iloc[-1],
                                                       freq=item[time_col].iloc[1] - item[time_col].iloc[0])

        if not correct_number_of_time_entries.size == len(item.index):
            print("Missing time values")

        if item[time_col].is_monotonic_increasing:
            print(f"The time in {key} looks fine")
        else:
            print(f"The time is not monotonic in {key}")
            test_data = item.copy()
            test_data['shift'] = test_data[time_col].shift(1)
            test_data['diff'] = test_data[time_col] - test_data['shift']
            print("Try to check near: ", test_data.loc[~(test_data['diff'] > np.timedelta64(20, 's')), time_col])
        if d_config['repair_time']:
            print("Fixing time")
            rows[key] = repair_time(item, time_col)
        item.index = item[time_col]

    return rows
'''


def detect_datetime_format(col: pd.Series, guesses: list[str]) -> str:
    """ Attempts to detect datetime format in col. Multiple matches are not considered as correct result. """
    
    test_chunk_size = min(DETECT_DATETIME_CHUNKS, col.size // 2)
    
    start_chunk = col[: test_chunk_size]
    end_chunk = col[-test_chunk_size:]    
    
    ok_formats = []
    for guess in guesses:
        try:
            # optimisation to throw faster on wrong formats
            pd.to_datetime(start_chunk, format=guess)
            pd.to_datetime(end_chunk, format=guess)
            
            pd.to_datetime(col, format=guess)
            ok_formats.append(guess)
        except ValueError:
            continue
    
    if len(ok_formats) == 0:
        raise Exception(f'None of date or time formats worked, check file contents. Formats were {guesses}, '
                        f'Trying to apply them to column data: \n{start_chunk}')
    elif len(ok_formats) > 1:
        raise Exception(f'Multiple date or time formats worked, remove excessive. Formats were {guesses}, '
                        f'Trying to apply them to column data: \n{start_chunk}')
    else:
        if len(guesses) > 1:
            ff_logger.info(f'Detected datetime format {ok_formats[0]}')
        return ok_formats[0]


def detect_or_use_datetime_format(col: pd.Series, guesses: str | list[str]) -> str:    
    guesses = ensure_list(guesses)
    if len(guesses) == 0:
        raise Exception('No time formats are suggested, cannot import date or time column.')
    elif len(guesses) == 1:
        fmt = guesses[0]
        ff_logger.info(f'Using datetime format {fmt}')
        return fmt
    else:
        return detect_datetime_format(col, guesses)
    

def datetime_parser(df: pd.DataFrame,
                    datetime_col: str, datetime_fmt_guesses: str | list[str],
                    pd_to_datetime_errors_arg) -> pd.Series:
    """ Parses datetime column into pd.datetime column"""
    assert datetime_col is not None
    
    dt_strs = df[datetime_col].astype(str)
    datetime_format = detect_or_use_datetime_format(dt_strs, datetime_fmt_guesses)
    res = pd.to_datetime(dt_strs, format=datetime_format, errors=pd_to_datetime_errors_arg)
    
    return res


def date_time_parser(df: pd.DataFrame,
                     time_col: str, time_fmt_guesses: str | list[str],
                     date_col: str, date_fmt_guesses: str | list[str],
                     pd_to_datetime_errors_arg) -> pd.Series:
    """ Parses separate date and time columns into pd.datetime column """
    assert time_col is not None and date_col is not None
    
    date_strs = df[date_col].astype(str)
    date_format = detect_or_use_datetime_format(date_strs, date_fmt_guesses)
    time_strs = df[time_col].astype(str)
    time_format = detect_or_use_datetime_format(time_strs, time_fmt_guesses)
    
    dt_strs = date_strs + " " + time_strs
    res = pd.to_datetime(dt_strs, format=f"{date_format} {time_format}", errors=pd_to_datetime_errors_arg)
    
    return res


def merge_time_series(named_dfs: dict[str: pd.DataFrame], time_col: str, no_duplicate_cols=False):
    """
    dfs: list of (name, df) from the highest intersection priority to the lowest
    merge is done by time_col from each df
    returns merged time series or None if failure
    should not repair time gaps after merge, it's separate operation 
    """
    # TODO 1 ensure cols are renamed (to script name, .columns.str.lower()) before merge

    if len(named_dfs) == 0:
        return None
    elif len(named_dfs) == 1:
        return list(named_dfs.values())[0]
        
        # each df must have two new attributes: .name and .index.freq
    named_freqs = {name: df.index.freq for name, df in named_dfs.items()}
    freqs = np.array(list(named_freqs.values()))
    if not np.all(freqs == freqs[0]):
        raise Exception('Different freqs in data files: \n'
                        f'{format_dict(named_freqs)}. \n'
                        'Import canceled.')
    dfs = []
    for name, df in named_dfs.items():
        for col in df.columns:
            df[col].attrs['source_file'] = name
        dfs += [df]
    
    if no_duplicate_cols:
        # df = dfs[0]
        # for df_join in dfs[1:]:
        #     df = df.join(df_join, how='outer', rsuffix='_meteo')
        df = None
        raise NotImplementedError
    else:
        df = pd.concat(dfs, axis=0)
        df[time_col] = df.index
        # df = df.sort_index()
    
    '''
    if df[df_biomet.columns[-1]].isna().sum() == len(df.index):
        print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
        has_meteo = False
    '''
    
    '''
    cols = pd.Index([])
    for name, df in dfs:        
        if no_duplicate_cols:
            duplicate_cols = cols.intersection(new_cols) - time_col

            if len(duplicate_cols) > 0:
                ff_log.warning(f'Duplicate columns {duplicate_cols} on merge, columns from {name} excluded. \n')
                # TODO 1 ensure works
                df = df.drop(columns=duplicate_cols, axis=1)
            new_cols = df.columns
        else:
            new_cols = new_cols - cols
        cols += new_cols
    '''
    
    ''' horizontal
    df = df_csf.join(df_biomet, how='outer', rsuffix='_meteo')
    df[time_col] = df.index
    df = repair_time(df, config.data_in.time_col)
    if df[df_biomet.columns[-1]].isna().sum() == len(df.index):
        print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
        has_meteo = False
    '''
    
    ''' vertical merge sample (without repair)
        multi_out = pd.concat(dfs)
        multi_out = multi_out.sort_index()
        multi_out = repair_time(multi_out, time)
        return {'default': multi_out}, time
    '''
    return df
