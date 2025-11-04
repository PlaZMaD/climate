import logging
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from src.config.config_types import ImportMode, InputFileType, ColabDemoMixPolicy
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
    
    last_ver = 'v1.0.4'
    default_fpath = Path(f'misc/config_{last_ver}_default_ru.yaml')
    disabled_physical_filters_path = Path(f'misc/config_{last_ver}_disabled_physical_filters.yaml')
    
    # if ipynb validation after construct works
    config = FFConfig.load_or_init(load_path=None, default_fpath=default_fpath,
                                   init_debug=False, init_version=last_ver)
    config.data_import.input_files = {'file_name': InputFileType.EDDYPRO_FO}
    with pytest.raises(Exception, match='EDDYPRO_FO'):
        config.data_import.input_files = {'file_name2': 'incorrect_file_type'}
    with pytest.raises(Exception, match='string'):
        config.version = 9

    # if auto-creation of missing filters works
    load_path = 'misc/config_v1.0.4_disabled_filters.yaml'
    yaml_dict = FFConfig.get_yaml_io().load(Path(load_path).read_text())
    assert yaml_dict['filters']['meteo'] is None
    config = FFConfig.load_or_init(load_path=load_path, default_fpath=default_fpath,
                                   init_debug=False, init_version=last_ver)
    assert config.filters.meteo == {}
    
    # if works and auto replaced on save
    config = FFConfig.load_or_init(load_path=disabled_physical_filters_path, default_fpath=default_fpath,
                                   init_debug=False, init_version=last_ver)
    config.data_import.eddypro_fo.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.filters.quantile = {'ok': 'ok'}  
    config.filters.man_ranges = [('test1', 'test2')]
    config.reddyproc.partitioning_methods = ['Lasslop10']
    config.data_import.input_files = ['ya_ckd_FO_2015_test.csv', 'ya_ckd_biomet_2015.csv']
    config.data_import.import_mode = ImportMode.CSF_AND_BIOMET
    config.calc.calc_with_strg = True    
    config.filters.qc['h'] = 2
    config.filters.qc['le'] = 3            
    FFConfig.save(config, tmp_path / 'test2.yaml', add_comments=True)
    test_config = FFConfig.load_or_init(tmp_path / 'test2.yaml', default_fpath=default_fpath,
                                        init_debug=False, init_version=last_ver)   
    assert test_config.data_import.import_mode == ImportMode.AUTO
    assert test_config.filters.qc['le'] == 3 
    
    # os_view_path(tmp_path)


@pytest.mark.usefixtures('tmp_path')
def test_config_backwards_compatibility(tmp_path):
    init_logging(level=logging.INFO, fpath=tmp_path / 'log.log', to_stdout=True)
    
    test_ver = 'v1.0.5'
    default_fpath = Path(f'misc/config_{test_ver}_default_ru.yaml')
    old_fpath = Path(f'test/fixtures/test_config/config_v1.0.4_default_ru.yaml')
    
    # if v1.0.4 loads normally
    config = FFConfig.load_or_init(load_path=old_fpath, default_fpath=default_fpath,
                                   init_debug=False, init_version=test_ver)
    
    assert config.data_import.mixed_demo_policy == ColabDemoMixPolicy.AUTO_DELETE_DEMO
    
    assert True
    
    # os_view_path(tmp_path)
