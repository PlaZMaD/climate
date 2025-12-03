from bglabutils import basic as bg
from src.config.config_types import InputFileType
from src.config.ff_config import ImportConfig
from src.data_io.biomet_loader_todel import load_biomets_todel
from src.data_io.time_series_loader import merge_time_series_biomet
from src.data_io.utils.time_series_utils import date_time_parser
from src.ff_logger import ff_logger
from src.helpers.env_helpers import ENV


def load_eddypro_via_bgl_todel(cfg_import: ImportConfig):
    c_fo = cfg_import.eddypro_fo
    
    fo_paths = [str(fpath) for fpath, ftype in cfg_import.input_files.items() if ftype == InputFileType.EDDYPRO_FO]
    
    # load of eddypro = full_output, optionally with biomet
    if not set(c_fo.missing_data_codes) <= {-9999}:
        raise NotImplementedError(f'Changing missing_data_codes is not yet supported')
    
    bg_fo_config = {
        'path': fo_paths,
        # reddyproc requires 90 days, cut moved to the end of this function
        'debug': False,
        '-9999_to_nan': -9999 in c_fo.missing_data_codes,
        'time': {
            'column_name': cfg_import.time_col,
            'converter': lambda x: date_time_parser(x, c_fo.time_col, c_fo.try_time_formats,
                                                       c_fo.date_col, c_fo.try_date_formats)
        },
        'repair_time': c_fo.repair_time,
    }
    df_fo, time_col = bg.load_df(bg_fo_config)
    df_fo = df_fo[next(iter(df_fo))]  # т.к. изначально у нас словарь
    data_freq = df_fo.index.freq
    
    print('Диапазон времени full_output: ', df_fo.index[[0, -1]])
    ff_logger.info('Time range for full_output: ' + ' - '.join(df_fo.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    ff_logger.info('Колонки в FullOutput \n'
                   f'{df_fo.columns.values}')

    bm_paths = [str(fpath) for fpath, ftype in cfg_import.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET]
    df_bm, has_meteo = load_biomets_todel(bm_paths, cfg_import.time_col, data_freq, cfg_import.eddypro_biomet)
      
    if has_meteo:
        df = df_fo.join(df_bm, how='outer', rsuffix='_meteo')
        df[time_col] = df.index
        df = bg.repair_time(df, time_col)
        if df[df_bm.columns[-1]].isna().sum() == len(df.index):
            ff_logger.info('Bad meteo df_fo range, overriding option has_meteo to False')
            has_meteo = False
    else:
        df = df_fo

    if ENV.LOCAL and has_meteo:        
        # TODO 2 finish the safe switch to merge_time_series_biomet and then to just abstract merge
        # TODO 1 something is off under {"nik_biomet": 'EDDYPRO_BIOMET', 'nik_full_output': 'EDDYPRO_FO'}        
        df_test_merge_nly, has_meteo_test = merge_time_series_biomet(df_fo, df_bm, time_col)
        assert has_meteo == has_meteo_test
        assert len(df_test_merge_nly.compare(df)) == 0
            
    biomet_columns = []
    if has_meteo:
        biomet_columns = df_bm.columns.str.lower()
    
    return df, time_col, biomet_columns, data_freq, has_meteo
