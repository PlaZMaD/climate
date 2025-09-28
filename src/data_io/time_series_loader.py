""" 
Currently this is ff aware loader (knows about csf, biomet, fo formats).
Goal is to extract to format unaware utils in time_series_utils.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.data_import_modes import InputFileType
from src.data_io.table_loader import load_table_logged
from src.data_io.utils.time_series_utils import repair_time, pick_datetime_format
from src.ff_logger import ff_log
from src.ff_config import FFConfig


def preprocess_time_csf(df: pd.DataFrame, src_time_col, try_fmts, tgt_time_col):
    """ Only init time column, no checks or repairs """
    fmt = pick_datetime_format(df[src_time_col], try_fmts)
    
    src_time_col_bkp = src_time_col + '_STR'
    
    df.rename(columns={'TIMESTAMP': 'TIMESTAMP_STR'}, inplace=True)
    df[tgt_time_col] = pd.to_datetime(df['TIMESTAMP_STR'], format=fmt)
    return df


def preprocess_time_biomet(df: pd.DataFrame, ftype, tgt_time_col):
    """ Only init time column, no checks or repairs """
    return df


def cleanup_df(df: pd.DataFrame, missing_data_codes):
    print(f'Replacing {missing_data_codes} to np.nan')
    df.replace(missing_data_codes, np.nan, inplace=True)
    return df


def preload_time_series(fpath: Path, ftype: InputFileType, config: FFConfig) -> pd.DataFrame:
    # TODO 3 # if 'debug' in d_config.keys():f:
    if ftype == InputFileType.CSF:
        df = load_table_logged(fpath, header_row=1, skiprows=[2, 3])
        df = preprocess_time_csf(df, config.csf.datetime_col, config.csf.try_datetime_formats, config.time_col)
        df = cleanup_df(df, config.csf.missing_data_codes)
    elif ftype == InputFileType.EDDYPRO_BIOMET:
        # Not switched to use this yet
        df = load_table_logged(fpath, header_row=1)
        df = preprocess_time_biomet(df, ftype, config.time_col)
        df = cleanup_df(df, config.biomet.missing_data_codes)
    else:
        raise Exception('Unexpected file type')
    
    # TODO 1 abstract ts repair
    # return prepare_time_series_df(df)
    return df


def merge_time_series(config, df_biomet, df_csf, has_meteo):
    """ based on bglabutils==0.0.21 """
    
    print("Колонки в CSF \n", df_csf.columns.to_list())
    if has_meteo:
        print("Колонки в метео \n", df_biomet.columns.to_list())
    same_cols = {col for col in df_csf.columns if col.lower() in df_biomet.columns.str.lower()}
    same_cols = same_cols - {config.time_col}
    if len(same_cols) > 0:
        ff_log.warning(f'Duplicate columns {same_cols} on merge with meteo data, using columns from biomet \n')
        df_csf = df_csf.drop(list(same_cols), axis=1)
    # merge into common DataFrame
    if has_meteo:
        df = df_csf.join(df_biomet, how='outer', rsuffix='_meteo')
        df[config.time_col] = df.index
        df = repair_time(df, config.time_col)
        if df[df_biomet.columns[-1]].isna().sum() == len(df.index):
            print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
            has_meteo = False
    else:
        df = df_csf
    # reddyproc requires 3 months
    if config.debug:
        df = df[0: min(31 * 3 * 24 * 2, len(df))]
    return df, has_meteo
    
    ''' consequent merge sample (without repair)
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


def df_init_time_draft(df: pd.DataFrame, time_col: str, repair: bool):
    if not repair:
        raise NotImplementedError
    
    # TODO 3 more transparent rework could be handy:
    #  with support of repair=False and separation of checks, repairs, and standard routines E: ok
    return repair_time(df, time_col)
