"""
Module specifically for Google Colab.
During local runs, all functions here are to be mocked or cancelled.
"""
from enum import Enum
from pathlib import Path

from src.config.config_types import ColabDemoMixPolicy
from src.ff_logger import ff_logger
from src.data_io.detect_import import get_supported_data_files
from src.helpers.env_helpers import colab_only, ENV
from src.helpers.py_collections import format_dict

# TODO 1 repair replacing auto in colab 
# TODO 1 import in colab directly after specifying data)import config
# TODO 1 import statistical distributions check vs default data

# TODO 3 %autoreload stopped to work in colab, any replacement?
DEMO_DATA_FILE_SIZES = {'eddy_pro_full output_Fy4_2023_demo.csv': 14948833, 'BiometFy4_2023_demo.csv': 1216730}

if ENV.COLAB:
    from google.colab import output
    from google.colab import files
    from IPython.display import display
    from IPython.core.display import Javascript


class _StopExecution(Exception):
    def _render_traceback_(self):
        return ['Colab env not detected. Current cell is only for Colab.']


def colab_only_cell():
    """
    Works like return, but for local/colab cells. Allows to avoid if then indents in ipynb.
    Reminder: cannot be imported and used before this file is downloaded.
    """
    try:
        import google.colab
    except ImportError:
        raise _StopExecution()


@colab_only
def colab_no_scroll():
    """
    Tries to resize cell to avoid the very need of scrolling.
    But disables horizontal scroll on large images too.
    Horizontal scroll can be fixed with HBox(widgets.Output()).
    """
    output.no_vertical_scroll()


@colab_only
def colab_enable_custom_widget_manager():
    # move to here was useful to support both local and colab run without any code changes
    output.enable_custom_widget_manager()


def _move_progress_bar_to_top():
    display(Javascript('''
        let outputContainer = google.colab.output.getActiveOutputArea().parentNode.parentNode;
        let outputArea = outputContainer.querySelector('#output-area');
        outputArea.parentNode.append(outputArea);        
    '''))


@colab_only
def colab_add_download_button(fpath, caption):
    def clicked(arg):
        files.download(fpath)
        _move_progress_bar_to_top()
    
    import ipywidgets as widgets
    
    button_download = widgets.Button(description=caption)
    button_download.on_click(clicked)
    
    button_box = widgets.HBox([button_download], layout=widgets.Layout(justify_content='center'))
    display(button_box)


""" unused:
from IPython.display import HTML, display, Javascript, display_javascript
js1 = Javascript('''
async function resize_output() {
    google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);
    google.colab.output.getActiveOutputArea().scrollTo(2000, 0);
}
''')
get_ipython().events.register('post_run_cell', resize_output)
"""

''' possibly can be used  before gdown to track better which exactly files were downloaded
# @colab_only
def colab_track_uploads(input_dir: Path) -> dict[Path: int]:
    files = get_supported_data_files(input_dir)
    file_sizes = {f: f.stat().st_size for f in files}
    return file_sizes    
'''


# @colab_only
def colab_xor_demo_data(input_dir: Path, mixed_demo_policy: ColabDemoMixPolicy):
    fpaths = get_supported_data_files(input_dir)
    fsizes = {fp: fp.stat().st_size for fp in fpaths}
    
    '''
    gdown_files = {fp for fp in fsizes.keys() if fp not in fsizes_before_gdown}
    updated_files = {fp for fp in fsizes_before_gdown.keys() if fsizes_before_gdown[fp] != fsizes[fp]}
    previous_files = {fp for fp in fsizes_before_gdown.keys() if fp not in updated_files}
    '''
    demo_files = {fp for fp, sz in fsizes.items() if DEMO_DATA_FILE_SIZES.get(str(fp), None) == sz}
    user_files = {fp for fp in fsizes.keys() if fp not in demo_files}
    
    mixed = (demo_files and user_files)
    if not mixed:
        return
    if mixed and mixed_demo_policy == ColabDemoMixPolicy.STOP_RUN:
        raise Exception(
            'Demo files are mixed with user files. Consider disabling gdown commands for the demo files: !gdown -> # !gdown ')
    
    info_str = [
        (demo_files, 'demo data'),
        (user_files, 'user data'),
        # (previous_files, 'file uploaded manually or from the previous run'),
        # (gdown_files, 'downloaded via gdown'),
        # (updated_files, 'updated via gdown')         
    ]
    
    fsummary = {}
    for fp in fsizes.keys():
        finfo = [info for arr, info in info_str if fp in arr]
        fsummary |= {str(fp): ', '.join(finfo)}
    
    ff_logger.info('\n' +
                   'Demo data is mixed with other files. Demo data will be removed: \n' +
                   format_dict(fsummary, separator=': ', item_separator='\n') +
                   '\n')
    
    mixed_demo = len(demo_files) < len(fpaths)
    if mixed_demo and mixed_demo_policy == ColabDemoMixPolicy.AUTO_DELETE_DEMO:
        for fp in demo_files:
            fp.unlink(missing_ok=True)
