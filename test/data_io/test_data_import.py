import shutil
from pathlib import Path

import pytest

import src.helpers.os_helpers  # noqa: F401
from src.data_io.data_import import import_data
from src.data_io.data_import_modes import ImportMode
from src.data_io.detect_import import try_auto_detect_input_files, AutoImportException
from src.ff_config import FFConfig, FFGlobals
from src.ff_logger import init_logging
from test.test_config import os_view_path


# TODO 2 generate or period test data, allow data_chunks in gitignore


@pytest.mark.usefixtures('tmp_path')
def test_auto_detect_input_files(tmp_path):
    init_logging(to_stdout=False)
    
    gl = FFGlobals.model_construct()
    gl.input_dir = tmp_path
    
    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    config.site_name = 'auto'
    config.ias_out_version = 'auto'
    
    with pytest.raises(AutoImportException, match='No import modes possible'):
        try_auto_detect_input_files(config, gl)

    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    config.site_name = 'auto'
    config.ias_out_version = 'auto'

    shutil.copy('test/fixtures/data_chunks/CSF_tv_fy4_2024.xlsx', tmp_path)
    shutil.copy('test/fixtures/data_chunks/Biomet_tv_fy4_2023.csv', tmp_path)
    
    input_files, import_mode, site_name, ias_out_version, has_meteo = try_auto_detect_input_files(config, gl)
    # data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)
    assert import_mode == ImportMode.CSF_AND_BIOMET
    
    # os_view_path(tmp_path)
    assert True


@pytest.mark.usefixtures('tmp_path')
def test_input_merge(tmp_path):
    init_logging(to_stdout=False)
    
    gl = FFGlobals.model_construct()
    gl.input_dir = tmp_path
      
    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    config.site_name = 'auto'
    
    config.ias_out_version = 'auto'
    config.ias.skip_validation = True
    config.ias.repair_time = True
    config.ias.missing_data_codes = []
    
    config.time_col = 'datetime'
    
    # TODO 2 add both overlap and gap for ias
    shutil.copy('test/fixtures/data_chunks/tv_fy4_2017_v01.csv', tmp_path)
    shutil.copy('test/fixtures/data_chunks/tv_fy4_2015_v01.xlsx', tmp_path)
    shutil.copy('test/fixtures/data_chunks/tv_fy4_2024_v01.xlsx', tmp_path)
    
    input_files, import_mode, site_name, ias_out_version, has_meteo = try_auto_detect_input_files(config, gl)
    assert import_mode == ImportMode.IAS
    data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)
    
    # TODO 2 add both overlap and gap for csf + biomet
    
    # os_view_path(tmp_path)
    assert True

