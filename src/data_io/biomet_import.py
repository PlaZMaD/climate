
from src.config.config_types import InputFileType
from src.config.ff_config import ImportConfig
from src.data_io.biomet_loader_todel import load_biomets_todel
from src.data_io.time_series_loader import preload_time_series
from src.data_io.utils.time_series_utils import repair_time, merge_time_series
from src.ff_logger import ff_logger
from src.helpers.env_helpers import ENV


# TODO 1 support biomet ~ with separate time date cols 

def import_biomets(cfg_import: ImportConfig):  
    dfs_bm = {fpath.name: preload_time_series(fpath, ftype, cfg_import)
              for fpath, ftype in cfg_import.input_files.items() if ftype == InputFileType.EDDYPRO_BIOMET}
    
    for fpath, df in dfs_bm.items():
        # TODO 2 extract FO specific renames
        # df = regex_fix_col_names(df, COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES)
        # check_csf_col_names(df)
        # df = import_rename_csf_cols(df, cfg_import.time_col)
        if cfg_import.eddypro_biomet.repair_time:
            df = repair_time(df, cfg_import.time_col, fill_gaps=False)
        dfs_bm[fpath] = df
    
    if len(dfs_bm) > 1:
        ff_logger.info('Merging data from files...')
    
        df, has_meteo = merge_time_series(dfs_bm, cfg_import.time_col)
    else:
        df, has_meteo = next(iter(dfs_bm.values())), True
        
    print('Диапазон времени Biomet (START): ', df.index[[0, -1]])
    ff_logger.info('Time range: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
    ff_logger.info('Колонки в Biomet \n'
                   f'{df.columns.values}')

    if ENV.LOCAL:    
        data_freq = df.index.freq
        bm_paths = [str(fpath) for fpath, ftype in cfg_import.input_files.items() if
                    ftype == InputFileType.EDDYPRO_BIOMET]
        df_check, has_meteo_check = load_biomets_todel(bm_paths, cfg_import.time_col, data_freq, cfg_import.eddypro_biomet)
        assert has_meteo == has_meteo_check
        
        df.rename(columns={'TIMESTAMP_1_STR': 'TIMESTAMP_1'}, inplace=True)
        assert (df_check.columns == df.columns).all()
        
        check_same = df.compare(df_check) 
        assert len(check_same) == 0

    return df, has_meteo

