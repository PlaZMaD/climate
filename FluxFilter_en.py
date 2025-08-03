# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% [markdown] id="pqQVYpfkwA8E"
# # **FluxFilter**

# %% [markdown] id="oE87fcFbwlIu"
# ## **Introduction**
# This open-sourced script is designed for the post-processing - visualization, filtering, filling, and partitioning - of 30-minute data from the eddy covariance stations. The script can be used for obtaining reliable cumulative sums of ecosystem heat, water vapour and NEE fluxes. A user-specified post-processing pipeline is available by means of a set of instruments for data filtering. The input parameters are: data on ecosystem fluxes with a time step of 30 minutes, calculated from the high-frequency data, with diagnostic flags, as well as meteorological parameters with a time resolution of 30 minutes. The main purpose of the script: postprocessing of the eddy covariance data of the 1-st processing level to obtain the data of the levels 2, 3 and 4.
#
# * Level 1 means fluxes calculated using the special software with the widely used filtering and correction procedures (example is Full Output file of EddyPro, LI-COR Inc., USA) and meteorological data averaged for each 30 minutes.
# * Level 2 means unfilled 30-minute data, the PI of the station excludes periods of the obvious malfunction of the instruments (i.e. data for these periods are filled with the missing values code -9999). Such data are equivalent of the Level 2 data of the European fluxes database cluster.
# * Level 3 refers to level 2 data, also unfilled, but carefully filtered based on physical and statistical criteria.
# * Level 4 refers to the gapfilled data.
# To run the demo-version of the script, just click in the Google Colab "Runtime - Run All"  
# The newest version of the script is in the repository https://github.com/PlaZMaD/climate/releases
#
# ## **Input files**
# Input file formats: EddyPro full output file (see [EddyPro manual](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) for fluxes, and EddyPro biomet file ([again](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) for meteorology. Turbulent fluxes and u* are taken from the full output file, and all meteorological variables (air temperature and relative humidity, etc.) are taken from the biomet file. Basic requirements for input files:
#
# * Files must be in .csv (comma separated value) format.
# * Column headings should strictly correspond to the EddyPro manual. The variables in the script are identified by the column names (co2_flux for CO2 flux in full output, Ta_1_1_1 for air temperature in biomet, etc.).
# * The missing value indicator in the input files must be -9999.
# * Units for biomet file variables should be the same as the base units for biomet file as per EddyPro manual. Exception: Air/Soil Temperature should be in degrees Celsius.
# * An example full output file can be downloaded [here](https://drive.google.com/file/d/1TyuHYZ0uh5teRiRFAga0XIqfU4vYW4-N/view?usp=sharing).
# * An example biomet file can be downloaded [here](https://drive.google.com/file/d/1FjiBcSspDBlYlcg9Vzy71Sm49gOFZGBF/view?usp=sharing).
# * The full output file should have 3 header lines and the variable names should be written in the 2nd line.
# * The biomet file must have 2 header lines and the variable names must be written in the 1st line. By default, files with date and time written in the TIMESTAMP_1 column in the yyyy-mm-dd HHMM format are read without problems.
#
# ## **Output files**
# Output file formats (written to the FluxFilter_output.zip archive and to the output directory in the Files section):
# 1.   A file formatted for European fluxes database cluster, level 2 (ias-file);
# 2.   Input file for the u* filtering, gap filling and partitioning tool REddyProcWeb (Max Planck Institute, Germany). This file is used as input for the "Processing with the REddyProc tool" section of this script. These are the data of level 3.
# 3.   Input file for the Flux Analysis Tool (M. Ueyama, Japan) for the gap filling, level 3.
# 4.   The output_all file contains all the raw variables (level 1) and all flags implemented for the data.
# 5.   The output_summary file contains the time series for the main variables of the raw data, filtered data, the flag for each filter applyed, average diurnal courses in a 30- and 10-day window.
# 6.   The log file records during the script's run, includes parameters that were accepted for the filtering at this run.
# 7.   The reddyproc directory contains the results of gapfilling (level 4) in the same format as the original [REddyProcWeb tool](https://www.bgc-jena.mpg.de/5624929/Output-Format). Additionally, the output/reddyproc directory contains summary files (level 4) with the indexes _hourly (diurnal courses of the original and filled variables), _daily (daily averages), _monthly (monthly averages), and _yearly (yearly values, or for the entire processing period if there is less data).
#
# ## **Loading the input files**
# * upload full output and biomet files to the Google drive,
# * open access to them (sharing to everyone with the link)
# * in the Data loading config replace the names of the input files with the names of the files under processing
# * in the Data loading config check the format of the input date and time
# * copy the part of the public link to the section Loading data into the command !gdown
#
# ## **Before the filtering**
# *   You can upload multiple full output and biomet files, they will be automatically arranged in ascending date-time order and merged into the one table
# *   The timestamps of each input file are checked (regularization)
# *   VPD <-> RH, SWIN <-> RG <-> PAR are calculated in case of absence of any of them
# *   You can process CO2 flux or check the storage data, add it to the CO2 flux and work with NEE
#
# ## **How does the filtering happen**
# The script allows you to identify and remove low-quality and outlier values using 1) physical, 2) statistical filtering, which occurs under your visual control - you can look at the graphs before and after filtering. Each filter can be switched off (just comment the corresponding line), the parameters should be adjusted to the data of a given site and eddy covariance system.
# 1. Physical filtering includes removing of the following types of the suspicious values: based at the quality flag greater than the threshold, with the gas analyzer signal strength below the threshold, in case of rain events, at high humidity, by night and daytime plausible ranges, by the plausible range in winter.
# 2. Statistical filtering includes the removal of outliers/spikes using filters for minimum and maximum plausible values, quantiles, deviations from the average diurnal course in a moving window, deviations from the average in a sliding window of several points MAD (Sachs, 2006) and HAMPEL (Pearson et al., 2016).
# 3. It is possible to exclude data by a list of intervals (exclude from ... to ...), for example, calibrations according to the technical work log.
#
# ## **Downloading the output files**
# All output files can be downloaded in the last section "Downloading results" by clicking the "Download outputs" button.
#
# (c)Evgeny Kurbatov, Vadim Mamkin, Olga Kuricheva  
# (c)REddyProc tool: Wutzler T, Lucas-Moffat A, Migliavacca M, Knauer J, Sickel K, Sigut, Menzer O & Reichstein M (2018) Basic and extensible post-processing of eddy covariance flux data with REddyProc. Biogeosciences, Copernicus, 15, doi: 10.5194/bg-15-5015-2018  
# (c)REddyProc adaptation and post-processing: Oleg Deshcherevskii
#

# %% [markdown] id="sj6Z0gnhVM-R"
# # Technical block
# Importing libraries and defining functions

# %% id="lZliIHxRJiqk"
# from google.colab import userdata
# key = userdata.get('registry_key')

# %% id="HT2KP0eYk1r3"
# !mkdir output

# %% id="E-a6ANTGBsqg"
# %pip install plotly-resampler dateparser >> /dev/null
# # %pip install --index-url https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null
# %pip install --index-url https://gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null

# %% id="Ywv5kp0rzanK"
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pylab as plt
import os
from pandas.api.types import is_datetime64_any_dtype as is_datetime
import dateutil
from copy import deepcopy as copy

import plotly.io as pio
pio.renderers.default = "colab"
from IPython.display import display


from google.colab import output
output.enable_custom_widget_manager()

from plotly.subplots import make_subplots
import plotly.express as px
import plotly_resampler
import dateparser

import bglabutils.basic as bg
import bglabutils.filters as bf

import logging
import re
import sys

# import bglabutils.boosting as bb
# import textwrap

from google.colab import output
output.no_vertical_scroll()

# %load_ext autoreload
# %autoreload 2

logging.basicConfig(level=logging.INFO, filename="/content/output/log.log", filemode="w", force=True)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logging.info("START")


# %% [markdown] id="c_5uwjkzfk45"
# ## Functions for visualisation

# %% id="5AXOLjh5VeMp"
def colapse_filters(data, filters_db_in):
  out_filter = {}
  for feature, filters in filters_db_in.items():
    if len(filters)>0:
      out_filter[feature] = data[filters[0]].astype(int) if len(filters)==1 else np.logical_and.reduce((data[filters].astype(int)), axis=1).astype(int)
  return out_filter

def get_column_filter(data, filters_db_in, column_name):
  if column_name not in filters_db_in.keys():
    return np.array([1]*len(data.index))
  if len(filters_db_in[column_name]) > 0:
    return colapse_filters(data, filters_db_in)[column_name]
  else:
    return np.array([1]*len(data.index))

def basic_plot( data, col2plot, filters_db=None,  min_days=8, window_days = 10, steps_per_day=2*24, use_resample=False):

  multiplot = isinstance(col2plot, list)

  window_days = window_days   # days in a moving window
  min_days = window_days//2 - 1
  pl_data = data.copy()

  layout = go.Layout(
      paper_bgcolor='rgba(0,0,0,0)',
      plot_bgcolor='rgba(0,0,0,0)'
  )
  color_data = 'darkorange'
  color_line = 'darkslateblue'

  add_color_data = copy(px.colors.qualitative.Pastel1)
  add_color_line = copy(px.colors.qualitative.Prism)

  add_color_data.insert(0, color_data)
  add_color_line.insert(0, color_line)

  fig = go.Figure(layout=layout)
  if multiplot:
    fig = make_subplots(rows=len(col2plot), cols=1, shared_xaxes=True, figure=fig, subplot_titles=[i.upper() for i in col2plot])
  else:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, figure=fig, row_heights=[.8, .2], subplot_titles=[col2plot.upper(), 'Residuals'])

  fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey', minor_ticks='inside', minor_tickcolor='Grey')
  fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey')
  # fig.update_layout(
  #     title = col2plot,
  #     xaxis_tickformat = '%H:%M %d %B <br>%Y'
  # )
  if not multiplot:
    cols = [col2plot]
  else:
    cols = col2plot

  fig.update_layout(
    # title = " ".join(cols),
    xaxis_tickformat = '%H:%M %d %B <br>%Y'
  )
  for row, col2plot in enumerate(cols):
    if filters_db is not None:
      filters =  get_column_filter(pl_data, filters_db, col2plot)
      pl_data.loc[~filters.astype(bool), col2plot] = np.nan

    if steps_per_day % 2 == 0:
      closed='left'
    else:
      closed='both'
    rolling_mean = bg.calc_rolling(pl_data[col2plot], step=steps_per_day, rolling_window=window_days, min_periods=min_days)

    fig.add_trace(go.Scattergl(x=pl_data.index, y=pl_data[col2plot], mode='markers', name=col2plot, marker_color=add_color_data[row]), row=row+1, col=1)
    fig.add_trace(go.Scattergl(x=rolling_mean.index, y=rolling_mean, mode='lines', name=f'{col2plot} mean {window_days} days', opacity=.7, line_color=add_color_line[row]), row=row+1, col=1)
    if not multiplot:
      fig.add_trace(go.Scattergl(x=rolling_mean.index, y=rolling_mean - pl_data[col2plot], mode='lines', name=f'residuals'), row=2, col=1)

  if use_resample:
    fig = plotly_resampler.FigureResampler(fig, default_n_shown_samples=5000)

  fig_name = f"_{int(np.median(pl_data.index.year))}"
  if "ias_output_prefix " in locals() or "ias_output_prefix" in globals():
    fig_name = fig_name + "_" + ias_output_prefix
  fig_config = {'toImageButtonOptions': {'filename': '_'.join(cols)+fig_name,}}
  fig.show(config=fig_config)



