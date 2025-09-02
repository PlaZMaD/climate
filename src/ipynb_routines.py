"""
Unlike colab_routines.py, this file is expected to be used under local runs too.
However, output may be auto replaced with text.

Also consider to change if nessesary:
if ENV.IPYNB:
    import matplotlib.pyplot as plt
"""
import logging
from pathlib import Path
from warnings import warn

from IPython import get_ipython
from IPython.display import display, HTML, SVG
from PIL import Image
from ipywidgets import widgets, HBox
from plotly import graph_objects as go
from plotly.io import renderers

from src.helpers.env_helpers import ipython_only, ENV
from src.helpers.image_tools import grid_images
from src.helpers.io_helpers import ensure_empty_dir


# TODO 2 create git readme and changelog for releases
# TODO 1 QOA QV have you shared 0.9.5? move to 0.9.4en + edit 0.9.2 source carefully?


if ENV.LOCAL:
    # reducing plotly log spam
    logging.getLogger('kaleido').setLevel(logging.WARNING)
    logging.getLogger('choreographer').setLevel(logging.WARNING)


def display_image_row(paths: list[Path]):
    imgs = []
    for path in paths:
        try:
            img = Image.open(path)
        except:
            continue
        imgs += [img]
    # TODO 4 check paths exist where?
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


def _plotly_show_override(self: go.Figure, local_out_dir: Path, **args):
    if ENV.IPYNB:
        svg_text = self.to_image(format='svg')
        display(SVG(svg_text))
    if ENV.LOCAL:
        print('Reminder: local screen resolution for plotly render can be adjusted.')

        dir = local_out_dir
        dir.mkdir(parents=True, exist_ok=True)

        fname = args['config']['toImageButtonOptions']['filename']
        fpath = dir / (fname + '.png')
        self.write_image(format='png', width=1920, file=fpath)


def setup_plotly(out_dir):
    if ENV.COLAB:
        renderers.default = 'colab'
    elif ENV.IPYNB or ENV.LOCAL:
        renderers.default = 'svg'
        # python < 3.10:
        #     https://stackoverflow.com/a/72614865/10141885
        #     on W10, pip install --upgrade "kaleido==0.1.*" may be required instead of 0.2.0
        # python >= 3.10:
        #     plotly_get_chrome may be required
        #     kaleido==1.0.0
        #     plotly==6.2.0

        local_dir = out_dir / 'local' / 'plots'
        ensure_empty_dir(local_dir)

        go.Figure.show = lambda self, **args: _plotly_show_override(self, local_dir, **args)
        print(f"Pure py plotly renderer is set to: {renderers.default}.")
