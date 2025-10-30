import shutil
from pathlib import Path

import pytest

import src.helpers.os_helpers  # noqa: F401
from src.data_io import ias_io
from src.data_io.data_import import import_data
from src.config.config_types import ImportMode
from src.data_io.detect_import import try_auto_detect_input_files, AutoImportException
from src.config.ff_config import FFConfig, FFGlobals
from src.ff_logger import init_logging
from src.helpers.io_helpers import ensure_empty_dir

# TODO 2 generate or period test data, allow data_chunks in gitignore
TEST_DATA_CHUNKS_DIR = 'test/fixtures/data_chunks'


def prepare_import_test_data(test_dir: str | Path, fnames: list[str], src_dir: str = TEST_DATA_CHUNKS_DIR):
    ensure_empty_dir(test_dir)
    for fname in fnames:
        shutil.copy(Path(src_dir) / fname, test_dir)


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
    config.ias_out_fname_ver_suffix = 'auto'
    
    with pytest.raises(AutoImportException, match='No import modes possible'):
        try_auto_detect_input_files(config, gl)
    
    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    config.site_name = 'auto'
    config.ias_out_fname_ver_suffix = 'auto'
    
    prepare_import_test_data(tmp_path, ['CSF_tv_fy4_2024.xlsx', 'Biomet_tv_fy4_2023.csv'])
    
    input_files, import_mode, site_name, ias_out_version, has_meteo = try_auto_detect_input_files(config, gl)
    # data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)
    assert import_mode == ImportMode.CSF_AND_BIOMET
    
    # os_view_path(tmp_path)
    assert True


@pytest.mark.usefixtures('tmp_path')
def test_fo_import(tmp_path):
    init_logging(to_stdout=False)
    
    gl = FFGlobals.model_construct()
    gl.input_dir = tmp_path
    
    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    
    config.site_name = 'auto'
    config.ias_out_fname_ver_suffix = 'auto'
    
    config.eddypro_fo.missing_data_codes = [-9999]
    config.eddypro_fo.date_col = 'date'
    config.eddypro_fo.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.eddypro_fo.time_col = 'time'
    config.eddypro_fo.try_time_formats = ['%H:%M', '%H:%M:%S']
    config.eddypro_fo.repair_time = True
    
    config.eddypro_biomet.missing_data_codes = [-9999]
    config.eddypro_biomet.datetime_col = 'TIMESTAMP_1'
    config.eddypro_biomet.try_datetime_formats = ['%Y-%m-%d %H%M', '%d.%m.%Y %H:%M']  # yyyy-mm-dd HHMM
    config.eddypro_biomet.repair_time = True
    
    config.time_col = 'datetime'
    
    prepare_import_test_data(tmp_path, ['eddy_pro tv_fy4_2023_broken.csv'])
    
    _, import_mode, _, _, _ = try_auto_detect_input_files(config, gl)
    assert import_mode == ImportMode.EDDYPRO_FO
    with pytest.raises(Exception, match='None of date or time formats worked'):
        import_data(config)
    
    # TODO 3 something is broken on time repair operation, but it's in bglautils
    '''
    ensure_empty_dir(tmp_path)
    prepare_import_test_data(tmp_path, ['eddy_pro tv_fy4_2023.csv'])
    
    config.input_files = 'auto'
    res = try_auto_detect_input_files(config, gl)
    config.input_files, config.import_mode, config.site_name, config.ias_out_version, config.has_meteo = res
    data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)
    '''
    
    # os_view_path(tmp_path)
    assert True


@pytest.mark.usefixtures('tmp_path')
def test_ias_import(tmp_path):
    init_logging(to_stdout=False)
    
    gl = FFGlobals.model_construct()
    gl.input_dir = tmp_path
    
    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    
    config.site_name = 'auto'
    config.ias_out_fname_ver_suffix = 'auto'
    
    config.ias.skip_validation = True
    config.ias.missing_data_codes = [-9999]
    config.ias.datetime_col = 'TIMESTAMP_START'
    config.ias.try_datetime_formats = '%Y%m%d%H%M'
    config.ias.repair_time = True
    
    config.time_col = 'datetime'
    # TODO 1 VPD_PI_1_1_1 not rename in import?
    # TODO 2 ias test: both overlap and gap for ias
    prepare_import_test_data(tmp_path, ['tv_fy4_2024_v01.xlsx', 'tv_fy4_2022_1.csv', 'tv_fy4_2022_2.xlsx'])
    
    _, import_mode, _, _, _ = try_auto_detect_input_files(config, gl)
    assert import_mode == ImportMode.IAS
    # with pytest.raises(Exception, match='None of date or time formats worked'):
    ias_io.COLS_IAS_TIME = []
    data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)
    
    # os_view_path(tmp_path)
    assert True


@pytest.mark.usefixtures('tmp_path')
def test_csf_input(tmp_path):
    init_logging(to_stdout=False)
    
    gl = FFGlobals.model_construct()
    gl.input_dir = tmp_path
    
    config = FFConfig.model_construct()
    config.import_mode = ImportMode.AUTO
    config.input_files = 'auto'
    config.has_meteo = True
    
    config.site_name = 'auto'
    config.ias_out_fname_ver_suffix = 'auto'
    
    config.csf.missing_data_codes = [-9999, 'NAN']
    config.csf.datetime_col = 'TIMESTAMP'
    config.csf.try_datetime_formats = ['%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']  # yyyy-mm-dd HHMM
    config.csf.repair_time = True
    
    config.time_col = 'datetime'

    # TODO 2 add both overlap and gap for csf + biomet
    prepare_import_test_data(tmp_path, [])
    
    input_files, import_mode, site_name, ias_out_version, has_meteo = try_auto_detect_input_files(config, gl)
    assert import_mode == ImportMode.CSF_AND_BIOMET
    data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)
    
    # os_view_path(tmp_path)
    assert True