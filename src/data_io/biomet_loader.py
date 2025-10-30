from bglabutils import basic as bg
from src.ff_logger import ff_logger


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
