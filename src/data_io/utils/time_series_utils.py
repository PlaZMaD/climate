""" ff unaware pandas level utilities """

import numpy as np
import pandas as pd

from src.ff_logger import ff_logger
from src.helpers.py_collections import ensure_list, format_dict

# DONE repair time also repairs file gaps

MIN_DATETIME_ROWS = 12


def format_year_interval(from_year: int, to_year: int):
    # 2022, 2022->2022 
    # 2023, 2025 -> 23-25
    if from_year == to_year:
        return f'from_year'
    else:
        return f'{from_year % 100}-{to_year % 100}'


def get_freq(df, time_col):
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null """
    
    max_search_len = 100
    window_sz = 5
    start_offset = 1
    n_windows = min(max_search_len, len(df) - start_offset) // window_sz
    
    deltas = df[time_col] - df[time_col].shift(1)
    for window_idx in range(0, n_windows):
        ws = start_offset + window_idx * window_sz
        window_deltas = deltas[ws: ws + window_sz].values
        
        freq_guess = window_deltas[0]
        if freq_guess and np.all(window_deltas == freq_guess):
            return freq_guess
    raise Exception('Unexpected or unordered time column contents: cannot detect frequency.')


def repair_time(df: pd.DataFrame, time_col, fill_gaps: bool):
    """ 
    source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null
    df.index could be both pd.RangeIndex or pd.DatetimeIndex (if converted previously) 
    """
    
    # TODO 3 more transparent rework could be handy:
    # with support of repair=False and separation of checks, repairs, and standard routines E: ok
     
    if df[time_col].size < MIN_DATETIME_ROWS:
        raise Exception(f'Need at least {MIN_DATETIME_ROWS} rows in data for time repair.')
    
    freq = get_freq(df, time_col)
    # freq.astype('timedelta64[h]')
    
    df = df.set_index(time_col, drop=False)
    tmp_index = df.index.copy()
    df = df[~df.index.duplicated(keep='first')]
    
    if not tmp_index.equals(df.index):
        ff_logger.warning(f'Duplicated time indexes! check lines: {tmp_index[tmp_index.duplicated()]}')

    # TODO 1 QOA test: shouldn't start/end time errors be not allowed at all?
    # can be optimised, also what if years are reversed?
    coerced_index: pd.Series = pd.to_datetime(df[time_col], errors='coerce')    
    valid_index = coerced_index.dropna()
    
    index_start = valid_index.min()
    first_index = valid_index.iloc[0]
    if first_index != index_start:
        ff_logger.warning(f'First time entry {first_index} is not the earliest {index_start}. Using the earliest. Time order is incorrect.')

    index_end = valid_index.max()
    last_index = valid_index.iloc[-1]
    if last_index != index_end:
        ff_logger.warning(f'Last time entry {last_index} is not the oldest {index_end}. Using the oldest. Time order is incorrect.')
            
    index_rebuild = pd.date_range(start=index_start, end=index_end, freq=pd.to_timedelta(freq))  
    abnormal_values = valid_index.index.difference(index_rebuild)
    abnormal_count = len(abnormal_values)
    
    if abnormal_count > 1:
        raise Exception(f'Time index contains irregular values not fitting to frequency: {abnormal_values}.')
    elif abnormal_count == 1:
        ff_logger.warning(f'Time index contains irregular value not matching to frequency: {abnormal_values}. Value excluded.')

    if not fill_gaps:
        # TODO 1 kills freq, need fix
        index_rebuild = index_rebuild.intersection(valid_index)
            
    df_fixed = pd.DataFrame(index=index_rebuild)
    df_fixed = df_fixed.join(df, how='left')
    
    assert isinstance(df_fixed.index, pd.DatetimeIndex)
    idx = (df_fixed.index == df_fixed[time_col]) | df_fixed[time_col].isna()
    assert idx.all()
    df_fixed[time_col] = df_fixed.index
    
    assert df_fixed.index.freq
    
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


def detect_datetime_format(col: pd.Series, guesses: str | list[str]) -> str:
    """ 
    Attempts to detect datetime format on df column.
    Skips detection if only one guess is provided. 
    Multiple matches are not considered as correct result.
    Required as separate function for now due because consequently passed to the library.
    """
    
    guesses = ensure_list(guesses)
    if len(guesses) == 1:
        fmt = guesses[0]
        ff_logger.info(f'Using datetime format {fmt}')
        return fmt
    
    if col.size < MIN_DATETIME_ROWS:
        raise Exception(f'Need at least {MIN_DATETIME_ROWS} rows in data for time format detection.')
    
    start_chunk = col[: MIN_DATETIME_ROWS]
    end_chunk = col[-MIN_DATETIME_ROWS:]
    
    ok_formats = []
    for guess in guesses:
        try:
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


def datetime_parser(df: pd.DataFrame, datetime_col: str, datetime_fmt_guesses: str | list[str]) -> pd.Series:
    """ Parses datetime column into pd.datetime column"""
    assert datetime_col is not None
    
    datetime_format = detect_datetime_format(df[datetime_col], datetime_fmt_guesses)
    res = pd.to_datetime(df[datetime_col], format=datetime_format)
    
    return res


def date_time_parser(df: pd.DataFrame,
                     time_col: str, time_fmt_guesses: str | list[str],
                     date_col: str, date_fmt_guesses: str | list[str]) -> pd.Series:
    """ Parses separate date and time columns into pd.datetime column """
    assert time_col is not None and date_col is not None
    
    date = df[date_col].astype(str)
    date_format = detect_datetime_format(date, date_fmt_guesses)
    time = df[time_col].astype(str)
    time_format = detect_datetime_format(time, time_fmt_guesses)
    
    tmp_datetime = date + " " + time
    res = pd.to_datetime(tmp_datetime, format=f"{date_format} {time_format}")
    
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
