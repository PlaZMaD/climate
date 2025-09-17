import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.ias_cols import COLS_IAS_EXPORT_MAP, COLS_IAS_IMPORT_MAP, \
    COLS_IAS_KNOWN, COLS_IAS_TIME, COLS_IAS_UNUSED_NORENAME_IMPORT, COLS_IAS_CONVERSION_IMPORT, \
    COLS_IAS_CONVERSION_EXPORT
from src.data_io.ias_error_check import set_lang, draft_check_ias
from src.data_io.table_loader import load_table_logged
from src.data_io.time_series_utils import df_init_time_draft
from src.ffconfig import FFConfig
from src.helpers.pd_helpers import df_ensure_cols_case
from src.helpers.py_helpers import sort_fixed, intersect_list


# TODO 1 test more ias export to match import after export 1y fixed


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


def import_ias_cols(df: pd.DataFrame, time_col):
    print('Переменные в IAS: \n', df.columns.to_list())

    known_ias_cols = COLS_IAS_KNOWN + [time_col]
    df = df_ensure_cols_case(df, known_ias_cols, ignore_missing=True)

    unknown_cols = df.columns.difference(known_ias_cols)
    if len(unknown_cols) > 0:
        msg = 'Неизвестные ИАС переменные: \n', str(unknown_cols)
        logging.critical(msg)

    unsupported_cols = df.columns.intersection(COLS_IAS_UNUSED_NORENAME_IMPORT)
    if len(unsupported_cols) > 0:
        # TODO 2 localize properly, check prints (logging.* goes to stdout too, but must be ru / en)
        print('Переменные, которые не используются в тетради (присутствуют только в загрузке - сохранении): \n',
              unsupported_cols.to_list())
        logging.warning('Unsupported by notebook IAS vars (only save loaded): \n' + str(unsupported_cols.to_list()))

    df = import_ias_cols_conversions(df)

    df = df.rename(columns=COLS_IAS_IMPORT_MAP)
    print('Переменные после загрузки: \n', df.columns.to_list())

    # TODO 2 remove whole biomet_cols_index from the script E, OA: ok
    expected_biomet_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
    biomet_cols_index = df.columns.intersection(expected_biomet_cols)
    return df, biomet_cols_index


def import_ias(config: FFConfig):
    # TODO 2 move to ipynb?
    set_lang('ru')

    # TODO 1 V: implement merge for any amount of iases
    # TODO 2 V: implement custom split of ias on export (month, year, all years)
    if len(config.input_files) != 1:
        raise NotImplementedError(
            'Multiple IAS files detected. Multiple run or combining multiple files is not supported yet.')
    ias_fpath = list(config.input_files.keys())[0]
    draft_check_ias(ias_fpath)
    df = load_table_logged(ias_fpath)
    ''' from eddypro to ias
    for year in ias_df.index.year.unique():
        ias_filename = f'{ias_output_prefix}_{year}_{ias_output_version}.csv'
        save_data = ias_df.loc[ias_df[time_col].dt.year == year]
        save_data = save_data.drop(time_col, axis=1)
        save_data = save_data.fillna(-9999)
        if len(save_data.index) >= 5:
            save_data.to_csv(os.path.join('output', ias_filename), index=False)
            logging.info(f'IAS file saved to {os.path.join('output', ias_filename)}.csv')
        else:
            try:
                os.remove(os.path.join('output', ias_filename))
            except Exception as e:
                print(e)

            print(f'not enough df for {year}')
            logging.info(f'{year} not saved, not enough df!')
    # ias_filename = f'{ias_output_prefix}_{ias_year}_{ias_output_version}.csv'
    # ias_df.to_csv(os.path.join('output',ias_filename), index=False)
    '''

    # TODO 2 check conversion is to TIMESTAMP_START E: eddypro = TIMESTAMP_START, not end, nor mid
    time_col = 'datetime'
    df[time_col] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
    df = df.drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis='columns')
    df = df_init_time_draft(df, time_col)

    print('Диапазон времени IAS (START): ', df.index[[0, -1]])
    logging.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    df = ias_table_extend_year(df, time_col, -9999)

    print('Replacing -9999 to np.nan')
    df.replace(-9999, np.nan, inplace=True)

    df, biomet_cols_index = import_ias_cols(df, time_col)

    has_meteo = True
    return df, time_col, biomet_cols_index, df.index.freq, has_meteo


