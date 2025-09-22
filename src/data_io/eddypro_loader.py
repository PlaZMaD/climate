import pandas as pd

import bglabutils.basic as bg
from src.helpers.py_helpers import ensure_list
from src.ff_logger import ff_log
from src.data_io.data_import_modes import ImportMode, InputFileType
from src.ffconfig import FFConfig


def load_biomet(config_meteo, data_freq):
    print("Проверяем корректность временных меток. Убираем повторы, дополняем пропуски. "
          "На случай загрузки нескольких файлов. При загрузке одного делается автоматически.")

    data_meteo, time_meteo = bg.load_df(config_meteo)
    data_meteo = data_meteo[next(iter(data_meteo))]  # т.к. изначально у нас словарь

    meteo_freq = data_meteo.index.freq
    print("Диапазон времени метео: ", data_meteo.index[[0, -1]])
    ff_log.info(f"MeteoData loaded from {config_meteo['path']}")
    ff_log.info("Time range for meteo: " + " - ".join(data_meteo.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

    if data_freq != meteo_freq:
        print("Resampling meteo data")
        ff_log.info(f"Resampling meteo data")
        data_meteo = data_meteo.asfreq(data_freq)

    return data_meteo


def pick_datetime_format(col: pd.Series, guesses: str | list[str]) -> str:
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
                        f'Trying to apply then to column data: \n{test_chunk}')
    elif len(ok_formats) > 1:
        raise Exception(f'Multiple date or time formats worked, remove excessive. Formats were {guesses}, '
                        f'Trying to apply them to column data: \n{test_chunk}')
    else:
        if len(guesses) > 1:
            ff_log.info(f'Using datetime format {ok_formats[0]}')
        return ok_formats[0]


def datetime_converter(df: pd.DataFrame,
                       time_col: str | None = None, time_formats: str | list[str] | None = None,
                       date_col: str | None = None, date_formats: str | list[str] | None = None,
                       datetime_col: str | None = None, datetime_formats: str | list[str] | None = None) -> pd.Series:
    # TODO 3 move to abstract load utils? 
    # TODO 1 split fo and biomet

    has_date_and_time_cols = time_col is not None and date_col is not None
    has_datetime_col = datetime_col is not None

    if has_date_and_time_cols == has_datetime_col:
        raise Exception(
            'Unexpected time and date column options: specify time_col and date_col or datetime_col in import options.')

    if has_date_and_time_cols:
        date = df[date_col].astype(str)
        date_format = pick_datetime_format(date, date_formats)
        time = df[time_col].astype(str)
        time_format = pick_datetime_format(time, time_formats)

        tmp_datetime = date + " " + time
        res = pd.to_datetime(tmp_datetime, format=f"{date_format} {time_format}")
    elif has_datetime_col:
        datetime_format = pick_datetime_format(df[datetime_col], datetime_formats)
        res = pd.to_datetime(df[datetime_col], format=datetime_format)
    else:
        res = None

    return res

# TODO 1 in the ipynb, u_star is not yet renamed at the next line?
# cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength',
# ppfd_in_1_1_1 will be renamed to ppfd_1_1_1, 

# TODO 1 some renames in the main script are specific to eddypro/biomet files and should not be part of main script anymore?
# if moved, check ias import-export handling stands (or solve with generalised col names preprocess check?)
def load_eddypro(config: FFConfig):
    c_fo = config.eddypro_fo
    c_bm = config.eddypro_biomet
    fo_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_FO]
    bm_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET]

    # load of eddypro = full_output, optionally with biomet
    if not set(c_fo.missing_data_codes) <= {'-9999'}:
        raise NotImplementedError(f"Not yet supported missing codes: {c_fo.missing_data_codes}")

    bg_fo_config = {
        'path': fo_paths,
        # reddyproc requires 90 days, see this function below
        'debug': False,
        '-9999_to_nan': '-9999' in c_fo.missing_data_codes,
        'time': {
            'column_name': config.time_col,
            'converter': lambda x: datetime_converter(x,
                                                      time_col=c_fo.time_col, time_formats=c_fo.try_time_formats,
                                                      date_col=c_fo.date_col, date_formats=c_fo.try_date_formats)
        },
        'repair_time': c_fo.repair_time,
    }
    df, time_col = bg.load_df(bg_fo_config)
    df = df[next(iter(df))]  # т.к. изначально у нас словарь
    data_freq = df.index.freq

    print("Диапазон времени full_output: ", df.index[[0, -1]])
    ff_log.info("Time range for full_output: " + " - ".join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

    has_meteo = (config.import_mode == ImportMode.EDDYPRO_FO_AND_BIOMET)
    if has_meteo:
        bg_bm_config = {
            'path': bm_paths,
            'debug': False,
            '-9999_to_nan': '-9999' in c_bm.missing_data_codes,
            'time': {
                'column_name': config.time_col,
                'converter': lambda x: datetime_converter(x, datetime_col=c_bm.datetime_col,
                                                          datetime_formats=c_bm.try_datetime_formats)
            },
            'repair_time': c_bm.repair_time,
        }
        data_meteo = load_biomet(bg_bm_config, data_freq)
    else:
        data_meteo = None
        
    print("Колонки в FullOutput \n", df.columns.to_list())
    if has_meteo:
        print("Колонки в метео \n", data_meteo.columns.to_list())

    # merge into common DataFrame
    if has_meteo:
        df = df.join(data_meteo, how='outer', rsuffix='_meteo')
        df[time_col] = df.index
        df = bg.repair_time(df, time_col)
        if df[data_meteo.columns[-1]].isna().sum() == len(df.index):
            print("Bad meteo df range, skipping! Setting config_meteo ['use_biomet']=False")
            has_meteo = False

    # reddyproc requires 3 months
    if config.debug:
        df = df[0: min(31*3 * 24*2, len(df))]

    biomet_columns = []
    if has_meteo:
        biomet_columns = data_meteo.columns.str.lower()

    return df, time_col, biomet_columns, data_freq, has_meteo
