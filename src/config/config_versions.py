from src.ff_logger import ff_logger


def update_config_version(config: dict, need_ver) -> dict:
    if 'version' not in config:
        raise Exception('Unexpected config contents.')
    else:
        ver = config['version'] 
    
    if ver == need_ver:
        return config
    else:
        ff_logger.warning(f'Config version will be updated from {ver} to {need_ver}. \n' 
                          'Please verify new options by comparing new version in the outputs with your version.')
    
    if ver == '1.0.2':
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
    else:
        raise NotImplementedError(
            f'Current config version: {need_ver} does not match loaded version: {ver}. \n'
            f'Backwards compatibility for {ver} is not supported. \n'
            f'Please use default {need_ver} config and update it manually.')
    
    return config