def plot_nice_year_hist_plotly(df, to_plot, time_col, filters_db):
    pl_data = df.copy()#[to_plot]
    # point
    if filters_db is not None:
      print()
      filters =  get_column_filter(df, filters_db, to_plot)
      pl_data['filter'] = filters
      pl_data.loc[~filters.astype(bool), to_plot] = np.nan
    # print(pl_data.loc[pd.to_datetime('26 June 2016 1:30'), ['nee', 'nee_nightFilter', 'swin_1_1_1', 'filter']].to_string())
    fig = go.Figure()
    fig.update_layout(title = f'{to_plot}')
    fig.add_trace(go.Heatmap(x=pl_data[time_col].dt.date, y=pl_data[time_col].dt.hour + 0.5*(pl_data[time_col].dt.minute//30), z=pl_data[to_plot]))
    fig_config = {'toImageButtonOptions': {'filename': f'{to_plot}_{int(np.median(pl_data.index.year))}',}}

    fig.show(config=fig_config)


def make_filtered_plot(data_pl, col, filters_db):
  data = data_pl.copy()
  layout = go.Layout(
      paper_bgcolor='rgba(0,0,0,0)',
      plot_bgcolor='rgba(0,0,0,0)'
  )
  add_color_dot = copy(px.colors.qualitative.Dark24)
  fig = go.Figure(layout=layout)
  fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey', minor_ticks='inside', minor_tickcolor='Grey')
  fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey')

  data['full_filter'] =  get_column_filter (data, filters_db, col)
  data['full_filter'] = data['full_filter'].astype(int)
  pl_data = data.query(f"full_filter==0")
  color_ind = 0
  fig.add_trace(go.Scattergl(x=data.query("full_filter==1").index, y=data.query("full_filter==1")[col], mode='markers', name="Good data", marker_color=add_color_dot[color_ind] ))
  color_ind += 1

  if len(filters_db[col]) > 0:
    for filter_name in filters_db[col]:
      fig.add_trace(go.Scattergl(x=pl_data.query(f"{filter_name}==0").index, y=pl_data.query(f"{filter_name}==0")[col], mode='markers',   name=filter_name, marker_color=add_color_dot[color_ind]))
      color_ind += 1
      pl_data = pl_data.query(f"{filter_name}==1")

  fig.update_layout(
      title = f'{col2plot}',
      xaxis_tickformat = '%H:%M %d %B <br>%Y'
  )
  fileName = "basic"
  if "ias_output_prefix " in locals() or "ias_output_prefix" in globals():
    fileName = ias_output_prefix
  fileName += f'_{int(np.median(data.index.year))}_{col}'
  fig_config = {'toImageButtonOptions': {'filename': fileName,}}
  fig.show(config=fig_config)


def plot_albedo (plot_data, filters_db):
  pl_data = plot_data.copy()

  layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
    )


  if ('swin_1_1_1' not in pl_data.columns) or ('swout_1_1_1' not in pl_data.columns):
    print("No swin_1_1_1/sout_1_1_1")
    return 0
  pl_data['albedo'] = pl_data['swout_1_1_1'].div(pl_data['swin_1_1_1'])
  pl_data.loc[pl_data['swin_1_1_1']<=20., 'albedo'] = np.nan
  pl_data.loc[pl_data['swout_1_1_1']<=0, 'albedo'] = np.nan

  pl_ind  = pl_data[pl_data['albedo']<pl_data['albedo'].quantile(0.95)].index
  fig = go.Figure(layout=layout)
  fig.add_trace(go.Scattergl(x=pl_data.loc[pl_ind].index, y=pl_data.loc[pl_ind, 'albedo'], name="Albedo"))
  fig.update_layout(title = 'Albedo')
  fig_config = {'toImageButtonOptions': {'filename': 'albedo',}}
  fig.show(config=fig_config)


# %% [markdown] id="PKznP_r1foao"
# ## Functions for filtering

# %% id="EuUwWEPRaVT5"
def min_max_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    for col, limits in config.items():
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue
      filter = get_column_filter(data, filters_db, col)

      if len(filter) == 0:
        filter = [1]*len(data.index)


      data[f"{col}_minmaxfilter"] = filter

      if col not in ['rh_1_1_1', 'swin_1_1_1', 'ppfd_1_1_1', 'swin_1_1_1']:
        data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
      else:
        if col == 'rh_1_1_1':
          data[col] = data[col].clip(upper=limits[1])
          data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
        else:
          data[col] = data[col].clip(lower=limits[0])
          if col not in ['swin_1_1_1']:
            data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
          else:
            data.loc[data.query(f"{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0

      if f"{col}_minmaxfilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_minmaxfilter")
      else:
        print("filter already exist but will be overwritten")
    logging.info(f"min_max_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def qc_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, limits in config.items():
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      data[f"{col}_qcfilter"] = filter
      if f"qc_{col}" not in data.columns and col != 'nee':
        print(f"No qc_{col} in data")
        continue
      if col != 'nee':
        data.loc[data[f"qc_{col}"] > config[col], f"{col}_qcfilter"] = 0
      else:
        data.loc[data[f"qc_co2_flux"] > config['co2_flux'], f"nee_qcfilter"] = 0

      if f"{col}_qcfilter" not in filters_db[col]:
          filters_db[col].append(f"{col}_qcfilter")
      else:
        print("filter already exist but will be overwritten")
    logging.info(f"qc_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def std_window_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    for col, lconfig in config.items():
      sigmas = lconfig['sigmas']
      window_size = lconfig['window']
      min_periods = lconfig['min_periods']#(window_size//2-1)
      points_per_day = int(pd.Timedelta('24h')/data_in.index.freq)#lconfig['points_per_day']
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      data[f"{col}_stdwindowfilter"] = filter
      data['tmp_col'] = data[col]
      data.loc[~filter.astype(bool), 'tmp_col'] = np.nan
      rolling_mean = bg.calc_rolling(data['tmp_col'], rolling_window=window_size, step=points_per_day, min_periods= min_periods)
      residuals = data['tmp_col'] - rolling_mean
      rolling_sigma = residuals.rolling(window=window_size * points_per_day, center=True, closed='both',  min_periods=window_size * points_per_day//2).std()
      data = data.drop(columns='tmp_col')
      # print(rolling_sigma, rolling_mean)
      upper_bound = rolling_mean + rolling_sigma * sigmas
      lower_bound = rolling_mean - rolling_sigma * sigmas
      upper_inds = upper_bound[upper_bound < data[col]].index
      lower_inds = lower_bound[lower_bound > data[col]].index
      data.loc[upper_inds , f"{col}_stdwindowfilter"] = 0
      data.loc[lower_inds , f"{col}_stdwindowfilter"] = 0
      # # print(len(lower_inds), len(upper_inds))
      # plt.plot(rolling_mean)
      # plt.title(col)
      # plt.show()

      if f"{col}_stdwindowfilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_stdwindowfilter")
      else:
        print("filter already exist but will be overwritten")
    logging.info(f"std_window_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_filter(data_in, filters_db_in, config):#, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()


    for col in ["co2_flux", 'h', 'le', 'ch4_flux']:

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_physFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_physFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_physFilter"] = filter

    if 'co2_signal_strength' in data.columns and 'CO2SS_min' in config.keys():
      data.loc[data['co2_signal_strength'] < config['CO2SS_min'], 'co2_flux_physFilter'] = 0
    else:
      print("No co2_signal_strength found")

    if 'ch4_signal_strength' in data.columns and 'CH4SS_min' in config.keys():
      data.loc[data['ch4_signal_strength'] < config['CH4SS_min'], 'ch4_flux_physFilter'] = 0
    else:
      print("No ch4_signal_strength found")

    if 'p_rain_limit' in config.keys():
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'co2_flux_physFilter'] = 0
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'h_physFilter'] = 0
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'le_physFilter'] = 0
      if 'rain_forward_flag' in config:
        rain_forward_flag = config['rain_forward_flag']
        for i in range(rain_forward_flag):
          ind = data.loc[data['p_rain_1_1_1'] >  config['p_rain_limit']].index.shift(i, freq=file_freq)
          data.loc[ind, 'co2_flux_physFilter'] = 0
          data.loc[ind, 'h_physFilter'] = 0
          data.loc[ind, 'le_physFilter'] = 0

    if 'RH_max' in config.keys():
      RH_max = config['RH_max']
      data.loc[data['rh_1_1_1']>RH_max, 'co2_flux_physFilter'] = 0
      data.loc[data['rh_1_1_1']>RH_max, 'le_physFilter'] = 0
    logging.info(f"meteorological_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_rh_filter(data_in, filters_db_in, config):#, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'le', 'nee']:

      if col not in data.columns:
        print(f"no {col}")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_rhFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_rhFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_rhFilter"] = filter

    if 'RH_max' in config.keys() and 'rh_1_1_1' in data.columns:
      RH_max = config['RH_max']
      data.loc[data['rh_1_1_1']>RH_max, 'co2_flux_rhFilter'] = 0
      if 'nee' in data.columns:
        data.loc[data['rh_1_1_1']>RH_max, 'nee_rhFilter'] = 0
      data.loc[data['rh_1_1_1']>RH_max, 'le_rhFilter'] = 0
    logging.info(f"meteorological_rh_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_night_filter(data_in, filters_db_in, config):#, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    if "swin_1_1_1" not in data_in.columns:
      logging.info(f"meteorological_night_filter not applied, no SWIN found  \n")
      return data_in, filters_db_in

    if not config['use_night_filter']:
      logging.info(f"Night filter dissabled.")
      return data_in, filters_db_in

    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    col_of_interest = ["h", 'le', 'nee', 'co2_flux']

    for col in col_of_interest:
      if col not in data.columns:
        print(f"no {col} column")
        continue
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_nightFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_nightFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_nightFilter"] = filter

    if "nee" in data.columns:
      data_night_index = data.query(f"swin_1_1_1<10&nee<{config['night_nee_min']}").index
      data.loc[data_night_index, f"nee_nightFilter"] = 0

    if "co2_flux" in data.columns:
      data_night_index = data.query("swin_1_1_1<10&co2_flux<0").index
      data.loc[data_night_index, f"co2_flux_nightFilter"] = 0

    data_night_index = data.query(f"(h<{config['night_h_limits'][0]}|h>{config['night_h_limits'][1]})&swin_1_1_1<10").index
    data.loc[data_night_index, f"h_nightFilter"] = 0

    data_night_index = data.query(f"(h<{config['night_le_limits'][0]}|h>{config['night_le_limits'][1]})&swin_1_1_1<10").index
    data.loc[data_night_index, f"le_nightFilter"] = 0

    # if 'nee' in data.columns:
    #   data_night_index = data.query(f'nee>{config["day_nee_max"]}&swin_1_1_1>=10').index
    #   data.loc[data_night_index, f"nee_nightFilter"] = 0
    logging.info(f"meteorological_night_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_day_filter(data_in, filters_db_in, config):#, file_freq='30T'):
    if "swin_1_1_1" not in data_in.columns:
      logging.info(f"meteorological_day_filter not applied, no SWIN found  \n")
      return data_in, filters_db_in

    if not config['use_day_filter']:
      logging.info(f"Day filter dissabled.")
      return data_in, filters_db_in

    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    col_of_interest = ['nee']

    for col in col_of_interest:
      if col not in data.columns:
        print(f"no {col} column")
        continue
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_dayFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_dayFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_dayFilter"] = filter

    if 'nee' in data.columns:
      data_day_index = data.query(f'nee>{config["day_nee_max"]}&swin_1_1_1>={config["day_swin_limit"]}').index
      data.loc[data_day_index, f"nee_dayFilter"] = 0
    logging.info(f"meteorological_day_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_co2ss_filter(data_in, filters_db_in, config):#, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    file_freq = data_in.index.freq
    if 'CO2SS_min' not in config.keys():
      return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'nee']:

      if col not in data.columns:
        print(f"no {col} column")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_co2ssFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_co2ssFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_co2ssFilter"] = filter

      if 'co2_signal_strength' in data.columns:
        data.loc[data['co2_signal_strength'] < config['CO2SS_min'], f'{col}_co2ssFilter'] = 0

      else:
        print("No co2_signal_strength found")
    logging.info(f"meteorological_co2ss_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_ch4ss_filter(data_in, filters_db_in, config):#, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    file_freq = data_in.index.freq
    if 'CH4SS_min' not in config.keys():
      return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["ch4_flux"]:

      if col not in data.columns:
        print(f"no {col} column")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_ch4ssFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_ch4ssFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_ch4ssFilter"] = filter

    if 'ch4_signal_strength' in data.columns:
      data.loc[data['ch4_signal_strength'] < config['CH4SS_min'], 'ch4_flux_ch4ssFilter'] = 0
    else:
      print("No ch4_signal_strength found")
    logging.info(f"meteorological_coh4ss_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_rain_filter(data_in, filters_db_in, config):#, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'h', 'le', 'nee', "ch4_flux"]:
      if col not in data.columns:
        print(f"no {col}")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_rainFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_rainFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_rainFilter"] = filter

    if 'p_rain_limit' in config.keys() and 'p_rain_1_1_1' in data.columns:
      if 'co2_flux' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'co2_flux_rainFilter'] = 0
      if 'h' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'h_rainFilter'] = 0
      if 'le' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'le_rainFilter'] = 0
      if 'nee' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'nee_rainFilter'] = 0
      if 'ch4_flux' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'ch4_flux_rainFilter'] = 0

      if 'rain_forward_flag' in config:
        rain_forward_flag = config['rain_forward_flag']
        for i in range(rain_forward_flag):
          ind = data.loc[data['p_rain_1_1_1'] >  config['p_rain_limit']].index.shift(i, freq=file_freq)
          ind = ind.intersection(data.index)
          if len(ind) == 0:
            continue
          if 'nee' in data.columns:
            data.loc[ind, 'nee_rainFilter'] = 0
          if 'ch4_flux' in data.columns:
            data.loc[ind, 'ch4_flux_rainFilter'] = 0
          if 'co2_flux' in data.columns:
            data.loc[ind, 'co2_flux_rainFilter'] = 0
          if 'h' in data.columns:
            data.loc[ind, 'h_rainFilter'] = 0
          if 'le' in data.columns:
            data.loc[ind, 'le_rainFilter'] = 0

    logging.info(f"meteorological_rain_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def quantile_filter(data_in, filters_db_in, config):
    if len(config) == 0:
      return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, limits in config.items():
      limit_down, limit_up = limits
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_quantilefilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_quantilefilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_quantilefilter"] = filter
      up_limit = data.loc[data[f'{col}_quantilefilter'] == 1, col].quantile(limit_up)
      down_limit = data.loc[data[f'{col}_quantilefilter'] == 1, col].quantile(limit_down)
      f_inds = data.query(f"{col}_quantilefilter==1").index
      print("Quantile filter cut values: ", down_limit, up_limit)
      # data.loc[f_inds, f'{col}_quantilefilter'] = ((data.loc[f_inds, col] <= up_limit) & (data.loc[f_inds, col] >= down_limit)).astype(int)
      data.loc[data[col] > up_limit, f'{col}_quantilefilter'] = 0
      data.loc[data[col] < down_limit, f'{col}_quantilefilter'] = 0

      # print(col, (data.loc[f_inds, col] < down_limit).sum(), (data.loc[f_inds, col] > up_limit).sum(), len(data.loc[f_inds, col].index), ((data.loc[f_inds, col] < up_limit) & (data.loc[f_inds, col] > down_limit)).astype(int).sum())
      # print(filter.sum(), data[f'{col}_quantilefilter'].sum(), filter.sum() - data[f'{col}_quantilefilter'].sum())
    logging.info(f"quantile_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def mad_hampel_filter(data_in, filters_db_in, config):
    if len(config) == 0:
      return data_in, filters_db_in
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, lconfig in config.items():
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue

      hampel_window = lconfig['hampel_window']
      z = lconfig['z']
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_madhampel" not in filters_db[col]:
        filters_db[col].append(f"{col}_madhampel")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_madhampel"] = filter

      # hampel_window = 20
      print(f"Processing {col}")
      outdata = bf.apply_hampel_after_mad(data.loc[data[f'{col}_madhampel']==1, :], [col], z=z, window_size=hampel_window)
      data.loc[data[f'{col}_madhampel']==1, f'{col}_madhampel'] = outdata[f'{col}_filtered'].astype(int)
      data[f"{col}_madhampel"] = data[f"{col}_madhampel"].astype(int)

    logging.info(f"mad_hampel_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def manual_filter(data_in, filters_db_in, col_name, range, value ):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    filter = get_column_filter(data, filters_db, col_name)
    if len(filter) == 0:
      filter = [1]*len(data.index)
    data[f"{col_name}_manualFilter"] = filter
    # if range not in data.index:
    #   print('WARNING date range is not in index! Nothing is changed!')
    #   return data, filters_db
    try:
      dt_start = pd.to_datetime(start, dayfirst=True)
      dt_stop = pd.to_datetime(stop, dayfirst=True)
      if dt_start > dt_stop:
        raise KeyError("Check your dates")

      if dt_start < data.index[0] and (dt_stop <= data.index[-1] and dt_stop > data.index[0]):
        dt_start = data.index[0]
        print(f"Actual manual start: {dt_start}")

      if dt_stop > data.index[-1] and (dt_start >= data.index[0] and dt_start < data.index[-1]):
        dt_stop = data.index[-1]
        print(f"Actual manual stop: {dt_start}")

      range=pd.date_range(dt_start, dt_stop, freq=data.index.freq)
      data.loc[range, f"{col_name}_manualFilter"] = value
    except KeyError:
      print("ERROR! Check the date range!")
      return data, filters_db

    if f"{col_name}_manualFilter" not in filters_db[col_name]:
        filters_db[col_name].append(f"{col_name}_manualFilter")
    else:
      print("filter already exist but will be overwritten")
    logging.info(f"manual_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def winter_filter(data_in, filters_db_in, config, date_ranges):
  data = data_in.copy()
  filters_db = filters_db_in.copy()
  if ('winter_nee_limits' not in config.keys()) and ('winter_ch4_flux_limits' not in config.keys()):
    return data, filters_db

  printed_flag_start = False
  printed_flag_stop = False

  if 'winter_nee_limits' in config.keys():
      for col in ['nee', 'co2_flux']:
        if col not in data.columns:
          print(f"No column with name {col}, skipping...")
          continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
          filter = [1]*len(data.index)
        data[f"{col}_winterFilter"] = filter
        try:
          for start, stop  in date_ranges:
            dt_start = pd.to_datetime(start, dayfirst=True)
            dt_stop = pd.to_datetime(stop, dayfirst=True)

            if dt_start > dt_stop:
              raise KeyError("Check your dates, start > stop")

            if dt_stop <= data.index[0] or dt_start >= data.index[-1]:
              print(f'Warning, empty range {dt_start} - {dt_stop}!')
              continue

            if dt_start < data.index[0] and (dt_stop <= data.index[-1] and dt_stop > data.index[0]):
              dt_start = data.index[0]
              if not printed_flag_start:
                print(f"Actual winter start: {dt_start}")
                printed_flag_start = True

            if dt_stop > data.index[-1] and (dt_start >= data.index[0] and dt_start < data.index[-1]):
              dt_stop = data.index[-1]
              if not printed_flag_stop:
                print(f"Actual winter stop: {dt_start}")
                printed_flag_stop = True

            range=pd.date_range(dt_start, dt_stop, freq=data.index.freq)

            inds_down = data.loc[range].query(f"{col}<{config['winter_nee_limits'][0]}").index
            inds_up = data.loc[range].query(f"{col}>{config['winter_nee_limits'][1]}").index
            data.loc[inds_up, f"{col}_winterFilter"] = 0
            data.loc[inds_down, f"{col}_winterFilter"] = 0
        except KeyError:
          print("ERROR! Check the date range!")
          return data, filters_db

        if f"{col}_winterFilter" not in filters_db[col]:
          filters_db[col].append(f"{col}_winterFilter")
        else:
          print("filter already exist but will be overwritten")

  if 'winter_ch4_flux_limits' in config.keys():
      for col in ['ch4_flux']:
        if col not in data.columns:
          print(f"No column with name {col}, skipping...")
          continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
          filter = [1]*len(data.index)
        data[f"{col}_winterFilter"] = filter
        try:
          for start, stop  in date_ranges:

            dt_start = pd.to_datetime(start, dayfirst=True)
            dt_stop = pd.to_datetime(stop, dayfirst=True)

            if dt_start > dt_stop:
              raise KeyError("Check your dates, start > stop")

            if dt_stop <= data.index[0] or dt_start >= data.index[-1]:
              print(f'Warning, empty range {dt_start} - {dt_stop}!')
              continue

            if dt_start < data.index[0] and (dt_stop <= data.index[-1] and dt_stop > data.index[0]):
              dt_start = data.index[0]
              if not printed_flag_start:
                print(f"Actual winter start: {dt_start}")
                printed_flag_start = True

            if dt_stop > data.index[-1] and (dt_start >= data.index[0] and dt_start < data.index[-1]):
              dt_stop = data.index[-1]
              if not printed_flag_stop:
                print(f"Actual winter stop: {dt_start}")
                printed_flag_stop = True

            range=pd.date_range(dt_start, dt_stop, freq=data.index.freq)

            inds_down = data.loc[range].query(f"{col}<{config['winter_ch4_flux_limits'][0]}").index
            inds_up = data.loc[range].query(f"{col}>{config['winter_ch4_flux_limits'][1]}").index
            data.loc[inds_up, f"{col}_winterFilter"] = 0
            data.loc[inds_down, f"{col}_winterFilter"] = 0
        except KeyError:
          print("ERROR! Check the date range!")
          return data, filters_db

        if f"{col}_winterFilter" not in filters_db[col]:
          filters_db[col].append(f"{col}_winterFilter")
        else:
          print("filter already exist but will be overwritten")

  logging.info(f"winter_filter applied with the next config: \n {config}  \n Date range: {date_ranges} \n")
  return data, filters_db


# %% [markdown] id="WfWRVITABzrz"
# #Setting the parameters for loading and processing of the data
#

# %% [markdown] id="ox0UplWMe7wn"
# ## Data loading config
# Here the parameters of the input files are specified: names, date-time format, etc.
# **It is necessary to change:**
#
# `###Type the names of your files and the path to them.`
#
# In `config['path']` should be either path to a file (`= ['1.csv']`) if the filename is 1.csv or the list of paths in case of several files (`= ['1.csv', '2.csv']`). If we import files via the !gdown command from the Google drive,  it is enough to specify in single quotes  *filename.extension*. Do not miss the extension .csv!
#
# **It is necessary to check:**
#
# `  format = "%Y-%m-%d %H:%M"  #"%d/%m/%Y %H:%M"  #"%Y-%m-%d %H:%M:%S"`
#
# Check the date order (year, month, day) and date-time separators in the input files by opening them in a text editor (Notepad). Possible options:
#
# 1.  The date is written as 05/29/2024 and the time as 12:00. Then they are encoded as "%d.%m.%Y %H:%M" - this format is written below by default, nothing needs to be changed;
# 2.  The date is written as 05/29/2024 and the time as 12:00. Change the format in the line below to "%d/%m/%Y %H:%M"
# 3.  The date is written as 2024-05-29 and the time as 1200. Change the format in the line below to "%Y-%m-%d %H%M"
# 4.  In other cases, behave similarly. If there are seconds in the time column, the format is encoded as "%Y-%m-%d %H:%M:%S".
#
# **Additional options (better not to change without PRO level):**
#
# `config['time']['converter']` must contain a function that takes a DataFrame as input and return a valid DateTime column as output, which will be used as a timestamp.
#
# `config['-9999_to_nan']` when set `True` will change -9999 to np.nan для for the proper work of the algorithm.
#
# `config['repair_time']` when set `True` will check the date-time column for gaps and monotony, and will perform regeneration by the first-last point taking into account the expected step length (calculated by the first pair of values in the series).

# %% [markdown] id="CXIuHMoSHMts"
# ## Full output file loading options

# %% id="tVJ_DRBrlpYd"
config = {}
config['debug'] = False  #True will load a small part of a file instead of a full length
config['-9999_to_nan'] = True #change -9999 to np.nan
config['repair_time'] = True #generate a new timestamp in case of errors

#####################
#in case of complex date-time columns
config['time'] = {}
config['time']['column_name'] = 'datetime'
def my_datetime_converter(x):
    date = x['date'].astype(str) #x['date'].dt.strftime('%d.%m.%Y') if is_datetime(x['date'].dtype) else x['date'].astype(str)
    time = x['time'].astype(str) #x['time'].dt.strftime('%H:%M') if is_datetime(x['time'].dtype) else x['time'].astype(str)

    x['tmp_datetime'] = date + " " + time
    #Check the format of a date and time in the Full Output file
    format = "%d.%m.%Y %H:%M"#"%d/%m/%Y %H:%M"# "%Y-%m-%d %H:%M"  #"%d/%m/%Y %H:%M"  #"%Y-%m-%d %H:%M:%S"
    return pd.to_datetime(x['tmp_datetime'], format=format)#dayfirst=True)#, format=format)
config['time']['converter'] = my_datetime_converter
#####################

###Type the names of your files and the path to them. If the files are loaded from the Google drive
###using !gdown command, just change the name of the file below
config['path'] = ['eddy_pro result_SSB 2023.csv']#['eddypro_GHG_biomet_CO2SS_Express_full_output_2023-03-29T020107_exp.csv']#['eddypro_noHMP_full_output_2014_1-5.csv', 'eddypro_noHMP_full_output_2014_5-12.csv']#['/content/eddypro_NCT_GHG_22-23dry_full_output.xlsx', '/content/eddypro_NCT_GHG_22wet_full_output.xlsx', '/content/eddypro_NCT_GHG_23wet_full output.xlsx']#'/content/new.csv'
# config['path'] = '/content/DT_Full output.xlsx'

# %% [markdown] id="S2Qc-fltJLaF"
# ## Biomet file loading options
# `use_biomet`: if there is no file with meteorological data, set it to False. Fluxes will be filtered and filled using the information from the full output file (air temperature and humidity)
#
# **It is necessary to change:**
#
# `###Type the names of your files and the path to them.`
#
# In config['path'] should be either path to a file (= ['1.csv']) if the filename is 1.csv or the list of paths in case of several files (= ['1.csv', '2.csv']). If we import files via the !gdown command from the Google drive, it is enough to specify in single quotes filename.extension. Do not miss the extension .csv!
#
# **It is necessary to check:**
#
# `  format = "%Y-%m-%d %H%M"  #"%d.%m.%Y %H:%M"  #yyyy-mm-dd HHMM`
#
# Check the order of the date (year, month, day) and date-time separators in the input files by opening them in a text editor I(Notepad). In the biomet file, by default, the date is written as 2011-11-12 and the time as 1200. It is encoded as "%Y-%m-%d %H%M". In other cases, change the date-time format code according to the instructions for the instruction in Data loading config section (see upper).

# %% id="H7E5LGx1DVsA"
config_meteo = {}
config_meteo ['use_biomet'] = True
config_meteo['debug'] = False  # True will load a small part of a file instead of a full length
config_meteo['-9999_to_nan'] = True #change -9999 to np.nan
config_meteo['repair_time'] = True #generate a new timestamp in case of errors

#####################
#in case of complex date-time columns
config_meteo['time'] = {}
config_meteo['time']['column_name'] = 'datetime'
def my_datetime_converter(x):
    format = "%Y-%m-%d %H%M"  #"%d.%m.%Y %H:%M"  #yyyy-mm-dd HHMM #Check the format of a date and time in the Biomet file
    return pd.to_datetime(x["TIMESTAMP_1"], format=format)
config_meteo['time']['converter'] = my_datetime_converter
#####################

###Type the names of your files and the path to them. If the files are loaded from the Google drive
###using !gdown command, just change the name of the file below
config_meteo['path'] = 'BiometFy4_2023.csv'#'BiometFy4_2016.csv'#'BiometNCT_2011-22.csv'

# %% [markdown] id="DtxFTNnEfENz"
# ## Selecting columns for graphs and filters

# %% id="nLnivFTtg9cu"
#Gather the summary information about the parameters of interest:
cols_to_investigate = []
cols_to_investigate.append("co2_flux")
cols_to_investigate.append("ch4_flux")
cols_to_investigate.append("LE")
cols_to_investigate.append("H")
cols_to_investigate.append("co2_strg")
cols_to_investigate.append("Ta_1_1_1")
cols_to_investigate.append("RH_1_1_1")
cols_to_investigate.append("VPD_1_1_1")
cols_to_investigate.append("P_1_1_1")
cols_to_investigate.append("SWIN_1_1_1")
cols_to_investigate.append("PPFD_1_1_1")
# cols_to_investigate.append("co2_signal_strength")
# cols_to_investigate.append("ch4_signal_strength")

cols_to_investigate =  [k.lower()for k in cols_to_investigate]

# %% [markdown] id="wVpYvr9_fKBU"
# ## Setting up parameters for the data analysis
#
# All settings for co2_flux will be applied to nee if it is chosen to calculate

# %% [markdown] id="FH2uRGi4p5Zj"
# ### Physical filtering

# %% id="pPemVdWVbq2E"
window_size = 10
calc_nee = True

# Output ID which will be added to the names of all output files and graphs
ias_output_prefix = 'tv_fy4'
ias_output_version = 'v01'

# %% [markdown] id="5MK90gyzQryZ"
# Filtering by quality flags. Data with flags in the range (-inf, val] will be marked as valid, and data with a flag value greater than the threshold will be excluded.

# %% id="ukl734CBblay"
qc_config = {}
qc_config['h'] = 1  #Change when using 1-9 flag system
qc_config['le'] = 1  #Change when using 1-9 flag system
qc_config['co2_flux'] = 1  #Change when using 1-9 flag system
qc_config['ch4_flux'] = 1  #Change when using 1-9 flag system

# %% [markdown] id="QPIFpLN_-8Uf"
# Filtering fluxes in certain meteorological conditions (by values of meteorological variables), possible options:
#
# *   `CO2SS_min` - will remove CO2_FLUX when co2_signal_strength is below the set threshold
# *   `p_rain_limit` - will remove H, LE and CO2_FLUX, for P_rain_1_1_1 above the set threshold
# *   `rain_forward_flag` - will remove values for the set number of records forward from each value filtered in the previous step
# *   `RH_max` - will remove LE and CO2_FLUX values for which RH_1_1_1 is greater than the specified threshold
# *   `use_day_filter` - if True, daily (Swin>`day_swin_limit`) NEEs greater than the set threshold (NEE>`day_nee_max`) will be excluded
# *   `use_night_filter` - if True, night (Swin<`day_swin_limit`) NEEs less than the set threshold (NEE<`night_nee_min`) will be excluded
# *   `day_nee_max` - threshold for NEE during daytime (excluding intense emission during daytime)
# *   `night_nee_min` - threshold for NEE at night (excluding intense net absorption at night)
# *   `day_swin_limit` - threshold of incoming shortwave radiation, defining daytime data (can be changed for stations beyond the Arctic Circle)
# *   `night_h_limits`, `night_le_limits` - plausible night ranges for H and LE
# *   `winter_nee_limits` - plausible range of NEE in winter (winter period is set separately in the section "winter period filtering, determine the dates!")
# *   `winter_ch4_flux_limits` - plausible range of methane flux in winter
# *   `CH4SS_min` - will remove CH4_FLUX when ch4_signal_strength is below the specified value
#
# If any of the parameters are missing or commented in this cell, filtering is not applied.
#
#
#
#
#
#

# %% id="vxpiAbWk2yYr"
meteo_filter_config = {}
meteo_filter_config['CO2SS_min'] = 80.

# These filters may not be needed for the closed-path eddy covariance systems
meteo_filter_config['p_rain_limit'] = .1
meteo_filter_config['rain_forward_flag'] = 2
# Relative humidity filter (intended to find the cases of formation of condensation): apply only if CO2SS and anemometer
# diagnostics are absent and the data were not filtered by these indicators during the calculation of 30-min data
# meteo_filter_config['RH_max'] = 98

# Plausible values at day/night-time
meteo_filter_config['use_day_filter'] = True
meteo_filter_config['use_night_filter'] = True
meteo_filter_config['day_nee_max'] = 5
meteo_filter_config['night_nee_min'] = -5
meteo_filter_config['day_swin_limit'] = 10
meteo_filter_config['night_h_limits'] = [-50, 20]
meteo_filter_config['night_le_limits'] = [-50, 20]

# Plausible values at winter. For the grass ecosystems the upper limit is usually lower
meteo_filter_config['winter_nee_limits'] = [-1, 5]
meteo_filter_config['winter_ch4_flux_limits'] = [-1, 1]
meteo_filter_config['CH4SS_min'] = 20.

# %% [markdown] id="utUX7SA4qA_I"
# ### Statistical filtering

# %% [markdown] id="wWISuF-xQCwq"
# Filtering parameters by absolute values. For `rh_1_1_1` values above the boundary are replaced with the boundary values instead of discarding. For `ppfd_1_1_1`, `swin_1_1_1` the minimum values are processed similarly.

# %% id="HQfIYFOd9uzi"
min_max_config  = {}
min_max_config['co2_flux'] = [-40, 40]
min_max_config['co2_strg'] = [-20, 20]
min_max_config['h'] = [-100, 800]
min_max_config['le'] = [-100, 1000]
min_max_config['u_star'] = [0, 10]
min_max_config['ta_1_1_1'] = [-50, 50]
min_max_config['p_1_1_1'] = [0, 100]
min_max_config['vpd_1_1_1'] = [0, 50]
min_max_config['rh_1_1_1'] = [0, 100]#max
min_max_config['swin_1_1_1'] = [0, 1200]#min
min_max_config['ppfd_1_1_1'] = [0, 2400]#min
min_max_config['rg_1_1_1'] = [0, 2400]#min
min_max_config['ch4_flux'] = [-10, 10]

# %% [markdown] id="vmyTKbV1RdjD"
# Filtering parameters based on the deviation from the average diurnal course in a moving window.
# * `sigmas` - plausible range of deviation from the average course; values outside the range are eliminated
# * `window` - window size in days for calculating the diurnal course
# * `min_periods` - minimum number of points for each 30-min interval in the window. If the window has less points then the course is not calculated, the filter is not applied.

# %% id="xfRVNYbFYzG3"
window_filter_config = {}

# Closed-path eddy covariance systems and less noisy data may need milder criteria (for example, 3 sigma)
window_filter_config['co2_flux'] = {'sigmas': 2, 'window': 10,  'min_periods': 4}
window_filter_config['ch4_flux'] = {'sigmas': 2, 'window': 10,  'min_periods': 4}

# If reliable data are deleted, it is recommended to increase the value of 'sigmas'
window_filter_config['ta_1_1_1'] = {'sigmas': 4, 'window': 10,  'min_periods': 4}
window_filter_config['u_star'] = {'sigmas': 4, 'window': 10,  'min_periods': 4}
for col in ['h', 'le', 'rh_1_1_1', 'vpd_1_1_1']:
    window_filter_config[col] = {'sigmas': 7, 'window': 10,  'min_periods': 4}
for col in ['swin_1_1_1', 'ppfd_1_1_1']:
    window_filter_config[col] = {'sigmas': 8, 'window': 10,  'min_periods': 4}

# %% [markdown] id="KF_MGD7pSGre"
# Filtering parameters above and below threshold by quantiles (drop-down points are eliminated)

# %% id="asO_t2tZmiD0"
quantile_filter_config = {}
quantile_filter_config['co2_flux'] = [0.01, 0.99]
quantile_filter_config['ch4_flux'] = [0.01, 0.99]
quantile_filter_config['co2_strg'] = [0.01, 0.99]

# %% [markdown] id="cPiTN288UaP3"
# Parameters for filtering by deviation from the neighboring points: MAD and Hampel filters.

# %% id="2b3eBVFUq3AU"
# madhampel_filter_config = {i:{'z': 5.5, 'hampel_window': 10} for i in cols_to_investigate if 'p_1_1_1' not in i}
madhampel_filter_config = {}

# Hard filtering: 'z'=4. Mild filtering: 'z'=7
madhampel_filter_config['co2_flux'] = {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['ch4_flux'] = {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['le'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['h'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['co2_strg'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'ta_1_1_1'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'rh_1_1_1'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'vpd_1_1_1'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'swin_1_1_1'] =  {'z': 8.0, 'hampel_window': 10}
madhampel_filter_config[ 'ppfd_1_1_1'] =  {'z': 8.0, 'hampel_window': 10}

# %% [markdown] id="wVF1vDm4EauW"
# # Loading data

# %% [markdown] id="LV9FvvtnVqdN"
# **It is necessary to change:**
#
# After !gdown, insert the characters after d/ and before the next / from the public link to the file located on Google Drive. For example, if the link is
# https://drive.google.com/file/d/1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB/view?usp=sharing,
# then the command will be written as
# `!gdown 1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB`
#
# `#Upload full output`  
# Here you need to write the symbols from the link to the full output file
#
# `#Upload biomet`  
# Here you need to type characters from the link to the biomet file

# %% id="KMu4IqY45HG6"
# Upload full output
# https://drive.google.com/file/d/1CGJmXyFu_pmzTLitG5aU8fwY8gW3CI1n/view?usp=sharing
# !gdown 1CGJmXyFu_pmzTLitG5aU8fwY8gW3CI1n

# Upload biomet
# https://drive.google.com/file/d/19XsOw5rRJMVMyG1ntRpibfkUpRAP2H4k/view?usp=sharing
# !gdown 19XsOw5rRJMVMyG1ntRpibfkUpRAP2H4k

# %% id="Xw5TapK10EhR"
data, time = bg.load_df(config)
data = data[next(iter(data))]  #it was dictionary
data_freq = data.index.freq

print("Timestamps interval for full_output: ", data.index[[0, -1]])
logging.info(f"Data loaded from {config['path']}")
logging.info("Time range for full_output: "+ " - ".join(data.index[[0,-1]].strftime('%Y-%m-%d %H:%M')))

# %% [markdown] id="6j7ombDYqyC8"
# Regularization: checking the ordering of timestamps. Removing duplicates, fill in gaps. Additional checking in case of loading several files.

# %% id="65DLIIucNOPe"
if config_meteo ['use_biomet']:
  data_meteo, time_meteo  = bg.load_df(config_meteo)
  data_meteo = data_meteo[next(iter(data_meteo))]  #it was dictionary
  meteo_freq = data_meteo.index.freq
  print("Диапазон времени метео: ", data_meteo.index[[0, -1]])
  logging.info(f"MeteoData loaded from {config_meteo['path']}")
  logging.info("Time range for meteo: "+ " - ".join(data_meteo.index[[0,-1]].strftime('%Y-%m-%d %H:%M')))

# %% id="3fVgA8UTMfJ3"
if config_meteo ['use_biomet']:
  if data_freq != meteo_freq:
    print("Resampling meteo data")
    logging.info(f"Resampling meteo data")
    data_meteo = data_meteo.asfreq(data_freq)

# %% id="rZbqd6adhHEP"
print("Columns in FullOutput \n", data.columns.to_list())
if config_meteo ['use_biomet']:
  print("Columns in meteo \n", data_meteo.columns.to_list())

# %% [markdown] id="FF78Wlq9rD_n"
# Merge into one DataFrame.

# %% id="9v0rxHehhZEI"
if config_meteo ['use_biomet']:
  data = data.join(data_meteo, how='outer', rsuffix='_meteo')
  data[time] = data.index
  data = bg.repair_time(data, time)
  if data[data_meteo.columns[-1]].isna().sum() == len(data.index):
    print("Bad meteo data range, skipping! Setting config_meteo ['use_biomet']=False")
    config_meteo ['use_biomet'] = False

points_per_day = int(pd.Timedelta('24H')/data_freq)

# %% id="C8lLDYOWzH2d"
data.columns = data.columns.str.lower()
if not config_meteo ['use_biomet']:
  for col in ['rh', 'vpd']:
    data[col+"_1_1_1"] = data[col]

# %% [markdown] id="ipknrLaeByCT"
# Checking for correct data type (example: presence of text instead of numbers):

# %% id="8LawdKUbB1_m"
cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength', 'rh_1_1_1', 'vpd_1_1_1', 'rg_1_1_1', 'p_rain_1_1_1', 'co2_signal_strength_7500_mean', 'CO2SS'.lower(), 'co2_signal_strength',
                'ch4_signal_strength_7500_mean', 'ch4SS'.lower(), 'ch4_signal_strength',
                'p_1_1_1', 'ta_1_1_1', 'co2_strg', 'le', 'h']


biomet_columns = []
if config_meteo ['use_biomet']:
  biomet_columns = data_meteo.columns.str.lower()
data_type_error_flag = False
for col in cols_2_check:
  if col not in data.columns:
    continue
  error_positions = data[col].fillna(0).apply(pd.to_numeric, errors='coerce').isna()
  if error_positions.any():
    logging.error(f"""Check input files for {col} column near:\n {error_positions[error_positions==True].index.strftime('%d-%m-%Y %H:%M').values} in {'biomet' if len(biomet_columns)>0 and col in  biomet_columns else 'data'} file""")
    data_type_error_flag = True
if data_type_error_flag:
  print("Data have some errors! Please check log file!")
  raise KeyboardInterrupt

# %% [markdown] id="QDHkyl_PruXE"
# # Preprocessing

# %% [markdown] id="Nh5MosYXS6aj"
# Renaming the columns to a single format, calculating VPD <-> RH, SWIN <-> RG and PAR <-> SWIN if absent.
#

# %% id="mAdYXJFdSRbJ"
have_rh_flag = False
have_vpd_flag = False
have_par_flag = False
have_swin_flag = False
have_rg_flag = False
have_p_flag = False
have_pr_flag = False
have_ppfd_flag = False

for col_name in data.columns:
  if 'u*' in col_name:
    print(f"renaming {col_name} to u_star")
    data = data.rename(columns={col_name: 'u_star'})
  if 'ppfd_in_1_1_1' in col_name:
    print(f"renaming {col_name} to ppfd_1_1_1")
    data = data.rename(columns={col_name: 'ppfd_1_1_1'})
  if 'sw_in_1_1_1' in col_name:
    print(f"renaming {col_name} to swin_1_1_1")
    data = data.rename(columns={col_name: 'swin_1_1_1'})
  if 'co2_signal_strength' in col_name:
    print(f"renaming {col_name} to co2_signal_strength")
    data = data.rename(columns={col_name: 'co2_signal_strength'})
  if "rh_1_1_1" in col_name:
    have_rh_flag =True
  if "vpd_1_1_1" in col_name:
    have_vpd_flag = True
  if 'swin' in col_name or 'sw_in' in col_name:
    have_swin_flag = True
  if 'par' in col_name:
    have_par_flag = True
  if 'rg_1_1_1' in col_name:
    have_rg_flag = True
  if 'p_1_1_1' in col_name:
    have_p_flag = True
  if 'p_rain_1_1_1' in col_name:
    have_pr_flag = True
  if 'ppfd_1_1_1' in col_name:
    have_ppfd_flag = True
  if col_name in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()] or 'co2_signal_strength' in col_name:
    print(f"renaming {col_name} to co2_signal_strength")
    data = data.rename(columns={col_name: 'co2_signal_strength'})
  if col_name in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()] or 'ch4_signal_strength' in col_name:
    print(f"renaming {col_name} to ch4_signal_strength")
    data = data.rename(columns={col_name: 'ch4_signal_strength'})


if not (have_ppfd_flag or have_swin_flag):
  print("NO PPFD and SWin")
else:
    if not have_ppfd_flag:
      data['ppfd_1_1_1'] = data['swin_1_1_1'] / 0.46
    if not have_swin_flag:
      data['swin_1_1_1'] = 0.46 * data['ppfd_1_1_1']
    have_ppfd_flag = True
    have_swin_flag = True


if not (have_rg_flag or have_swin_flag):
  print("NO RG AND SWIN")
else:
  print("Checking RG-SWIN pair")
  if not have_rg_flag:
    data['rg_1_1_1'] = data['swin_1_1_1']
  if not have_swin_flag:
    data['swin_1_1_1'] = data['rg_1_1_1']
    have_swin_flag = True


if not (have_p_flag or have_pr_flag):
  print("NO P and P_RAIN")
else:
  print("Checking P <-> P_rain pair")
  if not have_p_flag:
    data['p_1_1_1'] = data['p_rain_1_1_1']
  if not have_pr_flag:
    data['p_rain_1_1_1'] = data['p_1_1_1']


if not (have_vpd_flag or have_rh_flag):
  print("NO RH AND VPD")
else:
    if 'ta_1_1_1' in data.columns:
      temp_k = (data['ta_1_1_1'] + 273.15)
    else:
      temp_k = data['air_temperature']
    logE = 23.5518-(2937.4/temp_k)-4.9283*np.log10(temp_k)
    ehpa = np.power(10, logE)
    if not have_vpd_flag:
      print("calculating vpd_1_1_1 from rh")
      data['vpd_1_1_1'] = ehpa - (ehpa*data['rh_1_1_1']/100)
    if not have_rh_flag:
      print("calculating rh_1_1_1 from vpd")
      data['rh_1_1_1'] = ehpa


if not (have_par_flag or have_swin_flag):
  print("NO PAR and SWin")
else:
    if not have_par_flag:
      data['par'] = data['swin_1_1_1'] / 0.47#SWin=PAR*0.47
    if not have_swin_flag:
      data['swin_1_1_1'] = 0.47 * data['par']



for col_name in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()]:
  # print(data.columns.to_list())
  if col_name in data.columns.to_list():
    print(f"renaming {col_name} to co2_signal_strength")
    data = data.rename(columns={col_name: 'co2_signal_strength'})

for col_name in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()]:
  # print(data.columns.to_list())
  if col_name in data.columns.to_list():
    print(f"renaming {col_name} to ch4_signal_strength")
    data = data.rename(columns={col_name: 'ch4_signal_strength'})

if not config_meteo ['use_biomet'] or 'ta_1_1_1' not in data.columns:
    data['ta_1_1_1'] = data['air_temperature'] - 273.15
    logging.info("No Ta_1_1_1 column found, replaced by 'air_temperature'")

# %% [markdown] id="soyyX-MCbaXt"
# ## Calculating NEE from CO2_flux and storage

# %% [markdown] id="lqWwGSMObro4"
# Checking the storage. The storage calculated by one vertical level in EddyPro is not always reliable. Correctness is checked by the proper diurnal course: there should be an accumulation during the night, and a sharp decrease in the morning.

# %% [markdown] id="2yqwO7Uhcjmz"
# Filtering co2_strg to remove values above and below threshold quantiles. Filling co2_strg gaps of 3 points or less with linear interpolation. The resulting filtered and filled co2_strg values are plotted. You make a decision whether to sum co2_flux and co2_strg to obtain NEE or to continue working with co2_flux.

# %% id="cjt05XXtbr69"
# Gaps shorter then 3 points are linearly interpolated
if calc_nee and 'co2_strg' in data.columns:
  tmp_data = data.copy()
  tmp_data['co2_strg_tmp'] = tmp_data['co2_strg'].copy()
  tmp_filter_db =  {'co2_strg_tmp': []}
  if 'co2_strg' in  quantile_filter_config.keys():
    tmp_q_config = {'co2_strg_tmp':quantile_filter_config['co2_strg']}
  else:
    tmp_q_config = {}
  tmp_filter_db = {'co2_strg_tmp':[]}
  tmp_data, tmp_filter_db = quantile_filter(tmp_data, tmp_filter_db, tmp_q_config)
  tmp_data.loc[~get_column_filter(tmp_data, tmp_filter_db, 'co2_strg_tmp').astype(bool), 'co2_strg_tmp'] = np.nan
  # tmp_data['co2_strg_tmp'] = tmp_data['co2_strg_tmp'].interpolate(limit=3)
  # tmp_data['co2_strg_tmp'].fillna(bg.calc_rolling(tmp_data['co2_strg_tmp'], rolling_window=10 , step=points_per_day, min_periods=4))
  basic_plot(tmp_data, ['co2_strg_tmp'], tmp_filter_db, steps_per_day=points_per_day)
  print(tmp_q_config, tmp_filter_db, tmp_data['co2_strg_tmp_quantilefilter'].value_counts())

# %% id="2IQ7W6pslYF-"
# Decide whether to sum co2_flux and co2_strg_filtered_filled for obtaining NEE
calc_with_strg = False   #To calculate NEE type True.
logging.info(f"calc_with_strg is set to {calc_with_strg}")
# For working with co2_flux, ignoring co2_strg, type False

# %% id="ueuvsNxYdtgs"
if calc_nee and 'co2_strg' in data.columns:
  if calc_with_strg:
    data['nee'] = (tmp_data['co2_flux'] + tmp_data['co2_strg_tmp']).copy()
  else:
    data['nee'] = data['co2_flux'].copy()
  del tmp_data
  if 'nee' not in cols_to_investigate:
    cols_to_investigate.append('nee')
  for filter_config in [qc_config, meteo_filter_config, min_max_config, window_filter_config, quantile_filter_config, madhampel_filter_config]:
    if 'co2_flux' in filter_config:
      filter_config['nee'] = filter_config['co2_flux']

# %% [markdown] id="mUgwuaFYribB"
# #Overview of statistics for the columns of interest

# %% id="dhcplCMbXtkK"
cols_to_investigate = [p for p in cols_to_investigate if p in data.columns]

# %% id="YfusqiotOi3n"
data.loc[:, cols_to_investigate].describe()

fig, axs = plt.subplots(ncols=min(3, len(cols_to_investigate)), nrows=int(np.ceil(len(cols_to_investigate)/3)), squeeze=False, figsize=(13, 8))

for ind, ax in enumerate(axs.reshape(-1)):
  if ind >= len(cols_to_investigate):
    break
  feature = cols_to_investigate[ind]
  ax.boxplot(data[feature].to_numpy()[~np.isnan(data[feature].to_numpy())])
  ax.set_title(f"Boxplot for {feature}")
plt.tight_layout()
fig.show()

data[cols_to_investigate].describe()

# %% [markdown] id="0oJLXYGbr93S"
# # Physical data filtering

# %% id="apGNk8eBxgBv"
plot_data = data.copy()
filters_db = {col: [] for col in plot_data.columns.to_list()}
print(plot_data.columns.to_list())

# %% [markdown] id="BL_6XxGGsCBK"
# ## using quality flags

# %% id="GGwe7_uU1C8U"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = qc_filter(plot_data, filters_db, qc_config)

# %% [markdown] id="M_gKSTNYyzjS"
# ## accounting for CO2SS and CH4SS

# %% id="viq7BZue9Ett"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = meteorological_co2ss_filter(plot_data, filters_db, meteo_filter_config)

# %% id="5RrPfxfiJGhN"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = meteorological_ch4ss_filter(plot_data, filters_db, meteo_filter_config)

# %% [markdown] id="qwqVDeH6y73_"
# ## plausible RH values

# %% id="11isfvNZ9FGu"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = meteorological_rh_filter(plot_data, filters_db, meteo_filter_config)

# %% [markdown] id="oSX2h9QzzFkT"
# ## rain events

# %% id="jz696mc09FlB"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  plot_data, filters_db = meteorological_rain_filter(plot_data, filters_db, meteo_filter_config)

# %% [markdown] id="Xy2y00P1zJtZ"
# ## day-time and night-time plausible ranges

# %% id="ED_Qh6TS0Qkc"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  plot_data, filters_db = meteorological_night_filter(plot_data, filters_db, meteo_filter_config)

# %% id="X3Vguu8MK635"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  plot_data, filters_db = meteorological_day_filter(plot_data, filters_db, meteo_filter_config)

# %% [markdown] id="fzfTJdNe68Eu"
# ## winter period filtering, determine the dates!

# %% id="wJ87D57S7A91"
if ('winter_nee_limits' in meteo_filter_config.keys()) or ('winter_ch4_flux_limits' in meteo_filter_config.keys()):
  plot_albedo(plot_data, filters_db)

# %% id="Z_RAYINf67PO"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  date_ranges = [
      ['01.01.2023 00:00', '26.03.2023 00:00'],
      ['13.11.2023 00:00', '31.12.2023 00:00'],
  ]
  # date_ranges = []
  # date_ranges.append(['25.8.2014 00:00', '26.8.2014 00:00'])
  plot_data, filters_db = winter_filter(plot_data, filters_db, meteo_filter_config, date_ranges)

# %% [markdown] id="iipFLxf6fu5Y"
# Footprint filtering is expected further
#
# `fetch = 1 #or 0. 1 - remain, 0 – eliminate`

# %% [markdown] id="UAdRtCPGq6_y"
# # Statistical data filtering

# %% [markdown] id="LcwZplknsHJv"
# ## by minimum and maximum acceptable values

# %% id="FyJaM1zC1DDg"
# if config_meteo ['use_biomet']:
unroll_filters_db = filters_db.copy()
plot_data, filters_db = min_max_filter(plot_data, filters_db, min_max_config)

# %% [markdown] id="j62U1dw8sTEm"
# ## by quantiles

# %% id="aNQ4XDK01DME"
# if config_meteo ['use_biomet']:
unroll_filters_db = filters_db.copy()
plot_data, filters_db = quantile_filter(plot_data, filters_db, quantile_filter_config)

# %% [markdown] id="7Sg76Bwasnb4"
# ## by deviation from the average diurnal course

# %% id="uoDvHhoQ2MMe"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = std_window_filter(plot_data, filters_db, window_filter_config)

# %% [markdown] id="iXl5RdINss9D"
# ## MAD & Hampel outliers filtering

# %% colab={"background_save": true} id="gl9cImVr2MO3"
unroll_filters_db = filters_db.copy()
plot_data, tmp_filter = mad_hampel_filter(plot_data, filters_db, madhampel_filter_config)

# %% [markdown] id="iu8MLKyh1AFk"
# ## Manual filtering
#
# If you need to remove some intervals manually
#

# %% colab={"background_save": true} id="ADy534At0_fN"
#  the filter excludes values from the first to the last one inclusively
man_ranges = [
    # ['1.5.2023 00:00', '1.6.2023 00:00'],
    # ['25.8.2023 12:00', '25.8.2023 12:00'],
]
for start, stop in man_ranges:
  plot_data, tmp_filter = manual_filter(plot_data, filters_db, col_name="nee", range=[start, stop], value=0)

# %% [markdown] id="APyqyqSEHx3K"
# ## To undo the last filter
# Doesn't work with the filters which were run several times

# %% colab={"background_save": true} id="IYmSC2gpH4zo"
#filters_db = unroll_filters_db.copy()

# %% [markdown] id="quGbtDaJ_gID"
# ## Summary table of filter results

# %% colab={"background_save": true} id="Pg78qGJ9_miW"
all_filters = {}
for key, filters in filters_db.items():
   if len(filters) > 0:
    pl_data = plot_data.copy()
    for filter_name in filters:
      all_filters[filter_name] = []
      all_filters[filter_name].append(len(pl_data.index))
      filtered_amount = len(pl_data.query(f"{filter_name}==0").index)
      all_filters[filter_name].append(filtered_amount)
      # old_val =  len(pl_data.index)
      pl_data = pl_data.query(f"{filter_name}==1")
      # print(filter_name, filtered_amount, len(pl_data.index) - old_val)
fdf_df = pd.DataFrame(all_filters)
print("What percentage of data from all data (in %) was eliminated:")
print(fdf_df.iloc[1]/len(plot_data)*100)
logging.info("What percentage of data from all data (in %) was eliminated:")
logging.info(fdf_df.iloc[1]/len(plot_data)*100)

# %% [markdown] id="gA_IPavss0bq"
# # Drawing graphs

# %% [markdown] id="ijPM6mnJtMv8"
# ## Plotting the results of data filtering

# %% colab={"background_save": true} id="50Xhczc-BRc2"
plot_terator = iter(cols_to_investigate)

# %% [markdown] id="uat4oESzU4__"
# To free up memory and ensure the proper work of the Colab, the graphs will be displayed one by one when the cell is rerun.

# %% colab={"background_save": true} id="NhNoFAd7DqNN"
col2plot = next(plot_terator, False)
col2plot = 'nee' #Insert the parameter of interest: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1, co2_signal_strength, ch4_flux
# Or comment the previous line and rerun the cell for the switching to the next parameter
if col2plot:
  make_filtered_plot(plot_data, col2plot, filters_db)
else:
  print("No more data, start from the begining!")
  plot_terator = iter(cols_to_investigate)

# %% colab={"background_save": true} id="ZG_wF2qW-Qwb"
# #linear gapfilling, limit is the permitted maximal number of the consecutive missed values
# for col in cols_to_investigate:
#   plot_data[col] = plot_data[col].interpolate(limit=5)

# %% colab={"background_save": true} id="VtJ8wyx2-XCX"
# #Gapfilling with the diurnal course
# for col in cols_to_investigate:
#   plot_data[col].fillna(bg.calc_rolling(plot_data[col], rolling_window=10, step=points_per_day, min_periods=7))

# %% [markdown] id="MwuXRVTMtBz2"
# ## Plotting the average diurnal course for the filtered data
#

# %% colab={"background_save": true} id="pWDTiucTgRlI"
plot_terator = iter(cols_to_investigate)

# %% colab={"background_save": true} id="COKiwe7020D4"
#The example of the calculation of the diurnal course

col2plot = next(plot_terator, False)
#Can be chosen manually
# col2plot = 'h'#"co2_flux"
col2plot = ['nee', 'le'] #Insert the parameter of interest: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
#Or rerun the cell for the switching to the next parameter
if col2plot:
  basic_plot(plot_data, col2plot, filters_db, steps_per_day=points_per_day)
else:
  print("No more data, start from the begining!")
  plot_terator = iter(cols_to_investigate)

# %% [markdown] id="RKEg6YBstXMp"
# ## Heat maps of fluxes for the filtered data

# %% colab={"background_save": true} id="mCUJYURKEL-f"
for col in ['nee', 'le', 'h']: #Insert the parameter of interest: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
#Or rerun the cell for the switching to the next parameter
  plot_nice_year_hist_plotly(plot_data, col ,time, filters_db)

# %% [markdown] id="EFscf-JZt3_R"
# # Recording the output files

# %% [markdown] id="dokSxicNtdva"
# ## A file for REddyProc

# %% [markdown] id="tDqsi61kSeak"
# Creating a header for the REddyProc file and save the required variables, the filtering is taken into account. The output file has the 3rd level.

# %% colab={"background_save": true} id="YVu2UrCzLqb4"
reddyproc_filename = f"REddyProc_{ias_output_prefix}_{int(plot_data[time].dt.year.median())}.txt"
output_template = {'Year': ['-'],	'DoY': ['-'],	'Hour': ['-'],	'NEE': ['umol_m-2_s-1'],	'LE': ['Wm-2'],	'H': ['Wm-2'],	'Rg': ['Wm-2'],	'Tair': ['degC'], 	'Tsoil': ['degC'],	'rH': ['%'], 	'VPD': ['hPa'], 	'Ustar': ['ms-1'],	'CH4flux': ['umol_m-2_s-1']}

# %% colab={"background_save": true} id="GFulh7FtNWtM"
eddy_df = plot_data.copy()

for column, filter in filters_db.items():
  filter = get_column_filter(eddy_df, filters_db, column)
  eddy_df.loc[~filter.astype(bool), column] = np.nan


eddy_df['Year'] = eddy_df[time].dt.year
eddy_df['DoY'] = eddy_df[time].dt.dayofyear
eddy_df['Hour'] = eddy_df[time].dt.hour + eddy_df[time].dt.minute/60

eddy_df['NEE'] = eddy_df['nee'].fillna(-9999)
eddy_df['LE'] = eddy_df['le'].fillna(-9999)
eddy_df['H'] = eddy_df['h'].fillna(-9999)
if 'swin_1_1_1' in eddy_df.columns:
  eddy_df['Rg'] = eddy_df['swin_1_1_1'].fillna(-9999)
else:
  print("WARNING! No swin_1_1_1!")

if config_meteo ['use_biomet']:
  eddy_df['Tair'] = eddy_df['ta_1_1_1'].fillna(-9999)
  eddy_df['rH'] = eddy_df['rh_1_1_1'].fillna(-9999)
  eddy_df['VPD'] = eddy_df['vpd_1_1_1'].fillna(-9999)
else:
  eddy_df['Tair'] = (eddy_df['air_temperature'] - 273.15).fillna(-9999)
  eddy_df['rH'] = eddy_df['rh'].fillna(-9999)
  eddy_df['VPD'] = eddy_df['vpd'].fillna(-9999)

if 'ts_1_1_1' in eddy_df.columns:
  eddy_df['Tsoil'] = eddy_df['ts_1_1_1'].fillna(-9999)

eddy_df['Ustar'] = eddy_df['u_star'].fillna(-9999)

if 'ch4_flux' in eddy_df.columns:
  eddy_df['CH4flux'] = eddy_df['ch4_flux'].fillna(-9999)

i=0
while eddy_df.iloc[i]['Hour'] != 0.5:
  i += 1
eddy_df = eddy_df.iloc[i:]

if len(eddy_df.index) < 90 * points_per_day:
  print("WARNING!  < 90 days in reddyproc file!")

pd.DataFrame({key: item for key, item in output_template.items() if key in eddy_df.columns}).to_csv(os.path.join('output', reddyproc_filename), index=False, sep=' ')
eddy_df.to_csv(os.path.join('output', reddyproc_filename),  index=False, header=False, columns = [i for i in output_template.keys()  if i in eddy_df.columns], mode='a', sep=' ')
del eddy_df
logging.info(f"REddyProc file saved to {os.path.join('output', reddyproc_filename)}")

# %% [markdown] id="62o5-p8ZzR5T"
# ## A file for Information and Analytical System used in the RuFlux network (IAS)

# %% [markdown] id="e50f7947"
# Level 2 file, written from the input data **without taking into account** filtering

# %% colab={"background_save": true} id="yaLoIQmtzaYd"
if config_meteo ['use_biomet']:
	ias_df = plot_data.copy()
	for column, filter in filters_db.items():
		filter = get_column_filter(ias_df, filters_db, column)
		ias_df.loc[~filter.astype(bool), column] = np.nan
	ias_df = ias_df.fillna(-9999)

	col_match =  {"co2_flux" : "FC_1_1_1", "qc_co2_flux" : "FC_SSITC_TEST_1_1_1", "LE" : "LE_1_1_1",
		"qc_LE" : "LE_SSITC_TEST_1_1_1", "H" : "H_1_1_1", "qc_H" : "H_SSITC_TEST_1_1_1", "Tau" : "TAU_1_1_1",
		"qc_Tau" : "TAU_SSITC_TEST_1_1_1", "co2_strg" : "SC_1_1_1", "co2_mole_fraction" : "CO2_1_1_1",
		"h2o_mole_fraction" : "H2O_1_1_1", "sonic_temperature" : "T_SONIC_1_1_1", "u_star" : "USTAR_1_1_1",
		"Ta_1_1_1" : "TA_1_1_1", "Pa_1_1_1" : "PA_1_1_1", "Swin_1_1_1" : "SW_IN_1_1_1", "Swout_1_1_1" : "SW_OUT_1_1_1",
		"Lwin_1_1_1" : "LW_IN_1_1_1", "Lwout_1_1_1" : "LW_OUT_1_1_1", "PPFD_1_1_1" : "PPFD_IN_1_1_1",
		"Rn_1_1_1" : "NETRAD_1_1_1", "MWS_1_1_1" : "WS_1_1_1", "Ts_1_1_1" : "TS_1_1_1", "Ts_2_1_1" : "TS_2_1_1",
		"Ts_3_1_1" : "TS_3_1_1", "Pswc_1_1_1" : "SWC_1_1_1", "Pswc_2_1_1" : "SWC_2_1_1", "Pswc_3_1_1" : "SWC_3_1_1",
		"SHF_1_1_1" : "G_1_1_1", "SHF_2_1_1" : "G_2_1_1", "SHF_3_1_1" : "G_3_1_1", "L" : "MO_LENGTH_1_1_1",
		"(z-d)/L" : "ZL_1_1_1", "x_peak" : "FETCH_MAX_1_1_1", "x_70%" : "FETCH_70_1_1_1", "x_90%" : "FETCH_90_1_1_1",
		"ch4_flux" : "FCH4_1_1_1", "qc_ch4_flux" : "FCH4_SSITC_TEST_1_1_1", "ch4_mole_fraction" : "CH4_1_1_1", "ch4_strg" : "SCH4_1_1_1",
		"ch4_signal_strength" : "CH4_RSSI_1_1_1", "co2_signal_strength" : "CO2_STR_1_1_1", "rh_1_1_1": "RH_1_1_1", "vpd_1_1_1": "VPD_1_1_1"}
	col_match = {key.lower(): item for key, item in col_match.items()}

	ias_df = ias_df.rename(columns=col_match)
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']
	var_cols = [col_match[col] for col in col_match.keys() if col_match[col] in ias_df.columns]

	new_time = pd.DataFrame(index=pd.date_range(start=f"01.01.{ias_df[time].dt.year.min()}", end=f"01.01.{ias_df[time].dt.year.max()}",
                                                freq=ias_df.index.freq, inclusive='left'))
	ias_df = new_time.join(ias_df, how='left')
	ias_df[time] = ias_df.index

	ias_df['TIMESTAMP_START'] = ias_df[time].dt.strftime('%Y%m%d%H%M')
	ias_df['TIMESTAMP_END'] = (ias_df[time] + pd.Timedelta(0.5, "H")).dt.strftime('%Y%m%d%H%M')
	ias_df['DTime'] = np.round(ias_df[time].dt.dayofyear + 1./48*2*ias_df[time].dt.hour + 1./48*(ias_df[time].dt.minute//30), decimals=3)

	if 'h_strg' in ias_df.columns:
		ias_df['SH_1_1_1'] = ias_df['h_strg']
		var_cols.append('SH_1_1_1')
	if 'le_strg' in ias_df.columns:
		ias_df['SLE_1_1_1'] = ias_df['le_strg']
		var_cols.append('SLE_1_1_1')

	if 'SW_IN_1_1_1' in ias_df.columns:
		ias_df['SW_IN_1_1_1'] = data['swin_1_1_1']

	ias_year = ias_df[time].dt.year.min()
	var_cols.sort()
	col_list_ias = time_cols + var_cols + [time]
	print(col_list_ias)
	ias_df = ias_df[col_list_ias]

	for year in ias_df.index.year.unique():
		ias_filename = f"{ias_output_prefix}_{year}_{ias_output_version}.csv"
		save_data = ias_df.loc[ias_df[time].dt.year==year]
		save_data = save_data.drop(time, axis=1)
		save_data = save_data.fillna(-9999)
		if len(save_data.index) >= 5:
			save_data.to_csv(os.path.join('output',ias_filename), index=False)
			logging.info(f"IAS file saved to {os.path.join('output',ias_filename)}.csv")
		else:
			try:
				os.remove(os.path.join('output',ias_filename))
			except Exception as e:
				print(e)

			print(f"not enough data for {year}")
			logging.info(f"{year} not saved, not enough data!")
	# ias_filename = f"{ias_output_prefix}_{ias_year}_{ias_output_version}.csv"
	# ias_df.to_csv(os.path.join('output',ias_filename), index=False)
	# logging.info(f"IAS file saved to {os.path.join('output',ias_filename)}.csv")

# %% [markdown] id="Pm8hiMrb_wRW"
# ## File for FAT
# Level 3 file (filtered data) ready for input into the Flux Analysis Tool

# %% [markdown] id="0ll51nOal6Lz"
# ![image.png](data:image/png;base64,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)

# %% colab={"background_save": true} id="w9hkPLkB_zd1"
if config_meteo ['use_biomet']:
  fat_output_template = {'DoY': ['--'], r'u*': ['m s-1'],	'H': ['W m-2'], 'lE': ['-'],	'NEE': ['umol m-2 s-1'],	'PPFD': ['umol m-2 s-1'], 'Ta':['oC'], 'VPD':['kPa'], 'PPFD_gapfilling': ['umol m-2 s-1'], 'Ta_gapfilling': ['oC'], 'VPD_gapfilling': ['kPa'], 'period': ['--']}

  fat_df = plot_data.copy()


  for column, filter in filters_db.items():
    filter = get_column_filter(fat_df, filters_db, column)
    fat_df.loc[~filter.astype(bool), column] = np.nan



  fat_df['DoY'] = np.round(fat_df[time].dt.dayofyear + fat_df[time].dt.hour/24. + fat_df[time].dt.minute/24./60., decimals=3)
  fat_df[r'u*'] = fat_df['u_star'].fillna(-99999)
  fat_df['H'] = fat_df['h'].fillna(-99999)
  fat_df['lE'] = fat_df['le'].fillna(-99999)
  fat_df['NEE'] = fat_df['nee'].fillna(-99999)
  if 'ppfd_1_1_1' in fat_df.columns:
    fat_df['PPFD'] = fat_df['ppfd_1_1_1'].fillna(-99999)
    fat_df['PPFD_gapfilling'] = fat_df['ppfd_1_1_1'].interpolate(limit=3).fillna(bg.calc_rolling(fat_df['ppfd_1_1_1'], rolling_window=10 , step=points_per_day, min_periods=4)).fillna(-99999)
  else:
    logging.info(f"FAT file will have no PPFD")
    fat_output_template.pop('PPFD')

  if not config_meteo ['use_biomet']:
    fat_df['ta_1_1_1'] = fat_df['air_temperature'] - 273.15

  fat_df['Ta'] = fat_df['ta_1_1_1'].fillna(-99999)
  fat_df['VPD'] = fat_df['vpd_1_1_1'].fillna(-99999)

  fat_df['period'] = fat_df.index.month%12//3 + 1

  fat_df['Ta_gapfilling'] = fat_df['ta_1_1_1'].interpolate(limit=3).fillna(bg.calc_rolling(fat_df['ta_1_1_1'], rolling_window=10 , step=points_per_day, min_periods=4)).fillna(-99999)
  fat_df['VPD_gapfilling'] = fat_df['vpd_1_1_1'].interpolate(limit=3).fillna(bg.calc_rolling(fat_df['vpd_1_1_1'], rolling_window=10 , step=points_per_day, min_periods=4)).fillna(-99999)

  for year in fat_df.index.year.unique():
    fat_filename = f"FAT_{ias_output_prefix}_{year}.csv"
    pd.DataFrame(fat_output_template).to_csv(os.path.join('output',fat_filename), index=False)
    save_data = fat_df.loc[fat_df[time].dt.year==year]
    if len(save_data.index) >= 5:
      save_data.to_csv(os.path.join('output',fat_filename),  index=False, header=False, columns = [i for i in fat_output_template.keys()], mode='a')#, sep=' ')
    else:
      try:
        os.remove(os.path.join('output',fat_filename))
      except Exception as e:
        print(e)

      print(f"not enough data for {year}")
      logging.info(f"{year} not saved, not enough data!")
  del fat_df
  logging.info(f"FAT file saved to {fat_filename}")

# %% [markdown] id="GQ1bpermu8eq"
# ## File with all filtered data
# The file contains the original variables (fluxes, meteorological variables). The "tmp_datetime" column is the result of forming a single date-time from the two columns of the full output file - date, time. The "datetime" column is the result of the date-time correction for the tmp_datetime column. "datetime_meteo" is the result of the date-time correction for the "timestamp_1" column. The file contains flags for each filter to each variable (fluxes, meteorology) in binary format: 1 means that filter was not applied, 0 - applied.

# %% colab={"background_save": true} id="pk1lGANovC5U"
full_column_list = [c for c in plot_data.columns]
full_column_list = full_column_list.insert(0, full_column_list.pop(full_column_list.index(time)))
if 'date' in plot_data.columns:
  plot_data.loc[plot_data['date'].isna(), 'date'] = plot_data[time].dt.date
if 'time' in plot_data.columns:
  plot_data.loc[plot_data['time'].isna(), 'time'] = plot_data[time].dt.time
plot_data.fillna(-9999).to_csv(os.path.join('output','output_all.csv'), index=None, columns=full_column_list)
logging.info(f"Basic file saved to {os.path.join('output','output_all.csv')}")

# %% [markdown] id="-MSrgUD0-19l"
# ## Summary file of filtered results
# Short output file after filtering. Contains important input variables (meteorological parameters and fluxes), filtered important variables (index _filtered), integral flag for each variable, average diurnal cycles in 30- and 10-day windows for filtered variables.

# %% colab={"background_save": true} id="22dPWc2u-6IG"
columns_to_save = ['Date', 'Time', 'DoY', 'ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg', 'ch4_flux', 'u_star']

basic_df = plot_data.copy()

basic_df['Date'] = basic_df[time].dt.date
basic_df['Time'] = basic_df[time].dt.time
basic_df['DoY'] = np.round(basic_df[time].dt.dayofyear + basic_df[time].dt.hour/24. + basic_df[time].dt.minute/24./60., decimals=3)

if not config_meteo ['use_biomet']:
  basic_df['ta_1_1_1'] = basic_df['air_temperature'] - 273.15
#meteo
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
  # print(f"{col}(_[1-9]){{1,4}})")
  col_pos = [bool(re.fullmatch(f"{col}(_[1-9]){{1,4}}", col_in)) for col_in in  basic_df.columns]
  if not any(col_pos):
    continue
  else:
    real_col_name = basic_df.columns[np.argmax(col_pos)]
    basic_df[col] = basic_df[real_col_name]

#Filtered fluxes
for col in ['nee', 'h', 'le', 'co2_strg', 'ch4_flux']:
  if col not in basic_df.columns:
    continue
  basic_df[f"{col}_filtered"] = basic_df[col]
  filter = get_column_filter(basic_df, filters_db, col)
  basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
  columns_to_save.append(f"{col}_filtered")

#Filtered meteo
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
  if col not in basic_df.columns:
    continue
  basic_df[f"{col}_filtered"] = basic_df[col]
  filter = get_column_filter(basic_df, filters_db, col)
  basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
  columns_to_save.append(f"{col}_filtered")

#Flags
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg', 'nee', 'ch4_flux']: #['nee', 'ch4', 'le', 'h']:
  if col not in basic_df.columns:
    continue
  basic_df[f"{col}_integral_flag"] = get_column_filter(basic_df, filters_db, col)
  columns_to_save.append(f"{col}_integral_flag")

# for key, item in filters_db.items():
#   columns_to_save = columns_to_save + item

for col in ['h', 'le', 'nee', 'rg', 'ppfd', 'ta', 'rh', 'vpd', 'ch4_flux']:
  if f"{col}_filtered" not in basic_df.columns:
    print(f"No {col}_filtered in file")
    continue
  col_out = col
  if col == "ppfd":
    col_out = "rg"
  basic_df[f'{col_out}_10d'] = bg.calc_rolling(basic_df[f"{col}_filtered"], rolling_window=10 , step=points_per_day, min_periods=7)
  basic_df[f'{col_out}_30d'] = bg.calc_rolling(basic_df[f"{col}_filtered"], rolling_window=30 , step=points_per_day, min_periods=7)
  columns_to_save.append(f'{col_out}_10d')
  columns_to_save.append(f'{col_out}_30d')

basic_df = basic_df[[col for col in columns_to_save if col in basic_df.columns]]
basic_df = basic_df.fillna(-9999)
basic_df.to_csv(os.path.join('output','output_summary.csv'), index=None)
logging.info(f"New basic file saved to {os.path.join('output','output_summary.csv')}")

# %% [markdown] id="775a473e"
# # Processing with the REddyProc tool
# This block performs 1) filtering by the friction velocity threshold (u* threshold), 2) filling gaps in meteorological variables and 30-minute fluxes, 3) separating NEE into gross primary production (GPP) and ecosystem respiration (Reco), 4) calculating daily, monthly, annual averages and the average diurnal cycle by months.

# %% [markdown] id="a8aa54de"
# ## Technical block
# Required and automatically launched if a Google Colab environment is detected.
# Loads scripts used in cells into a directory `src` and prepares the R environment.

# %% colab={"background_save": true} id="06859169"
# %load_ext autoreload
# %autoreload 2

# def section_*(): + ipynb to py convert?
try:
    import google.colab
except ImportError:
    class StopExecution(Exception):
        def _render_traceback_(self):
            return ['Colab env not detected. Current cell is only for Colab.']
    raise StopExecution()

# cur_dir = %pwd
assert cur_dir == '/content'

# !mkdir -p src/repo1/
# %cd src/repo1/

# !git -c init.defaultBranch=main init
# !git sparse-checkout init
# !git sparse-checkout set "src"
# !git remote add origin https://github.com/PlaZMaD/climate.git
# !git fetch --depth 1 origin main
# !git -c advice.detachedHead=false checkout FETCH_HEAD

# %cd /content
# !cp -r src/repo1/src .

# 1.3.2 vs 1.3.3 have slightly different last columns
# alternative for windows
# install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")
setup_colab_r_code = """
install_if_missing <- function(package, version, repos) {
    if (!require(package, character.only = TRUE)) {
        remotes::install_version(package, version = version, upgrade = "never", repos = repos)
        library(package, character.only = TRUE)
    }
}
# sink redirect is required to improve ipynb output
sink(stdout(), type = "message")
install_if_missing("REddyProc", "1.3.3", repos = 'http://cran.rstudio.com/')
sink()
"""
from rpy2 import robjects
robjects.r(setup_colab_r_code)

from src.ipynb_helpers import enable_word_wrap
enable_word_wrap()

# %% [markdown] id="034b04a5"
# ## Filtering and gapfilling
#
# `ig.eddyproc_options` are the settings that correspond to the options of [the online tool](https://www.bgc-jena.mpg.de/REddyProc/ui/REddyProc.php).
#
# **It is necessary to check:**  
#
# Enabling detection of the conditions of weak turbulence  
# `is_to_apply_u_star_filtering=True`
#
# The Eddy Covariance method is applicable only in the conditions of the developed turbulence. When the friction velocity (*uStar* column) is below a certain threshold, the CO2 flux may be underestimated. Flux data in these conditions are replaced by gaps.
#
# Selection of the method of marking seasons, for each of which the saturation level is determined separately. `Continuous` - the beginning of seasons is in March, June, September, and December, December is included in the *next* year. `WithinYear` treats each year separately. `User` divides the year by the user-defined *season* column.  
# `u_star_seasoning="Continuous"`
#
# Compared to the original REddyProc tool, this notebook adds the ability to substitute a custom threshold value in cases where the threshold cannot be calculated (e.g., if data are lacking or solar income radiation *Rg* is missing). For grassland ecosystems, you can use a minimal threshold of `0.01`, for forest ecosystems - `0.1`, to disable substitution - `None`.  
# `ustar_threshold_fallback=0.01`
#
# REddyProc by default applies the uStar threshold only at night, which requires the *Rg* column to determine day/night-time. The following experimental option allows you to ignore the absence of *Rg* and apply the threshold to all data, regardless of the time of day  
# `ustar_allowed_on_days=True`
#
#  If an error occurs during filtering, a warning appears in the cell log and the cell reruns with a transition to the gap filling. Gap filling in the 30-minute fluxes corresponds to the online tool and is enabled by default.
#
# Enable and select one or both methods of partitioning the CO2 flux into the gross primary production (GPP) and the ecosystem respiration (Reco). The method `Reichstein05` performs the separation based on the night-time data, the method `Lasslop10` uses the day-time data.  
# `is_to_apply_partitioning=True`  
# `partitioning_methods=["Reichstein05", "Lasslop10"]`
#
# If there is no data on Rg, the partitioning will not be performed! To correctly run the cell in this case, set  
# `is_to_apply_partitioning=False`
#
# Latitude, longitude, time zone  
# `latitude = 56.5`  
# `longitude = 32.6`  
# `timezone = +3`  
#
# To use air or soil temperature for gapfilling  
# `temperature_data_variable="Tair"`
# or  
# `temperature_data_variable="Tsoil"`
#
# **Options that are not intended to be changed in this notebook:**
#
# EddyProc only has the moving point method `RTw` for determining the uStar threshold  
# `u_star_method="RTw"`  
# Iteratively assessing the accuracy of the calculated u* threshold (bootstrap)  
# `is_bootstrap_u_star=False`  
# Filling gaps in 30-minute fluxes  
# `is_to_apply_gap_filling=True`  
#
# **Additional options (consistent with previous sections):**  
#
# The name of the station, added to the names of the output files:  
# `site_id=ias_output_prefix`  
# The file from which the time series are loaded:  
# `input_file="REddyProc.txt"`  
# The directory to which the tool writes test graphs, basic statistics on gaps, filled series:  
# `output_dir="output/reddyproc"`

# %% colab={"background_save": true} id="278caec5"
from src.ipynb_globals import *
from types import SimpleNamespace
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
import src.ipynb_globals as ig
from src.helpers.io_helpers import ensure_empty_dir

ig.eddyproc = SimpleNamespace()
ig.eddyproc.options = SimpleNamespace(
    site_id=ias_output_prefix,

    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # default REP detects nights by Rg; when Rg is missing, this is experimental fallback to apply uStar over all data
    ustar_allowed_on_days=True,

    # u_star_seasoning: one of "WithinYear", "Continuous", "User"
    u_star_seasoning="Continuous",

    is_to_apply_partitioning=True,

    # partitioning_methods: one or both of "Reichstein05", "Lasslop10"
    partitioning_methods=["Reichstein05", "Lasslop10"],
    latitude=56.5,
    longitude=32.6,
    timezone=+3.0,

    # "Tsoil"
    temperature_data_variable="Tair",

    # do not change
    u_star_method="RTw",
    is_bootstrap_u_star=False,
    is_to_apply_gap_filling=True,
    input_file=f"output/{reddyproc_filename}",
    output_dir="output/reddyproc",
    log_fname_end='_log.txt'
)

ensure_empty_dir(ig.eddyproc.options.output_dir)
ig.eddyproc.out_info, ig.eddyproc.options = reddyproc_and_postprocess(ig.eddyproc.options)

# %% [markdown] id="0bed439c"
# ## Test graphs
# Displays individual graphs from the online tool in a convenient form for checking.
# The filled data, graphs and statistics can be downloaded in one archive by clicking the **Download eddyproc outputs** button.
#
# **Additional options:**  
# The order and set of graphs are formed automatically in the variable `output_sequence`, which can be changed or re-declared using tags.
# Tags for this particular version of the notebook will be visible after the cell is run by calling `display_tag_info`.

# %% colab={"background_save": true} id="e66a94ab"
from pathlib import Path
from typing import List, Tuple, Union

import src.ipynb_globals as ig
from src.helpers.io_helpers import create_archive
from src.reddyproc.postprocess_graphs import EProcOutputHandler, EProcImgTagHandler, EProcOutputGen
from src.colab_routines import colab_add_download_button, colab_no_scroll

tag_handler = EProcImgTagHandler(main_path='output/reddyproc', eproc_options=ig.eddyproc, img_ext='.png')
eog = EProcOutputGen(tag_handler)

output_sequence: Tuple[Union[List[str], str], ...] = (
    "## Heat maps",
    eog.hmap_compare_row('NEE_*'),
    eog.hmap_compare_row('LE_f'),
    eog.hmap_compare_row('H_f'),
    "## Diurnal course",
    eog.diurnal_cycle_row('NEE_*'),
    eog.diurnal_cycle_row('LE_f'),
    eog.diurnal_cycle_row('H_f'),
    "## 30-minute fluxes and daily averages",
    eog.flux_compare_row('NEE_*'),
    eog.flux_compare_row('LE_f'),
    eog.flux_compare_row('H_f')
)

eio = EProcOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=ig.eddyproc.out_info)
eio.prepare_images_safe()
ig.arc_exclude_files = eio.img_proc.raw_img_duplicates

eproc_arc_path = Path('output/reddyproc') / Path(ig.eddyproc.out_info.fnames_prefix + '.zip')
create_archive(arc_path=eproc_arc_path, folders='output/reddyproc', top_folder='output/reddyproc',
               include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eio.img_proc.raw_img_duplicates)

colab_add_download_button(eproc_arc_path, 'Download eddyproc outputs')

colab_no_scroll()
eio.display_images_safe()

tag_handler.display_tag_info(eio.extended_tags())

# %% [markdown] id="HEead6faY22W"
# # Downloading results
#
# The results of all the segments of the notebook can be downloaded in one archive using the **Download outputs** button.  
#
# If the button below does not appear, you need to run the cell again or download the output files in the Files section, output directory. In the summary files with indexes in the name _hourly (daily variations of filtered and filled variables), _daily (average daily values), _monthly (average monthly values) and _yearly (values for the year, if there is less data - for the entire processing period) the index _sqc means the percentage of values remaining after filtering (but without taking into account the REddyProc filter on u*), and the columns with indexes _f mean the final filled data after all the cells of the notebook.

# %% colab={"background_save": true} id="E4rv4ucOX8Yz"
from src.helpers.io_helpers import create_archive
from pathlib import Path
import src.ipynb_globals as ig

arc_path=Path('output') / 'FluxFilter_output.zip'
create_archive(arc_path=arc_path, folders=['output', 'output/reddyproc'], top_folder='output',
               include_fmasks=['*.png', '*.csv', '*.txt', '*.log'], exclude_files=ig.arc_exclude_files)
colab_add_download_button(arc_path, 'Download outputs')
