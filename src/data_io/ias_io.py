from pathlib import Path

import numpy as np
import pandas as pd

from src.config.config_types import DEBUG_NROWS
from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.ias_cols import COLS_IAS_EXPORT_MAP, COLS_IAS_IMPORT_MAP, \
    COLS_IAS_KNOWN, COLS_IAS_TIME, COLS_IAS_UNUSED_NORENAME_IMPORT, COLS_IAS_CONVERSION_IMPORT, \
    COLS_IAS_CONVERSION_EXPORT
from src.data_io.ias_data_check import set_lang, check_ias
from src.data_io.utils.table_loader import load_table_logged
from src.data_io.time_series_loader import repair_time, cleanup_df
from src.data_io.utils.time_series_utils import merge_time_series, detect_datetime_format
from src.config.ff_config import FFConfig, MergedDateTimeFileConfig
from src.helpers.pd_helpers import df_ensure_cols_case
from src.helpers.py_collections import sort_fixed, intersect_list
from src.ff_logger import ff_logger

IAS_EXPORT_MIN_ROWS = 5


# DONE separate check log, but merge into ff_log
# DONE column order improved
# DONE V: implement merge for any amount of iases
# DONE ias: years skipped if IAS data does not contain next year extra row V: could be necessary to fix bug QOA: fix
# DONE E: use TIMESTAMP_START for datetime, not end, nor mid
# DONE check merge chunks are preserved and not overriden by nan rows
# DONE test: merge for any amount of iases

# TODO 1 test: more ias export to match import after export 1y fixed
# TODO 2 ias: V: implement custom split of ias on export (month, year, all years)
# TODO 1 ias: Unsupported by notebook IAS vars - disappeared from 1.0.0 (debug?)


# TODO 1 ias: test no longer required and cleanup or move to export rebuild
'''
def ias_table_extend_year(df: pd.DataFrame, time_col, na_placeholder):
    # TODO QOA 1 appeared to be bugfix of bug introduced in 0.9.3, which skipped last year of IAS export
    # V: possible bug, probably no data should be lost and just filled with empty
    # E: ias should have 1 extra day and export should not export if not a full year
    # after bug fixed, extending year on import won't be nessesary anymore, remove whole func
    
    # add extra row, because main script expects currently for 2020 year extra row at the start of 2021
    # specifically, ias export currently requires 2 years, not 1
    # it does not look right, but not changing export yet
    
    # TODO 3 seems no better option to add row, extract to separate func
    freq = df.index.freq
    last_timestamp: pd.Timestamp = df.last_valid_index()
    next_timestamp = last_timestamp + freq
    if next_timestamp.year - last_timestamp.year == 1:
        new_row = df.loc[last_timestamp].copy()
        new_row.loc[time_col] = next_timestamp
        new_row.loc[df.columns != time_col] = na_placeholder
        df.loc[next_timestamp] = new_row
        df.index.freq = freq
    return df
'''


def import_ias_cols_conversions(df: pd.DataFrame) -> pd.DataFrame:
    # this is a mess, but expected to be moved to proper class or import table later
    
    col = 'VPD_PI_1_1_1'
    if col in df.columns:
        converted_col = COLS_IAS_CONVERSION_IMPORT[col]
        df[converted_col] = df[col] * 0.1  # hPa to kPa
        print(f'{col} was imported to {converted_col}')
    
    return df


def export_ias_cols_conversions(df: pd.DataFrame) -> (pd.DataFrame, [str]):
    new_cols = []
    
    col = 'vpd_1_1_1'
    if col in df.columns:
        converted_col = COLS_IAS_CONVERSION_EXPORT[col]
        df[converted_col] = df[col] * 10
        new_cols += [converted_col]
        print(f'{col} was exported to {converted_col}')
    
    return df, new_cols


