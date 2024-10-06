"""
Unlike colab_routines.py, this file is expected to be used under local runs too.
However, output may be auto replaced with text.
"""
import io
from warnings import warn

from IPython import get_ipython
from IPython.display import HTML, display
from PIL import Image
from ipywidgets import widgets, HBox


def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)


def ipython_only(func):
    def wrapper(*args, **kwargs):
        if get_ipython():
            return func(*args, **kwargs)
        else:
            print(f"IPython env not detected. {func.__name__} is skipped by design.")
            return None

    return wrapper


def css_enable_word_wrap(*args, **kwargs):
    display(HTML('''
    <style>
        pre {
            white-space: pre-wrap;
        }
    </style>
    '''))


def register_ipython_callback_once(event_name, cb):
    ev = get_ipython().events
    cb_unregs = [cb_old for cb_old in ev.callbacks[event_name] if cb_old.__name__ == cb.__name__]
    if len(cb_unregs) == 1 and cb.__code__ == cb_unregs[0].__code__:
        return

    for cb_old in cb_unregs:
        warn(f'Removing unexpected callback {cb_old}.')
        ev.unregister(event_name, cb_old)

    ev.register(event_name, cb)


@ipython_only
def enable_word_wrap():
    register_ipython_callback_once('pre_run_cell', css_enable_word_wrap)
    print("Word wrap in output is enabled.")