import warnings
from os import chdir
from pathlib import Path
from sys import path as sys_paths

"""
 This module is intended to be imported before all other user modules.
 ch_project_root_dir() allows to keep consistent imports root (from src.** import) when runnning from different dirs: 
    cmd: */run_main.bat, py: ./main.py, py tests: ./test/test_main.py, etc

 Import with autorun of declared functions without warning:
 from src.helpers import os_helpers  # noqa: F401
"""


def ch_project_root_dir():
    this_file_path = Path(__file__).parent
    assert this_file_path.name == 'helpers'

    src_dir = this_file_path.parent
    assert src_dir.name == 'src'

    project_dir = str(src_dir.parent)
    src_dir = str(src_dir)

    if src_dir in sys_paths:
        # ambigious imports can be broken
        sys_paths.remove(src_dir)
    if src_dir in sys_paths:
        # ambigious imports can be broken, dupe remove is nessesary somethimes
        sys_paths.remove(src_dir)
    assert src_dir not in sys_paths

    if project_dir not in sys_paths:
        sys_paths.append(project_dir)

    chdir(project_dir)
    print(f'Workaround for R lang "source" command: current dir is changed to {project_dir}.\n')


def set_simple_user_warnings():
    # TODO 3 possibly unused; to logging instead?

    default_show_warning = warnings.showwarning

    # logging.captureWarnings(True)
    # not used yet - replaced with logging.warning for ipynb

    def custom_show_warning(message, category, filename, lineno, file=None, line=None):
        if category != UserWarning:
            default_show_warning(message, category, filename, lineno, file, line)

        # print(f'{filename}: {lineno} \n WARNING: {message}')
        print(f'WARNING: {message}')

    warnings.showwarning = custom_show_warning
    warnings.simplefilter('always', category=UserWarning)


set_simple_user_warnings()
ch_project_root_dir()
