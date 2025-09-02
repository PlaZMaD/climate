import logging
import os
import subprocess
from copy import copy
from pathlib import Path

import pytest

from src.ffconfig import FFConfig
from src.helpers.config_io import ConfigStoreMode
from src.helpers.py_helpers import init_logging


def os_view_path(path):
    # subprocess.Popen(r'explorer /select,"' + name + '"')
    dir_path = os.path.abspath(path)
    full_path = r'explorer /select,"' + dir_path + '"'
    subprocess.Popen(full_path)


@pytest.mark.usefixtures('tmp_path')
def test_save_basemodel(tmp_path):
    init_logging(level=logging.INFO, fpath=tmp_path / 'log.log', to_stdout=True)

    repo_dir = Path('.')
    default_config = FFConfig.load('auto', repo_dir=repo_dir)
    default_config._load_path = None

    config = copy(default_config)
    config.reddyproc.partitioning_methods = ["Reichstein05"]

    config.save(tmp_path / 'test_all.yaml', mode=ConfigStoreMode.ALL_OPTIONS)
    config.save(tmp_path / 'test.yaml', mode=ConfigStoreMode.ONLY_CHANGES)
    os_view_path(tmp_path)