def import_ias_process_cols(df: pd.DataFrame, time_col):
    print('Переменные в IAS: \n', df.columns.to_list())
    
    known_ias_cols = COLS_IAS_KNOWN + [time_col]
    df = df_ensure_cols_case(df, known_ias_cols, ignore_missing=True)
    
    unknown_cols = df.columns.difference(known_ias_cols)
    if len(unknown_cols) > 0:
        msg = 'Неизвестные ИАС переменные: \n', str(unknown_cols)
        ff_logger.warning(msg)
    
    unused_cols = df.columns.intersection(COLS_IAS_UNUSED_NORENAME_IMPORT)
    if len(unused_cols) > 0:
        # TODO 3 lang localize properly, check prints (ff_log.* goes to stdout too, but must be ru / en)
        # ff_log.warning('Unused vars (only save loaded): \n' + str(unused_cols.to_list()))
        print('Переменные, которые не используются в скрипте (присутствуют только в загрузке - сохранении): \n',
              unused_cols.to_list())
    
    df = import_ias_cols_conversions(df)
    
    df = df.rename(columns=COLS_IAS_IMPORT_MAP)
    print('Переменные после загрузки: \n', df.columns.to_list())
    
    return df


def import_ias(fpath: Path, out_datetime_col: str, ias: MergedDateTimeFileConfig, skip_validation: bool, debug: bool):
    ff_logger.info('\n' f'Loading {fpath}')
    
    if skip_validation:
        ff_logger.warning('IAS validation is skipped due to user option.')
    elif not debug:
        check_ias(fpath)

    nrows = None if not debug else DEBUG_NROWS
    df = load_table_logged(fpath, nrows=nrows)
    
    assert out_datetime_col not in COLS_IAS_TIME
    assert out_datetime_col not in df.columns
    dt_fmt = detect_datetime_format(df[ias.datetime_col], ias.try_datetime_formats)
    df[out_datetime_col] = pd.to_datetime(df[ias.datetime_col], format=dt_fmt)
    df = df.drop(COLS_IAS_TIME, axis='columns')
    
    # TODO 2 ias: abstract better: time gaps should be filled after merge of multiple files, but index should be done before? 
    if ias.repair_time:
        df = repair_time(df, out_datetime_col, fill_gaps=False)
    print('Диапазон времени IAS (START): ', df.index[[0, -1]])
    ff_logger.info('Time range: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    
    # TODO 2 ias: test no longer required and cleanup
    # df = ias_table_extend_year(df, out_datetime_col, -9999)
    
    df = cleanup_df(df, ias.missing_data_codes)
    
    df = import_ias_process_cols(df, out_datetime_col)
    return df


def import_iases(config: FFConfig):
    # TODO 2 lang move to the script start?
    # will it be translation method for all the tools?
    # afaik это основной метод мультилокальности в питоне, но переделывать под него все потребует усилий.
    set_lang('ru')
    
    dfs = {fpath.name: import_ias(fpath, config.time_col, config.ias, config.ias.skip_validation, config.debug) 
           for fpath, _ in config.input_files.items()}
 
    if len(dfs) > 1:
        ff_logger.info('Merging data from files...')
    df = merge_time_series(dfs, config.time_col, no_duplicate_cols=False)
    if config.ias.repair_time:
        df = repair_time(df, config.time_col, fill_gaps=True)
    
    assert df[config.time_col].isna().sum() == 0
    
    # TODO 3 remove whole biomet_cols_index from the script E, OA: ok
    expected_biomet_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
    biomet_cols_index = df.columns.intersection(expected_biomet_cols)
    
    has_meteo = True
    return df, config.time_col, biomet_cols_index, df.index.freq, has_meteo


def export_ias_prepare_time_cols(df: pd.DataFrame, time_col, min_rows):
    # possibly will be applied later to each year separately
    
    dt_vals = df[time_col]
    first_year = dt_vals.dt.year.min()
    last_year = dt_vals.dt.year.max()
    
    # TODO 1 count skips nans?
    drop_first = dt_vals.where(dt_vals.dt.year == first_year).count() < min_rows
    drop_last = dt_vals.where(dt_vals.dt.year == last_year).count() < min_rows
    if drop_first and last_year > first_year:
        first_year += 1
    if drop_last and last_year > first_year:
        last_year -= 1
    
    new_time_index = pd.date_range(start=f'01.01.{first_year}',
                                   end=f'01.01.{last_year + 1}',
                                   freq=df.index.freq, inclusive='left')
    df_new_time = pd.DataFrame(index=new_time_index)
    df = df_new_time.join(df, how='left')
    df[time_col] = df.index
    
    df['TIMESTAMP_START'] = df[time_col].dt.strftime('%Y%m%d%H%M')
    time_end = df[time_col] + pd.Timedelta(0.5, 'h')
    df['TIMESTAMP_END'] = time_end.dt.strftime('%Y%m%d%H%M')
    
    # 1 365, 366, 1 or 1 365, 366, 367 ?
    # V: not a big deal, but better 1.021 and 367 (by TIMESTAMP_END) 
    # TODO 3 QV ias: from file start or from year start?
    day_part = (time_end.dt.hour * 60 * 60 + time_end.dt.minute * 60 + time_end.dt.second) / (24.0 * 60 * 60)
    df['DTime'] = time_end.dt.dayofyear + np.round(day_part, decimals=3)
    
    # original floating point routine had %
    # s_in_day = pd.Timedelta(days=1).total_seconds()
    # span = time_end - time_end[0] + pd.Timedelta(0.5, 'h')
    # day_part = span.dt.seconds % s_in_day / s_in_day
    # df['DTime'] = np.round(span.dt.days + 1 + day_part, decimals=3)
    return df


def export_ias(out_dir: Path, site_name, ias_out_version, df: pd.DataFrame, time_col: str, data_swin_1_1_1):
    # TODO 2 cols: check if attr/mark can be avoided and no info nessesary to attach to cols
    # E: no attrs approach was kinda intentional
    
    # think about abstraction, i.e. how much script-aware should be ias import and export?
    # may be even merge some import and export routines?
    # TODO 4 may be add test: load ias -> convert to eddypro -> convert to ias -> save ias ?
    
    df, new_cols = export_ias_cols_conversions(df)
    df = df.rename(columns=COLS_IAS_EXPORT_MAP)
    
    var_cols = intersect_list(df.columns, COLS_IAS_EXPORT_MAP.values()) + new_cols
    var_cols = sort_fixed(var_cols, fix_underscore=True)
    # TODO 1 remove after reference data update finished
    # var_cols.sort()
    
    df = export_ias_prepare_time_cols(df, time_col, IAS_EXPORT_MIN_ROWS)
      
    # TODO 1 ias: why they were separate ifs? move to COLS_IAS_EXPORT_MAP?
    #  OA: not important cols
    # were they modified during run?
    # E: probably no special reason, unless cols above all nust be presented
    '''
    if 'h_strg' in df.columns:
        df['SH_1_1_1'] = df['h_strg']
        var_cols.append('SH_1_1_1')
    if 'le_strg' in df.columns:
        df['SLE_1_1_1'] = df['le_strg']
        var_cols.append('SLE_1_1_1')
    '''
    
    # TODO 1 ias: SW_IN_1_1_1 was data col because:
    #  was swin_1_1_1 changed during script run and unchanged data is exported? any other similar cases?
    # OA: RH_1_1_1 - must be exported raw, not filtered (SW_IN_1_1_1 must be exported unchanged)
    if 'SW_IN_1_1_1' in df.columns:
        # assert df['SW_IN_1_1_1'] == data_swin_1_1_1
        df['SW_IN_1_1_1'] = data_swin_1_1_1

    # must be done after all cols added or modified
    df = df.fillna(-9999)

    col_list_ias = COLS_IAS_TIME + var_cols + [time_col]
    print(col_list_ias)
    df = df[col_list_ias]
        
    for year in df.index.year.unique():
        fname = f'{site_name}_{year}_{ias_out_version}.csv'
        fpath = out_dir / fname
        
        save_data = df.loc[df[time_col].dt.year == year]
        save_data = save_data.drop(time_col, axis=1)
        # save_data = save_data.fillna(-9999)
        if len(save_data.index) >= IAS_EXPORT_MIN_ROWS:
            save_data.to_csv(fpath, index=False)
            ff_logger.info(f'IAS file saved to {fpath}')
        else:
            fpath.unlink(missing_ok=True)
            
            # TODO 3 QOA logs: is it ok to simply put in logs most of the script outputs? (removing many dupe prints will be ok)
            # print(f'not enough data for {year}')
            ff_logger.info(f'{year} not saved, not enough data!')
    # ias_year = df[time_col].dt.year.min()
    # fname = f'{site_name}_{ias_year}_{ias_out_version}.csv'
    # ias_df.to_csv(os.path.join('output',fname), index=False)
    # ff_log.info(f'IAS file saved to {os.path.join("output",ias_filename)}.csv')
