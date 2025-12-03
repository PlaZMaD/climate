from src.config.config_types import ColabDemoMixPolicy
from src.ff_logger import ff_logger


def update_config_version(config: dict, tgt_ver) -> dict:
    if 'version' not in config:
        raise Exception('Unexpected config contents.')
    else:
        src_ver = config['version'] 
    
    if src_ver == tgt_ver:
        return config
    
    if config['version'] == '1.0.2':
        config = dict(config)
        config['data_import'] = {
            'input_files': config['input_files'],
            'eddypro_fo': config['eddypro_fo'],
            'eddypro_biomet': config['eddypro_biomet'],
            'ias': config['ias'],
            'csf': config['csf'],
            'import_mode': config['import_mode'],
            'time_col': config['time_col']
        }        
        del config['input_files']
        del config['eddypro_fo']
        del config['eddypro_biomet']
        del config['ias']
        del config['csf']
        del config['import_mode']
        del config['time_col']
        
        config['data_import']['ias']['datetime_col'] = 'TIMESTAMP_START'
        config['data_import']['ias']['try_datetime_formats'] = '%Y%m%d%H%M'
        config['data_import']['ias']['skip_validation'] = False
        config['data_import']['csf']['empty_co2_strg'] = True
        
        config['data_export'] = {
            'ias': {
                'out_fname_ver_suffix': config['ias_out_version'], 
                'split_intervals': 'YEAR'
        }
        }
        del config['ias_out_version']
        
        config['metadata'] = {
            'site_name': config['site_name']
        }
        del config['site_name']
        
        config['filters']['qc'] = config['qc']
        del config['qc']

        config['calc'] = {
            'has_meteo': config['has_meteo'],
            'calc_nee': config['calc_nee'],
            'calc_with_strg': config['calc_with_strg']
        }
        del config['has_meteo']
        del config['calc_nee']
        del config['calc_with_strg']
        
        config['version'] = '1.0.4'
    
    if config['version'] == '1.0.4':
        config['data_import']['mixed_demo_policy'] = ColabDemoMixPolicy.AUTO_DELETE_DEMO
        config['version'] = 'v1.0.5'
        
    if config['version'] != tgt_ver:
        raise NotImplementedError(
            f'Current config version: {tgt_ver} does not match loaded version: {src_ver}. \n'
            f'Backwards compatibility for {src_ver} is not supported. \n'
            f'Please use default {tgt_ver} config and update it manually.')
    else:
        ff_logger.warning(f'Config version was updated from {src_ver} to {tgt_ver}. \n'
                          f'Review new options by comparing your version to the new version from the outputs.')
    
    return config
