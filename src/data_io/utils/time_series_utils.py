""" ff unaware pandas level utilities """

import numpy as np
import pandas as pd

from src.ff_logger import ff_log
from src.helpers.py_collections import ensure_list, format_dict


def get_freq(df, time_col):
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null """
    
    try_max = 100
    try_ind = 0
    t_shift = 5
    start = 1
    deltas = df[time_col] - df[time_col].shift(1)
    while try_ind < try_max:
        del_arr = deltas.iloc[start + try_ind * t_shift: start + try_ind * t_shift + t_shift].values
        if not np.all(del_arr == del_arr[0]) and del_arr[0] is not None:
            try_ind = try_ind + 1
            continue
        else:
            return del_arr[0]


def repair_time(df, time_col):
    """ source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null """

    # TODO 3 more transparent rework could be handy:
    #  with support of repair=False and separation of checks, repairs, and standard routines E: ok
    
    freq = get_freq(df, time_col)
    df = df.set_index(time_col, drop=False)
    tmp_index = df.index.copy()
    df = df[~df.index.duplicated(keep='first')]
    
    if not tmp_index.equals(df.index):
        print("Duplicated indexes! check lines:", tmp_index[tmp_index.duplicated() == True])
    
    start = 0
    stop = -1
    while True:
        try:
            pd.to_datetime(df[time_col].iloc[start])
            break
        except:
            start = start + 1
            continue
    while True:
        try:
            pd.to_datetime(df[time_col].iloc[stop])
            break
        except:
            stop = stop - 1
            continue
    df_fixed = pd.DataFrame(index=pd.date_range(start=df[time_col].iloc[start], end=df[time_col].iloc[stop],
                                                freq=pd.to_timedelta(freq)))
    df_fixed = df_fixed.join(df, how='left')
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


def pick_datetime_format(col: pd.Series, guesses: str | list[str]) -> str:
    """ 
    Attempts to detect datetime format on df column. 
    If multiple matches fit, this is not considered as correct result. 
    """
    # TODO 4 raise in wrapper, not here
    
    guesses = ensure_list(guesses)
    
    rows = len(col)
    if rows < 100:
        raise Exception(f'Cannot detect datetime format based on less than 100 rows. Rows provided: {rows}')
    
    test_chunk = col[0:10]
    
    ok_formats = []
    for guess in guesses:
        try:
            pd.to_datetime(test_chunk, format=guess)
        except ValueError:
            continue
        ok_formats.append(guess)
    
    if len(ok_formats) == 0:
        raise Exception(f'None of date or time formats worked, check file contents. Formats were {guesses}, '
                        f'Trying to apply them to column data: \n{test_chunk}')
    elif len(ok_formats) > 1:
        raise Exception(f'Multiple date or time formats worked, remove excessive. Formats were {guesses}, '
                        f'Trying to apply them to column data: \n{test_chunk}')
    else:
        if len(guesses) > 1:
            ff_log.info(f'Using datetime format {ok_formats[0]}')
        return ok_formats[0]


def datetime_parser(df: pd.DataFrame, datetime_col: str, datetime_fmt_guesses: str | list[str]) -> pd.Series:
    """ Parses datetime column into pd.datetime column"""    
    assert datetime_col is not None
    
    datetime_format = pick_datetime_format(df[datetime_col], datetime_fmt_guesses)
    res = pd.to_datetime(df[datetime_col], format=datetime_format)
    
    return res


def date_time_parser(df: pd.DataFrame,
                     time_col: str, time_fmt_guesses: str | list[str],
                     date_col: str, date_fmt_guesses: str | list[str]) -> pd.Series:
    """ Parses separate date and time columns into pd.datetime column """
    assert time_col is not None and date_col is not None
       
    date = df[date_col].astype(str)
    date_format = pick_datetime_format(date, date_fmt_guesses)
    time = df[time_col].astype(str)
    time_format = pick_datetime_format(time, time_fmt_guesses)
    
    tmp_datetime = date + " " + time
    res = pd.to_datetime(tmp_datetime, format=f"{date_format} {time_format}")    

    return res


def merge_time_series(named_dfs: dict[str: pd.DataFrame], time_col: str, no_duplicate_cols=False):
    """
    dfs: list of (name, df) from the highest intersection priority to the lowest
    merge is done by time_col from each df
    returns merged time series or None if failure 
    """
    # TODO 1 ensure cols are renamed (to script name, .columns.str.lower()) before merge
    # TODO 1 ensure time is repaired (index.freq) before merge
    if len(named_dfs) == 0:
        return None
    elif len(named_dfs) == 1:
        return named_dfs.values()[0]    

    # each df must have two new attributes: .name and .index.freq
    named_freqs = {name: df.index.freq for name, df in named_dfs.items()}
    freqs = np.array(list(named_freqs.values()))
    if not np.all(freqs == freqs[0]):
        raise Exception(f'Aborting, different freqs in data files: {format_dict(named_freqs)}')
    
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
        df = repair_time(df, time_col)

    # TODO 1 ensure no datetime gaps?
    # if to use fo and biomet from different years, this will fail on rep export; ensure this is detected earlier
    assert df[time_col].isna().sum() == 0

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
    df = repair_time(df, config.time_col)
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
