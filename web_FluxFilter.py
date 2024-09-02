from flask import Flask, request, jsonify, render_template
import json

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pylab as plt
import os
from pandas.api.types import is_datetime64_any_dtype as is_datetime
import dateutil
from copy import deepcopy as copy

import plotly.io as pio

from plotly.subplots import make_subplots
import plotly.express as px
import plotly_resampler
import dateparser

import bglabutils.basic as bg
import bglabutils.filters as bf

# import logging
# import re
#
#
# logging.basicConfig(level=logging.INFO, filename="/content/log.log", filemode="w", force=True)
# logging.info("START")



app = Flask(__name__)

# def get_graph(period = 'JJA'):
#     # Import libraries
#     import pandas as pd
#     import plotly.express as px
#
#     df = pd.read_csv('GlobalTemps1880-2022.csv')
#     fig = px.bar(df, x='Year', y = period, color=period, title = period,
#         color_continuous_scale='reds', template='none', width=1000, height=500)
#
#     graphJSON = fig.to_json()
#
#     return json.dumps(graphJSON)

def template(params):
    return render_template(params['template'], params=params)

#### Simple template ####
@app.route('/')
def index():
    # The root endpoint builds the page
    header = "FluxFilter"
    subheader = "Data filtering software"
    description = """Some useful scripts
    """
    # menu_label = "Select a period"
    params = {
        'template': 'index.html',
        'title': header,
        'subtitle': subheader,
        'content' : description,
    #     'menu_label': menu_label,
    #     'options' : [{'code':'J-D', 'desc':'Whole year'},
    #                  {'code':'DJF','desc':'Winter (North)'},
    #                  {'code':'MAM','desc':'Spring (North)'},
    #                  {'code':'JJA','desc':'Summer (North)'},
    #                  {'code':'SON','desc':'Autumn/Fall (North)'}],
    #     'graph'   : get_graph()
    # }
    }
    return template(params)


#### Callback for drop down menu ####

# @app.route('/callback', methods=['POST'])
# def callback():
#     # The callback updates the page
#     if request.is_json:
#         data = request.get_json()
#         #print(f"{list(data.keys())}")
#
#         # do something with the incoming data and return the appropiate data
#         print(data['dropdown'])
#         return get_graph(period=data['dropdown'])
#     else:
#         return jsonify({"error": "Invalid JSON data"}), 400

#### Main ####

if __name__ == '__main__':
    app.run(debug=True)