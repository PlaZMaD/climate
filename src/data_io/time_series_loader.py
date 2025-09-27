from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.data_import_modes import InputFileType
from src.data_io.table_loader import load_table_logged
from src.ffconfig import FFConfig


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


def preprocess_time_csf(df: pd.DataFrame, ftype, tgt_time_col):
    """ Only init time column, no checks or repairs """
    df.rename(columns={'TIMESTAMP': 'TIMESTAMP_STR'}, inplace=True)
    df[tgt_time_col] = pd.to_datetime(df['TIMESTAMP_STR'], format='%Y-%m-%d %H:%M:%S')
    return df


def preprocess_time_biomet(df: pd.DataFrame, ftype, tgt_time_col):
    """ Only init time column, no checks or repairs """
    return df


def cleanup_df(df: pd.DataFrame):
    print('Replacing -9999 to np.nan')
    df.replace(-9999, np.nan, inplace=True)
    return df


def preload_time_series(fpath: Path, ftype: InputFileType, config: FFConfig) -> pd.DataFrame:
    # TODO 3 # if 'debug' in d_config.keys():f:
    if ftype == InputFileType.CSF:
        df = load_table_logged(fpath, header_row=1, skiprows=[2, 3])
        df = preprocess_time_csf(df, ftype, config.time_col)
        df = cleanup_df(df)
    elif ftype == InputFileType.EDDYPRO_BIOMET:
        df = load_table_logged(fpath, header_row=1)
        df = preprocess_time_biomet(df, ftype, config.time_col)
        df = cleanup_df(df)
    else:
        raise Exception('Unexpected file type')
        
    # TODO 1 abstract ts repair
    # return prepare_time_series_df(df)
    return df
    


def merge_time_series():
    '''
        multi_out = []
        time = None
        for file in d_config['path']:
            temp_config = d_config.copy()
            temp_config['path'] = file
            loaded_data, time = load_df(temp_config)
            multi_out = multi_out + [df for df in loaded_data.values()]
        freqs = [df.index.freq for df in loaded_data.values()]
        if not np.all(np.array(freqs) == freqs[0]):
            print("Different freq in data files. Aborting!")
            return None

        multi_out = pd.concat(multi_out)
        multi_out = multi_out.sort_index()
        multi_out = repair_time(multi_out, time)
        return {'default': multi_out}, time
    '''
    
    '''
        for file in d_config['path']:
            temp_config = d_config.copy()
            temp_config['path'] = file
            loaded_data, time = load_df(temp_config)
            multi_out = multi_out + [df for df in loaded_data.values()]
        freqs = [df.index.freq for df in loaded_data.values()]
        if not np.all(np.array(freqs) == freqs[0]):
            print("Different freq in data files. Aborting!")
            return None
    '''
    pass
