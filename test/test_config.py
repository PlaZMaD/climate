import logging
import os
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from src.data_io.data_import_modes import ImportMode
from src.ffconfig import FFConfig
from src.helpers.config_io import ConfigStoreMode
from src.helpers.py_helpers import init_logging


def os_view_path(filename):
    try:
        os.startfile(filename)
    except:
        subprocess.Popen(['xdg-open', filename])


@pytest.mark.usefixtures('tmp_path')
def test_config_io(tmp_path):
    init_logging(level=logging.INFO, fpath=tmp_path / 'log.log', to_stdout=True)

    # load defaults
    repo_dir = Path('.')
    FFConfig.load_or_init(load_path='auto', repo_dir=repo_dir, init_debug=False, init_version='1.0')
    
    # use defaults for test, only other way to have save load is to fill all values
    config = FFConfig.model_validate(FFConfig._default_model_values)
    FFConfig.save(config, tmp_path / 'config_default_all.yaml', mode=ConfigStoreMode.ALL_OPTIONS)
    FFConfig.save(config, tmp_path / 'config_default_changes.yaml', mode=ConfigStoreMode.ONLY_CHANGES)
    
    config._enable_tracking = True
    # config._load_path = 'some'
    config.reddyproc._enable_tracking = True

    config.eddypro_fo.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.eddypro_fo._load_path = 'locking_any_changes'
    config.eddypro_fo._enable_tracking = True
    config.eddypro_fo.try_date_formats = ['%d.%m.%Y']

    config.filters.quantile = {'ok': 'ok'}
    config.filters._enable_tracking = True
    config.filters.quantile = {'ok2': 'ok2'}

    config.filters.man_ranges = [('test1', 'test2')]
    
    config.reddyproc.partitioning_methods = ['Reichstein05']
    config.reddyproc.partitioning_methods = ['Lasslop10']
    config.input_files = ['ya_ckd_FO_2015_test.csv', 'ya_ckd_biomet_2015.csv']
    config.import_mode = ImportMode.AUTO
    config.import_mode = ImportMode.CSF_AND_BIOMET
    config.calc_with_strg = True

    config.qc['h'] = 0
    config.qc['le'] = 0
    config.qc['co2_flux'] = 0
    config.qc['ch4_flux'] = 0
    
    config.qc = {'should': 'work'}
    config.qc = {'should': 'not work'}
    
    # disable of revert to the first value (i.e. when config value was changed on runtime like auto or fallback err)
    del config._starting_values['input_files']

    FFConfig.save(config, tmp_path / 'test_all.yaml', mode=ConfigStoreMode.ALL_OPTIONS)
    FFConfig.save(config, tmp_path / 'test.yaml', mode=ConfigStoreMode.ONLY_CHANGES)

    test_config = FFConfig.load_or_init(tmp_path / 'test.yaml', repo_dir=repo_dir,
                                        init_debug=None, init_version=None)
    test_config._load_path = None

    assert test_config.import_mode == ImportMode.AUTO
    assert test_config.input_files == ['ya_ckd_FO_2015_test.csv', 'ya_ckd_biomet_2015.csv']
    # assert test_config.reddyproc.partitioning_methods == ["Reichstein05"]

    config2 = FFConfig.load_or_init(load_path=None, repo_dir=repo_dir, init_debug=False, init_version='1.0')
    config2.filters._enable_tracking = True
    config2.filters.man_ranges = [('r1', 'r2'), ('r3', 'r4')]
    config2.filters.man_ranges = [('r0', 'r0')]
    assert config2.filters.man_ranges == [('r0', 'r0')]
    config2.filters.restore_starting_values()
    assert config2.filters.man_ranges == [('r1', 'r2'), ('r3', 'r4')]
    
    os_view_path(tmp_path)
