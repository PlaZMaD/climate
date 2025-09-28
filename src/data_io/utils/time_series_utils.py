""" ff unaware pandas level utilities """

import numpy as np
import pandas as pd

from src.ff_logger import ff_log
from src.helpers.py_collections import ensure_list


def get_freq(df, time):
    try_max = 100
    try_ind = 0
    t_shift = 5
    start = 1
    deltas = df[time] - df[time].shift(1)
    while try_ind < try_max:
        del_arr = deltas.iloc[start + try_ind * t_shift: start + try_ind * t_shift + t_shift].values
        if not np.all(del_arr == del_arr[0]) and del_arr[0] is not None:
            try_ind = try_ind + 1
            continue
        else:
            return del_arr[0]


def repair_time(df, time):
    """ based on bglabutils==0.0.21 """
    
    freq = get_freq(df, time)
    df = df.set_index(time, drop=False)
    tmp_index = df.index.copy()
    df = df[~df.index.duplicated(keep='first')]
    
    if not tmp_index.equals(df.index):
        print("Duplicated indexes! check lines:", tmp_index[tmp_index.duplicated() == True])
    
    start = 0
    stop = -1
    while True:
        try:
            pd.to_datetime(df[time].iloc[start])
            break
        except:
            start = start + 1
            continue
    while True:
        try:
            pd.to_datetime(df[time].iloc[stop])
            break
        except:
            stop = stop - 1
            continue
    new_time = pd.DataFrame(index=pd.date_range(start=df[time].iloc[start], end=df[time].iloc[stop],
                                                freq=pd.to_timedelta(freq)))
    new_time = new_time.join(df, how='left')
    return new_time


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
