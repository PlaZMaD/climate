"""
Module specifically for Google Colab.
During local runs, all functions here are to be mocked or cancelled.
"""
from enum import Enum, auto


class RunMode(Enum):
    LOCAL, COLAB = auto(), auto()

try:
    import google.colab
except ImportError:
    RUN_MODE = RunMode.LOCAL
else:
    RUN_MODE = RunMode.COLAB

    from google.colab import output
    from google.colab import files
    from IPython.display import display
    from IPython.core.display import Javascript


def colab_only(func):
    def wrapper(*args, **kwargs):
        if RUN_MODE == RunMode.COLAB:
            return func(*args, **kwargs)
        else:
            print(f"Colab env not detected. {func.__name__} is skipped by design.")
            return None
    return wrapper


class StopExecution(Exception):
    def _render_traceback_(self):
        return ['Colab env not detected. Current cell is only for Colab.']


def colab_only_cell():
    """
    Works like return, but for cells.
    Reminder: cannot be imported and used before this file is downloaded.
    """
    try:
        import google.colab
    except ImportError:
        raise StopExecution()


@colab_only
def colab_no_scroll():
    """
    Tries to resize cell to avoid the very need of scrolling.
    But disables horizontal scroll on large images too.
    Horizontal scroll can be fixed with HBox(widgets.Output()).
    """
    output.no_vertical_scroll()


def move_progress_bar_to_top():
    display(Javascript('''
        let outputContainer = google.colab.output.getActiveOutputArea().parentNode.parentNode;
        let outputArea = outputContainer.querySelector('#output-area');
        outputArea.parentNode.append(outputArea);        
    '''))


@colab_only
def colab_add_download_button(fname, caption):
    def clicked(arg):
        files.download(fname)
        move_progress_bar_to_top()
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
