import logging
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from src.config.config_types import ImportMode
from src.config.ff_config import FFConfig
from src.ff_logger import init_logging


def os_view_path(fpath):
    try:
        os.startfile(fpath)
    except:
        subprocess.Popen(['xdg-open', fpath])


@pytest.mark.usefixtures('tmp_path')
def test_config_io(tmp_path):
    init_logging(level=logging.INFO, fpath=tmp_path / 'log.log', to_stdout=True)
    
    # load_path = 'misc/config_v1.0.4_all_filters_deleted.yaml'
    load_path = 'auto'
    config = FFConfig.load_or_init(load_path=load_path,
                                   default_fpath=Path('misc/config_v1.0.4_default.yaml'),
                                   init_debug=False, init_version='1.0.4')
    
    FFConfig.save(config, tmp_path / 'after_load.yaml', add_comments=True)
    with open(tmp_path / 'after_load.yaml', 'r') as fl:
        file_txt = fl.read()
        yaml = FFConfig.get_yaml() 
        loaded_yaml = yaml.load(file_txt)
    
    loaded_yaml['filters']['meteo'] = None
    test_model = FFConfig.model_validate(loaded_yaml)
    
    # test for basic definition errors
    config.model_dump(mode='json')
    
    config._enable_tracking = True
    # config._load_path = 'some'
    config.reddyproc._enable_tracking = True
    
    config.data_import.eddypro_fo.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.data_import.eddypro_fo._load_path = 'locking_any_changes'
    config.data_import.eddypro_fo._enable_tracking = True
    config.data_import.eddypro_fo.try_date_formats = ['%d.%m.%Y']
    
    config.filters.quantile = {'ok': 'ok'}
    config.filters._enable_tracking = True
    config.filters.quantile = {'ok2': 'ok2'}
    
    config.filters.man_ranges = [('test1', 'test2')]
    
    config.reddyproc.partitioning_methods = ['Reichstein05']
    config.reddyproc.partitioning_methods = ['Lasslop10']
    config.data_import.input_files = ['ya_ckd_FO_2015_test.csv', 'ya_ckd_biomet_2015.csv']
    config.data_import.import_mode = ImportMode.AUTO
    config.data_import.import_mode = ImportMode.CSF_AND_BIOMET
    config.calc.calc_with_strg = True
    
    config.filters.qc = {}
    config.filters.qc['h'] = 0
    config.filters.qc['le'] = 0
    config.filters.qc['co2_flux'] = 0
    config.filters.qc['ch4_flux'] = 0
    
    config.filters.qc = {'should': 'work'}
    config.filters.qc = {'test3': 'test2'}
        
    FFConfig.save(config, tmp_path / 'test_all.yaml', add_comments=True)
    
    test_config = FFConfig.load_or_init(tmp_path / 'test_all.yaml',
                                        default_fpath=Path('misc/config_v1.0.4_default.yaml'),
                                        init_debug=False, init_version='1.0.4')
    test_config._load_path = None
    
    assert test_config.data_import.import_mode == ImportMode.AUTO
    assert test_config.filters.qc['test3'] == 'test2' 
    
    os_view_path(tmp_path)
