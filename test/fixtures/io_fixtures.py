# To use same dir on each test by default, edit:
# PyCharm -> pytest default template -> Additional pytest options:
# -s -p no:warnings --basetemp=${TEMP}\pytest
import glob
import os
import shutil
import tempfile
from pathlib import Path
import pytest

'''
@pytest.mark.usefixtures('tmp_path')
@pytest.fixture
def use_fixture_path(tmp_path: Path, src_path: Path, masks: list[str] = None):
    assert(src_path.exists())
    if masks is None:
        masks = ['*.*']
    
    for m in masks:
        for fpath in glob.glob(str(src_path / m)):            
            shutil.copy(fpath, tmp_path)
            print(f'Using {fpath} in {tmp_path}')
            
    # shutil.copytree(src_path, tmp_path, dirs_exist_ok=True)
    # print('Path before test',  Path().resolve())
    # with cwd(tmp_path):
    #     print('Path during test', Path().resolve())
    yield tmp_path
'''
