"""
Module specifically for Google Colab.
During local runs, all functions here are to be mocked or cancelled.
"""
from pathlib import Path

from src.ff_logger import ff_logger
from src.data_io.detect_import import SUPPORTED_FILE_EXTS_LOWER
from src.helpers.env_helpers import colab_only, ENV

# TODO 3 %autoreload stopped to work in colab, any replacement?
DEMO_DATA_FILES = {'eddy_pro result_SSB 2023.csv', 'BiometFy4_2023.csv'}


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


@colab_only
def colab_xor_demo_files():
    input_files = list(Path('.').glob('*.*'))
    supported_input_files = {str(file) for file in input_files if file.suffix.lower() in SUPPORTED_FILE_EXTS_LOWER}
    if DEMO_DATA_FILES & supported_input_files:
        if supported_input_files - DEMO_DATA_FILES:
            ff_logger.info('Both demo data files and user files are found in the input folder. Demo files will be removed.')
            for fpath in DEMO_DATA_FILES:
                Path(fpath).unlink(missing_ok=True)
        else:
            ff_logger.info('No user files are found in the input folder. Script will be using demo data.')