from bglabutils import basic as bg
from src.config.ff_config import MergedDateTimeFileConfig
from src.data_io.utils.time_series_utils import datetime_parser
from src.ff_logger import ff_logger


# TODO 1 support biomet ~ with separate time date cols 


def load_biomet(config_meteo, data_freq):
    print("Проверяем корректность временных меток. Убираем повторы, дополняем пропуски. "
          "На случай загрузки нескольких файлов. При загрузке одного делается автоматически.")
    
    data_meteo, time_meteo = bg.load_df(config_meteo)
    data_meteo = data_meteo[next(iter(data_meteo))]  # т.к. изначально у нас словарь
    
    meteo_freq = data_meteo.index.freq
    print("Диапазон времени метео: ", data_meteo.index[[0, -1]])
    ff_logger.info(f"MeteoData loaded from {config_meteo['path']}")
    ff_logger.info("Time range for meteo: " + " - ".join(data_meteo.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    
    if data_freq != meteo_freq:
        print("Resampling meteo data")
        ff_logger.info(f"Resampling meteo data")
        data_meteo = data_meteo.asfreq(data_freq)
    
    return data_meteo


def load_biomets(bm_paths, tgt_time_col, data_freq, c_bm: MergedDateTimeFileConfig):
    if len(bm_paths) == 0:
        return None, False
    
    bg_bm_config = {
        'path': bm_paths,
        # reddyproc requires 90 days, cut moved to the end of this function
        'debug': False,
        '-9999_to_nan': -9999 in c_bm.missing_data_codes,
        'time': {
            'column_name': tgt_time_col,
            'converter': lambda x: datetime_parser(x, c_bm.datetime_col, c_bm.try_datetime_formats)
        },
        'repair_time': c_bm.repair_time,
    }
    dfs = load_biomet(bg_bm_config, data_freq)
    ff_logger.info('Колонки в метео \n'
                   f'{dfs.columns.values}')
            
    return dfs, True

