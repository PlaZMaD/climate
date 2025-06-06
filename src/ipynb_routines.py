"""
Unlike colab_routines.py, this file is expected to be used under local runs too.
However, output may be auto replaced with text.
"""
from warnings import warn

from IPython import get_ipython
from IPython.display import display, HTML
from PIL import Image
from ipywidgets import widgets, HBox

from src.helpers.env_helpers import ipython_only
from src.helpers.image_tools import grid_images


def display_image_row(paths):  
    imgs = []
    for path in paths:
        try:
            img = Image.open(path)
        except:
            continue
        imgs += [img]
    # TODO check paths exist where?
    if len(imgs) < 1:
            return

    img_combined = grid_images(imgs, len(imgs))
    # byte_arr = io.BytesIO()
    # img_combined.save(byte_arr, format='PNG')
    # from IPython.display import Image as IImage
    # IImage(data=byte_arr.getvalue(), width=img_combined.width, unconfined=True)

    # widgets.Image is not persistent on Colab load
    # display(byte_arr) does not have horisonal scroll,
    #     if vertical scroll is disabled on Colab
    # Hbox(widgets.Output(display(byte_arr))) works fluently

    out = widgets.Output(layout={'border': '1px solid black'})
    with out:
        display(img_combined)
    hbox = HBox([out])
    display(hbox)


def _css_enable_word_wrap(*args, **kwargs):
    display(HTML('''
    <style>
        pre {
            white-space: pre-wrap;
        }
    </style>
    '''))


def _register_ipython_callback_once(event_name, cb):
    ev = get_ipython().events
    cb_unregs = [cb_old for cb_old in ev.callbacks[event_name] if cb_old.__name__ == cb.__name__]
    if len(cb_unregs) == 1 and cb.__code__ == cb_unregs[0].__code__:
        return

    for cb_old in cb_unregs:
        warn(f'Removing unexpected callback {cb_old}.')
        ev.unregister(event_name, cb_old)

    ev.register(event_name, cb)


@ipython_only
def ipython_enable_word_wrap():
    _register_ipython_callback_once('pre_run_cell', _css_enable_word_wrap)
    print("Word wrap in output is enabled.")