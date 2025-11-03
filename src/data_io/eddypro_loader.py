import bglabutils.basic as bg
from src.data_io.biomet_loader import load_biomet
from src.data_io.utils.time_series_utils import datetime_parser, date_time_parser
from src.ff_logger import ff_logger
from src.config.config_types import ImportMode, InputFileType, DEBUG_NROWS
from src.config.ff_config import FFConfig, MergedDateTimeFileConfig


# TODO 1 in the ipynb, u_star is not yet renamed at the next line?
# cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength',
# ppfd_in_1_1_1 will be renamed to ppfd_1_1_1, 


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


# TODO 1 some renames in the main script are specific to eddypro/biomet files and should not be part of main script anymore?
# if moved, check ias import-export handling stands (or solve with generalised col names preprocess check?)
def load_eddypro(config: FFConfig):
    c_fo = config.eddypro_fo
    
    fo_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_FO]
    
    # load of eddypro = full_output, optionally with biomet
    if not set(c_fo.missing_data_codes) <= {-9999}:
        raise NotImplementedError(f'Changing missing_data_codes is not yet supported')
    
    bg_fo_config = {
        'path': fo_paths,
        # reddyproc requires 90 days, cut moved to the end of this function
        'debug': False,
        '-9999_to_nan': -9999 in c_fo.missing_data_codes,
        'time': {
            'column_name': config.time_col,
            'converter': lambda x: date_time_parser(x, c_fo.time_col, c_fo.try_time_formats,
                                                       c_fo.date_col, c_fo.try_date_formats)
        },
        'repair_time': c_fo.repair_time,
    }
    df, time_col = bg.load_df(bg_fo_config)
    df = df[next(iter(df))]  # т.к. изначально у нас словарь
    data_freq = df.index.freq
    
    print('Диапазон времени full_output: ', df.index[[0, -1]])
    ff_logger.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    ff_logger.info('Колонки в FullOutput \n'
                   f'{df.columns.values}')

    bm_paths = [str(fpath) for fpath, ftype in config.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET]
    data_meteo, has_meteo = load_biomets(bm_paths, config.time_col, data_freq, config.eddypro_biomet)
    
    # TODO 3 switch to common time series merge from utils
    # merge into common DataFrame
    if has_meteo:
        df = df.join(data_meteo, how='outer', rsuffix='_meteo')
        df[time_col] = df.index
        df = bg.repair_time(df, time_col)
        if df[data_meteo.columns[-1]].isna().sum() == len(df.index):
            ff_logger.info('Bad meteo df range, overriding option has_meteo to False')
            has_meteo = False
    
    # reddyproc requires 3 months
    if config.debug and DEBUG_NROWS:
        df = df[0: min(DEBUG_NROWS, len(df))]
    
    biomet_columns = []
    if has_meteo:
        biomet_columns = data_meteo.columns.str.lower()
    
    return df, time_col, biomet_columns, data_freq, has_meteo
