import logging

import bglabutils.basic as bg
from src.data_io.data_import_modes import ImportMode, InputFileType
from src.ffconfig import FFConfig
from src.helpers.py_helpers import ensure_list


def load_biomet(config_meteo, data_freq):
    print("Проверяем корректность временных меток. Убираем повторы, дополняем пропуски. "
          "На случай загрузки нескольких файлов. При загрузке одного делается автоматически.")

    data_meteo, time_meteo = bg.load_df(config_meteo)
    data_meteo = data_meteo[next(iter(data_meteo))]  # т.к. изначально у нас словарь

    meteo_freq = data_meteo.index.freq
    print("Диапазон времени метео: ", data_meteo.index[[0, -1]])
    logging.info(f"MeteoData loaded from {config_meteo['path']}")
    logging.info("Time range for meteo: " + " - ".join(data_meteo.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

    if data_freq != meteo_freq:
        print("Resampling meteo data")
        logging.info(f"Resampling meteo data")
        data_meteo = data_meteo.asfreq(data_freq)

    return data_meteo


def load_eddypro(config: FFConfig):
    c_fo = config.eddypro_fo
    c_bm = config.eddypro_biomet
    fo_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_FO]
    bm_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET]

    # load of eddypro = full_output, optionally with biomet
    if set(c_fo.missing_data_codes) != {'-9999'}:
        raise NotImplementedError(f"Not yet supported missing codes: {c_fo.missing_data_codes}")

    bg_fo_config = {
        'path': fo_paths,
        'debug': config.debug,
        '-9999_to_nan': '-9999' in c_fo.missing_data_codes,
        'time': {'column_name': config.time_col, 'converter': c_fo.time_converter},
        'repair_time': c_fo.repair_time,
    }
    df, time_col = bg.load_df(bg_fo_config)
    df = df[next(iter(df))]  # т.к. изначально у нас словарь
    data_freq = df.index.freq

    print("Диапазон времени full_output: ", df.index[[0, -1]])
    logging.info("Time range for full_output: " + " - ".join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

    has_meteo = (config.import_mode == ImportMode.EDDYPRO_FO_AND_BIOMET)
    if has_meteo:
        bg_bm_config = {
            'path': bm_paths,
            'debug': config.debug,
            '-9999_to_nan': '-9999' in c_bm.missing_data_codes,
            'time': {'column_name': config.time_col, 'converter': c_bm.time_converter},
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

    biomet_columns = []
    if has_meteo:
        biomet_columns = data_meteo.columns.str.lower()

    return df, time_col, biomet_columns, data_freq, has_meteo