def export_ias_prepare_time_cols(df: pd.DataFrame, time_col):
    # possibly will be applied later to each year separately

    # TODO 1 QOA years is skipped if IAS data does not contain next year extra row
    # V: could be necessary to fix bug E: intentionally, E: Вопрос к Вадиму. Я не знаю, совпадает определение полного года дя ИАС и остальных данных
    new_time_index = pd.date_range(start=f'01.01.{df[time_col].dt.year.min()}',
                                   end=f'01.01.{df[time_col].dt.year.max()}',
                                   freq=df.index.freq, inclusive='left')
    df_new_time = pd.DataFrame(index=new_time_index)
    df = df_new_time.join(df, how='left')
    df[time_col] = df.index

    df['TIMESTAMP_START'] = df[time_col].dt.strftime('%Y%m%d%H%M')
    time_end = df[time_col] + pd.Timedelta(0.5, 'h')
    df['TIMESTAMP_END'] = time_end.dt.strftime('%Y%m%d%H%M')

    # 1 365, 366, 1 or 1 365, 366, 367 ?
    # V: not a big deal, but better 1.021 and 367 (by TIMESTAMP_END) 
    # TODO 3 QV from file start or from year start?
    day_part = (time_end.dt.hour * 60 * 60 + time_end.dt.minute * 60 + time_end.dt.second) / (24.0 * 60 * 60)
    df['DTime'] = time_end.dt.dayofyear + np.round(day_part, decimals=3)

    # original floating point routine had %
    # s_in_day = pd.Timedelta(days=1).total_seconds()
    # span = time_end - time_end[0] + pd.Timedelta(0.5, 'h')
    # day_part = span.dt.seconds % s_in_day / s_in_day
    # df['DTime'] = np.round(span.dt.days + 1 + day_part, decimals=3)
    return df


def export_ias(out_dir: Path, ias_output_prefix, ias_output_version, df: pd.DataFrame, time_col: str, data_swin_1_1_1):
    # TODO 2 check if attr/mark can be avoided and no info nessesary to attach to cols
    # E: no attrs approach was kinda intentional

    # think about abstraction, i.e. how much script-aware should be ias import and export?
    # may be even merge some import and export routines?
    # TODO 3 may be add test: load ias -> convert to eddypro -> convert to ias -> save ias ?

    df, new_cols = export_ias_cols_conversions(df)
    df = df.rename(columns=COLS_IAS_EXPORT_MAP)

    df = df.fillna(-9999)
    
    var_cols = intersect_list(df.columns, COLS_IAS_EXPORT_MAP.values()) + new_cols
    # TODO 1 enable back after comparing finished
    sort_fixed(var_cols, fix_underscore=True)
    # var_cols.sort()

    df = export_ias_prepare_time_cols(df, time_col)

    # TODO 1 why they were separate ifs? move to COLS_IAS_EXPORT_MAP?
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

    # TODO 1 SW_IN_1_1_1 was data col because:
    #  was swin_1_1_1 changed during script run and unchanged data is exported? any other similar cases?
    # OA: RH_1_1_1 - must be exported raw, not filtered (SW_IN_1_1_1 must be exported unchanged)
    if 'SW_IN_1_1_1' in df.columns:
        # assert df['SW_IN_1_1_1'] == data_swin_1_1_1
        df['SW_IN_1_1_1'] = data_swin_1_1_1

    col_list_ias = COLS_IAS_TIME + var_cols + [time_col]
    print(col_list_ias)
    df = df[col_list_ias]

    for year in df.index.year.unique():
        fname = f'{ias_output_prefix}_{year}_{ias_output_version}.csv'
        fpath = out_dir / fname

        save_data = df.loc[df[time_col].dt.year == year]
        save_data = save_data.drop(time_col, axis=1)
        save_data = save_data.fillna(-9999)
        if len(save_data.index) >= 5:
            save_data.to_csv(fpath, index=False)
            logging.info(f'IAS file saved to {fpath}')
        else:
            fpath.unlink(missing_ok=True)

            # TODO 2 is print excessive?
            # print(f'not enough data for {year}')
            logging.info(f'{year} not saved, not enough data!')
    # ias_year = df[time_col].dt.year.min()
    # fname = f'{ias_output_prefix}_{ias_year}_{ias_output_version}.csv'
    # ias_df.to_csv(os.path.join('output',fname), index=False)
    # logging.info(f'IAS file saved to {os.path.join("output",ias_filename)}.csv')
