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
# * Level 1 means fluxes calculated using the special software with the widely used filtering and correction procedures (example is Full Output file of EddyPro software, LI-COR Inc., USA) and meteorological data averaged for each 30 minutes.
# * Level 2 means unfilled 30-minute data, the PI of the station excludes periods of the obvious malfunction of the instruments (i.e. data for these periods are filled with the missing values code -9999). Such data are equivalent of the Level 2 data of the European fluxes database cluster.
# * Level 3 refers to level 2 data, also unfilled, but carefully filtered based on physical and statistical criteria.
# * Level 4 refers to the gapfilled data.
#
# *To run the demo-version of the script, just click in the Google Colab "Runtime - Run All"*  
# *The newest version of the script is in the repository https://github.com/PlaZMaD/climate/releases*  
#
# ## **Input files**
# Script imports and processes time series of turbulent fluxes and also requires meteorological variables to filter and gap-fill turbulent fluxes. The time series can be imported from one file or combined from multiple files.
# This script supports the following input file formats:
# 1) EddyPro **full output** file (see [EddyPro manual](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) - for fluxes.
# 2) **CSF** output file from EasyFlux DL, Campbell Scientific Ink. software - for fluxes. EddyPro full output and CSF are mutually interchangeable.
# 3) EddyPro **biomet** file ([again](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) - for meteorology. When using full output or CSF for fluxes, biomet is also recommended for reliable flux filtering and gap-filling. However, if meteorological variables are unavailable, the script still will try to run using only Full Output or CSF files.
# 4) Or only file for Information and Analytical System used in the RuFlux network (**IAS**) - contains both fluxes and meteorology.
# 5) Optionally, a **configuration** file which allows to reapply this script parameters from the previous runs without editing cells.  
# 
# When using full output+biomet or CSF+biomet input modes, full output/CSF is the source of turbulent fluxes and u*, while all meteorological variables (air temperature and relative humidity, etc.) are sourced from the Biomet file. The main requirements for the input files are:
# * Files must be in .csv (comma separated value) format.
# * Column headers in full output and biomet must strictly follow the EddyPro manual and this script identifies variables by their column names (co2_flux for CO2 flux in Full Output, Ta_1_1_1 for air temperature in Biomet, etc.).
# * The missing value indicator in the input files must be -9999
# * Units for biomet file variables should be the same as the base units for biomet file as per EddyPro manual. Exception: Air/Soil Temperature should be in degrees Celsius.
# * Full Output file example can be downloaded [here](https://drive.google.com/file/d/1TyuHYZ0uh5teRiRFAga0XIqfU4vYW4-N/view?usp=sharing)
# * Biomet example can be downloaded [here](https://drive.google.com/file/d/1FjiBcSspDBlYlcg9Vzy71Sm49gOFZGBF/view?usp=sharing)
# * CSF can be downloaded *[here]*
# * Configuration (En) [here](https://raw.githubusercontent.com/PlaZMaD/climate/refs/tags/v1.0.8/misc/config_v1.0.8_default.yaml) (open link, right click - Save As), or check the `misc` repository folder
# * The full output file should contain 3 header rows with the variable names in the second row.
# * The biomet file must have 2 header rows with the variable names in the 1st row. Default and supported approach is to place date and time in the TIMESTAMP_1 column in the yyyy-mm-dd HHMM format, but also other import modes are avaliable (check the import cell).
#
# ## **Output files**
# Output file formats (packed to the FluxFilter_output.zip archive and avaliable in the output directory in the Files section):
# 1. One or multiple files formatted for European fluxes database cluster, level 2 (ias-file);
# 2. Input file for the u* filtering, gap filling and partitioning tool REddyProcWeb (Max Planck Institute, Germany). This file is used as input for the "Processing with the REddyProc tool" section of this script. These are the data of level 3.
# 3. Input file for the Flux Analysis Tool (M. Ueyama, Japan) for the gap filling, level 3.
# 4. The output_all file contains all the raw variables (level 1) and all flags implemented for the data.
# 5. The output_summary file contains the time series for the main variables of the raw data, filtered data, the flag for each filter applyed, average diurnal courses in a 30- and 10-day window.
# 6. config*.yaml file - options of the last script run, which can be re-applied on the next run as input file.
# 7. The log file records during the script's run, includes parameters that were accepted for the filtering at this run.
# 8. The reddyproc directory contains the results of gapfilling (level 4) in the same format as the original [REddyProcWeb tool](https://www.bgc-jena.mpg.de/5624929/Output-Format). Additionally, the output/reddyproc directory contains summary files (level 4) with the indexes _hourly (diurnal courses of the original and filled variables), _daily (daily averages), _monthly (monthly averages), and _yearly (yearly values, or for the entire processing period if there is less data).
#
# ## **Loading the input files**
# Two main file upload options are avaliable:  
#
# Via web browser:  
# *   click the directory button (button in bottom of the left panel, below the "key" button)
# *   drag and drop one or more files (for example, from Windows Explorer) into the empty space under the `sample_data` directory
# *   it is useful here to comment out (put a # at the start of the line) the two `!gdown` commands in the **Loading data** section  
#
# Via Google Drive:  
# * upload full output, biomet, configuration and/or other files to the Google drive
# * open access to them (sharing to everyone with the link)
# * copy part of the public link into !gdown commands in the **Loading data** section
#
# The Google Drive option is better if the goal is to share script preset (configuration and linked input files) with other users (it is possible to restrict linked data access to specific Google accounts).  
# Alternative sharing option is to send just input data and configuration files (for example, biomet_2025.csv + full_output_2025.xls + my_config.yaml).
#
# The script will try to detect and import input files automatically, but in case of errors or unexpected cell logs you can try to switch to manual Data loading config section:
# * specify the input file names to exactly match file names you upload
# * check the date and time format for each file type you upload (script recognises some common formats automatically)
#
# ## **Before the filtering**
# * You can upload multiple full output and biomet files, they will be automatically arranged in ascending date-time order and merged into the one table
# * A biomet file with a time step less than 30 minutes is supported - for example, 1 or 5 minutes - but the file must start at a minute value of :00 or :30. The meteorological variables will be averaged to 30 minutes
# * An error is displayed if there is text in the input files in rows below the header
# * The timestamps of each input file are checked (regularization)
# * VPD <-> RH, SWIN <-> RG <-> PAR are calculated in case of absence of any of them
# * You can process CO2 flux or check the storage data, add it to the CO2 flux and work with NEE
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

# %% [markdown] id="sj6Z0gnhVM-R"
# # Technical block
# Importing libraries, downlaoding cell scripts from the repository, defining functions

# %% id="lZliIHxRJiqk"
# from google.colab import userdata
# key = userdata.get('registry_key')

# %pip install -q ruamel.yaml pysolar plotly-resampler dateparser
# # %pip install --index-url https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null
# %pip install --index-url https://gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null

# !rm -rf sample_data
# !rm -rf scripts

# %env clone_br=main
# %env clone_repo=https://github.com/PlaZMaD/climate.git
# !git clone -b $clone_br -n --depth=1 --filter=tree:0 $clone_repo scripts
# !git -C scripts sparse-checkout set --no-cone src locale misc
# !git -C scripts checkout &> /dev/null

# %% id="Ywv5kp0rzanK"
import logging
import re
import sys

from pathlib import Path

import matplotlib.pylab as plt
import numpy as np
import pandas as pd

# #!pip install ipython==8.1.0
# #%load_ext autoreload
# #%autoreload 2

if Path('scripts').exists():
    from scripts import src
    
    sys.modules['src'] = src
    repo_dir = Path('scripts')
else:
    repo_dir = Path('.')

import bglabutils.basic as bg
# import bglabutils.boosting as bb
# import textwrap

from src.colab_routines import colab_no_scroll, colab_enable_custom_widget_manager, colab_add_download_button, \
    colab_xor_demo_data
from src.config.ff_config import FFConfig, RepConfig, FFGlobals, QuantileIQRFilterConfig, QuantileFilterConfig
from src.config.config_types import IasExportIntervals, InputFileType, ColabDemoMixPolicy  # noqa: F401
from src.data_quality import try_compare_stats
from src.ff_logger import init_logging, ff_logger
from src.helpers.io_helpers import ensure_empty_dir, create_archive
from src.data_io.fat_export import export_fat
from src.data_io.rep_level3_export import export_rep_level3
from src.data_io.data_import import import_data
from src.data_io.detect_import import try_auto_detect_input_files
from src.data_io.ias_io import export_ias
from src.ipynb_routines import setup_plotly, ipython_enable_word_wrap, ipython_edit_function  # noqa: F401
from src.filters import min_max_filter, qc_filter, std_window_filter, meteorological_rh_filter, \
    meteorological_night_filter, meteorological_day_filter, meteorological_co2ss_filter, meteorological_ch4ss_filter, \
    meteorological_rain_filter, quantile_filter, quantile_iqr_filter, mad_hampel_filter, manual_filter, winter_filter, \
    basic_filter
from src.plots import get_column_filter, basic_plot, plot_nice_year_hist_plotly, make_filtered_plot, plot_albedo, \
    debug_plot_changes
from src.plots import plot_cols  # noqa: F401

# rpy2 hotfix: path must be set properly before the first rpy2 import
from src.helpers.env_helpers import setup_r_env
setup_r_env(repo_dir)
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
from src.reddyproc.postprocess_graphs import RepOutputHandler, RepImgTagHandler, RepOutputGen
from src.reddyproc.preprocess_rg import prepare_rg

# cur_dir = %pwd
# assert cur_dir == '/content'
gl = FFGlobals(out_dir=Path('output'), input_dir=Path('.'), repo_dir=repo_dir)
ensure_empty_dir(gl.out_dir)

colab_no_scroll()
colab_enable_custom_widget_manager()
setup_plotly(gl.out_dir)
init_logging(level=logging.INFO, fpath=gl.out_dir / 'log.log', to_stdout=True)

# Cells can be executed separately via import * and mocking global vars import global as gl
# To tweak filters directly in Colab: 1) run all the cells above 2) run in a new cell the line below 3) #comment the line
# ipython_edit_function(meteorological_night_filter)

# Cleanup on each run: ensure no leftovers from the previous runs (make sure not to use with mounted folders)
# # !rm *.*

# %% [markdown] id="wVF1vDm4EauW"
# # Loading data

# %% [markdown] id="LV9FvvtnVqdN"
# **It is necessary to change:**
#
# There are two main file upload options:  (check Introduction: Loading the input files):  
# 1) drag and drop files into the web browser or use Upload menu (right-click under `sample_data`)  
# 2) script will download them from Google Drive link if `!gdown ...` command is correctly edited in this cell  
# 
# For the option 1, it is convenient to diable demo data downloads: change  
# `!gdown ...` to `# !gdown ...`.  
# 
# For the option 2, if public file link to the Google Drive file is 
# https://drive.google.com/file/d/1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB/view?usp=sharing, 
# then copy only the characters between `d/` and the next `/` and edit `!gdown` commands as  
# `!gdown 1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB`
#
# `# Load into Colab Full Output, CSF, or IAS file` 
# Here, demo FO file is loaded by default. Edit the symbols after gdown to match link to your file containing the flux data (full output, CSF, or IAS).
#
# `# Load into Colab biomet file`
# Here, demo Biomet files is loaded by default. Edit the symbols to match link to your biomet file (or any other file, or disable gdown command if unused)
#
# A configuration text file (in `.yaml` format) is packed into output files after the script finishes. It can also be uploaded to Google Drive and specified in the third `!gdown` command.

# %% id="KMu4IqY45HG6"
# Load into Colab full output, CSF, or IAS file
# https://drive.google.com/file/d/1AD4U06Qre-PgKnsyRHX11RuruCNQzMvB/view?usp=sharing
# !gdown 1AD4U06Qre-PgKnsyRHX11RuruCNQzMvB

# Load into Colab biomet file
# https://drive.google.com/file/d/1_ZoFgNyOZEYNdjf6rFq66HR4UXDSQ5z3/view?usp=sharing
# !gdown 1_ZoFgNyOZEYNdjf6rFq66HR4UXDSQ5z3

# Uploading any other files (configuration, data, etc.)
# https://drive.google.com/file/d/*/view?usp=sharing
# # !gdown *
# %% [markdown] id="WfWRVITABzrz"
# # Setting the parameters for loading and processing of the data

# %% [markdown] id="ox0UplWMe7wn"
# ## Data loading config
# The parameters of the input files are specified here: names, date-time format, etc.  
#
# Next data import modes are supported which expect different types of uploaded files:  
# - one or more EddyPro - full output files
# - one or more EddyPro - full output files and one or more biomet files described in the EddyPro manual
# - one or more IAS files
# - one or more CSF files and one or more biomet files described in the EddyPro manual
#
# By default there will be attempt to detect import mode and file settings automatically. When extra files are found or in complex imports you can try manually specify all settings in this cell.  
#
# **Configuration file**  
# The script supports two configuration options sources:  
# - when no configuration file is provided, the notebook cells themselves contain active options  
# - uploaded configuration file have higher priority and settings from the notebook cells will be ignored  
#
# After the each run, configuration file `config*.yaml` is packed to the output archive.
# Some examples of configuration files will also be available in the Colab directory `scripts/misc` after the notebook finishes.
# You can manually edit these yaml configurations and upload them on the next runs together with the data. In this cell there will be automatic attempt to read a file matching `config*.yaml` pattern. Loading can be disabled or a fixed filename can be specified using the `load_path='auto'` argument.  
#
# **It is necessary to check:**
#
# In the default automatic mode (`config.data_import.input_files = auto`), the log of the **Data import and validation** cell will contain diagnostic information about the validation and import mode (one of `EDDYPRO_FO`, `EDDYPRO_FO_AND_BIOMET`, `IAS`, `CSF`, `CSF_AND_BIOMET`). It is recommended to check the log to ensure that the date-time formats and other settings were detected correctly. If any settings are detected incorrectly, they can be specified manually:  
#
# In the manual mode `config.data_import.input_files` should be a dictionary mapping file paths to file types: `= {'1.csv': InputFileType.EDDYPRO_FO}`. Do not forget the single quotes and the `.csv` extension!  
# The way files were uploaded (`!gdown` Google Drive link or manual) is alrady irrelevant at this step, only the file name is used.  
#
# Check the date order (year, month, day) and date-time separators in the input files by opening them in a text editor (Notepad). Possible options:
# 1.  The date is written as 05/29/2024 and the time as 12:00. Then they are encoded as "%d.%m.%Y %H:%M" - this format is written below by default, nothing needs to be changed;
# 2.  The date is written as 05/29/2024 and the time as 12:00. Change the format in the line below to "%d/%m/%Y %H:%M"
# 3.  The date is written as 2024-05-29 and the time as 1200. Change the format in the line below to "%Y-%m-%d %H%M"
# 4.  In other cases, behave similarly. If there are seconds in the time column, the format is encoded as "%Y-%m-%d %H:%M:%S".  
# For example, default biomet date is 2011-11-12 and time is 1200, which is encoded as "%Y-%m-%d %H%M".  
#
# **Additional options (better not to change without PRO level):**  
# `config.*.missing_data_codes = ['-9999']` a list of missing data indication values to replace with np.nan for the proper work of the algorithm;  
# `config.*.repair_time` when `True` will check the date-time column for gaps and monotony, and will perform regeneration by the first-last point taking into account the expected step length (calculated by the first values in the series).
# `config.data_import.ias.skip_validation` when `True`, allows to skip IAS standard pre-validations  
# `config.data_import.csf.empty_co2_strg` when `True` and co2_strg is missing in the csf, generates empty co2_strg as a workaround  


# %% id="tVJ_DRBrlpYd"

# init_debug=True: enables debug options and processes a small part of a data instead of a full length
# load_path=None disables lookup, load_path='myconfig.yaml' sets fixed expected name without pattern lookup
config = FFConfig.load_or_init(load_path='auto', default_fpath=gl.repo_dir / 'misc/config_v1.0.8_default_ru.yaml',
                               init_debug=False, init_version='v1.0.8')

if not config.from_file:
    config.data_import.input_files = 'auto'
    # alternative ways if 'auto' mode works not as expected:
    # config.data_import.input_files = {'tv_fy4_2019_v01.xlsx': InputFileType.IAS}
    # config.data_import.input_files = {'eddy_pro tv_fy4 2023.csv': InputFileType.EDDYPRO_FO, 'BiometFy4_2023.csv': InputFileType.EDDYPRO_BIOMET}
    
    config.data_import.time_col = 'datetime'
    
    config.data_import.eddypro_fo.missing_data_codes = [-9999]
    config.data_import.eddypro_fo.date_col = 'date'
    config.data_import.eddypro_fo.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.data_import.eddypro_fo.time_col = 'time'
    config.data_import.eddypro_fo.try_time_formats = ['%H:%M', '%H:%M:%S']
    config.data_import.eddypro_fo.repair_time = True
    
    config.data_import.eddypro_biomet.missing_data_codes = [-9999]
    config.data_import.eddypro_biomet.datetime_col = 'TIMESTAMP_1'
    config.data_import.eddypro_biomet.try_datetime_formats = ['%Y-%m-%d %H%M', '%d.%m.%Y %H:%M']  # yyyy-mm-dd HHMM
    config.data_import.eddypro_biomet.repair_time = True
    
    config.data_import.eddypro_biomet_2.missing_data_codes = [-9999]
    config.data_import.eddypro_biomet_2.date_col = 'date'
    config.data_import.eddypro_biomet_2.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.data_import.eddypro_biomet_2.time_col = 'time'
    config.data_import.eddypro_biomet_2.try_time_formats = ['%H:%M', '%H:%M:%S']
    config.data_import.eddypro_biomet_2.repair_time = True
    
    config.data_import.csf.missing_data_codes = [-9999, 'NAN']
    config.data_import.csf.datetime_col = 'TIMESTAMP'
    config.data_import.csf.try_datetime_formats = ['%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']  # yyyy-mm-dd HHMM
    config.data_import.csf.repair_time = True
    config.data_import.csf.empty_co2_strg = True
    
    config.data_import.ias.skip_validation = False
    config.data_import.ias.missing_data_codes = [-9999]
    config.data_import.ias.datetime_col = 'TIMESTAMP_START'
    config.data_import.ias.try_datetime_formats = '%Y%m%d%H%M'
    config.data_import.ias.repair_time = True
    
    config.data_import.mixed_demo_policy = ColabDemoMixPolicy.AUTO_DELETE_DEMO

colab_xor_demo_data(gl.input_dir, config.data_import.mixed_demo_policy)

# %% [markdown] id="DtxFTNnEfENz"
# ## Selecting columns for graphs and filters

# %% id="nLnivFTtg9cu"
# Gather the summary information about the parameters of interest:
cols_to_investigate = [
    'co2_flux',
    'ch4_flux',
    'LE',
    'H',
    'co2_strg',
    'Ta_1_1_1',
    'RH_1_1_1',
    'VPD_1_1_1',
    'P_1_1_1',
    'SWIN_1_1_1',
    'PPFD_1_1_1',
    # 'co2_signal_strength',
    # 'ch4_signal_strength',
]

cols_to_investigate = [k.lower() for k in cols_to_investigate]

# %% [markdown] id="wVpYvr9_fKBU"
# ## Setting up parameters for the data analysis
#
# All settings for co2_flux will be applied to nee if it is chosen to calculate

# %% [markdown] id="FH2uRGi4p5Zj"
# ### Physical filtering

# %% id="pPemVdWVbq2E"
if not config.from_file:
    config.calc.calc_nee = True
    
    # Location ID which will be added to the names of all output files and graphs
    config.metadata.site_name = 'auto'
    config.data_export.ias.out_fname_ver_suffix = 'auto'

# %% [markdown] id="5MK90gyzQryZ"
# Filtering by quality flags. Data with flags in the range (-inf, val] will be marked as valid, and data with a flag value greater than the threshold will be excluded.

# %% id="ukl734CBblay"
qc = {}
qc['h'] = 1  # Change when using 1-9 flag system
qc['le'] = 1  # Change when using 1-9 flag system
qc['co2_flux'] = 1  # Change when using 1-9 flag system
qc['ch4_flux'] = 1  # Change when using 1-9 flag system
if not config.from_file:
    config.filters.qc = qc

# %% [markdown] id="QPIFpLN_-8Uf"
# Filtering fluxes in certain meteorological conditions (by values of meteorological variables), possible options:
#
# * `CO2SS_min` - will remove CO2_FLUX when co2_signal_strength is below the set threshold
# * `p_rain_limit` - will remove H, LE and CO2_FLUX, for P_rain_1_1_1 above the set threshold
# * `rain_forward_flag` - will remove values for the set number of records forward from each value filtered in the previous step
# * `RH_max` - will remove LE and CO2_FLUX values for which RH_1_1_1 is greater than the specified threshold
# * `use_day_filter` - if True, daily (Swin>`day_swin_limit`) NEEs greater than the set threshold (NEE>`day_nee_max`) will be excluded
# * `use_night_filter` - if True, night (Swin<`day_swin_limit`) NEEs less than the set threshold (NEE<`night_nee_min`) will be excluded
# * `day_nee_max` - threshold for NEE during daytime (excluding intense emission during daytime)
# * `night_nee_min` - threshold for NEE at night (excluding intense net absorption at night)
# * `day_swin_limit` - threshold of incoming shortwave radiation, defining daytime data (can be changed for stations beyond the Arctic Circle)
# * `night_h_limits`, `night_le_limits` - plausible night ranges for H and LE
# * `winter_nee_limits` - plausible range of NEE in winter (winter period is set separately in the section "winter period filtering, determine the dates!")
# * `winter_ch4_flux_limits` - plausible range of methane flux in winter
# * `CH4SS_min` - will remove CH4_FLUX when ch4_signal_strength is below the specified value
#
# If any of the parameters are missing or commented in this cell, filtering is not applied.

# %% id="vxpiAbWk2yYr"
filters_meteo = {}
filters_meteo['CO2SS_min'] = 80.

# These filters may not be needed for the closed-path eddy covariance systems
filters_meteo['p_rain_limit'] = .1
filters_meteo['rain_forward_flag'] = 2
# Relative humidity filter (intended to find the cases of formation of condensation): apply only if CO2SS and anemometer
# diagnostics are absent and the data were not filtered by these indicators during the calculation of 30-min data
# meteo_filter_config['RH_max'] = 98

# Plausible values at day/night-time
filters_meteo['use_day_filter'] = True
filters_meteo['use_night_filter'] = True
filters_meteo['day_nee_max'] = 5
filters_meteo['night_nee_min'] = -5
filters_meteo['day_swin_limit'] = 10
filters_meteo['night_h_limits'] = [-50, 20]
filters_meteo['night_le_limits'] = [-50, 20]

# Plausible values at winter. For the grass ecosystems the upper limit is usually lower
filters_meteo['winter_nee_limits'] = [-1, 5]
filters_meteo['winter_ch4_flux_limits'] = [-1, 1]
filters_meteo['CH4SS_min'] = 20.

if not config.from_file:
    config.filters.meteo = filters_meteo

# %% [markdown] id="utUX7SA4qA_I"
# ### Statistical filtering

# %% [markdown] id="wWISuF-xQCwq"
# Filtering parameters by absolute values. 
# For `rh_1_1_1` values above the boundary are replaced with the boundary values instead of discarding. For `ppfd_1_1_1`, `swin_1_1_1` the minimum values are processed similarly.

# %% id="HQfIYFOd9uzi"
filters_min_max = {}
filters_min_max['co2_flux'] = [-40, 40]
filters_min_max['co2_strg'] = [-20, 20]
filters_min_max['h'] = [-100, 800]
filters_min_max['le'] = [-100, 1000]
filters_min_max['u_star'] = [0, 10]
filters_min_max['ta_1_1_1'] = [-50, 50]
filters_min_max['p_1_1_1'] = [0, 100]
filters_min_max['vpd_1_1_1'] = [0, 50]
filters_min_max['rh_1_1_1'] = [0, 100]  # max
filters_min_max['swin_1_1_1'] = [0, 1200]  # min
filters_min_max['ppfd_1_1_1'] = [0, 2400]  # min
filters_min_max['rg_1_1_1'] = [0, 2400]  # min
filters_min_max['ch4_flux'] = [-10, 10]

if not config.from_file:
    config.filters.min_max = filters_min_max

# %% [markdown] id="vmyTKbV1RdjD"
# Filtering parameters based on the deviation from the average diurnal course in a moving window.
# * `sigmas` - plausible range of deviation from the average course; values outside the range are eliminated
# * `window` - window size in days for calculating the diurnal course
# * `min_periods` - minimum number of points for each 30-min interval in the window. If the window has less points then the course is not calculated, the filter is not applied.

# %% id="xfRVNYbFYzG3"
filters_window = {}
# Closed-path eddy covariance systems and less noisy data may need milder criteria (for example, 3 sigma)
filters_window['co2_flux'] = {'sigmas': 2, 'window': 10, 'min_periods': 4}
filters_window['ch4_flux'] = {'sigmas': 2, 'window': 10, 'min_periods': 4}

# If reliable data are deleted, it is recommended to increase the value of 'sigmas'
filters_window['ta_1_1_1'] = {'sigmas': 4, 'window': 10, 'min_periods': 4}
filters_window['u_star'] = {'sigmas': 4, 'window': 10, 'min_periods': 4}
for col in ['h', 'le', 'rh_1_1_1', 'vpd_1_1_1']:
    filters_window[col] = {'sigmas': 7, 'window': 10, 'min_periods': 4}
for col in ['swin_1_1_1', 'ppfd_1_1_1']:
    filters_window[col] = {'sigmas': 8, 'window': 10, 'min_periods': 4}

if not config.from_file:
    config.filters.window = filters_window

# %% [markdown] id="KF_MGD7pSGre"
# Filtering parameters above and below threshold by quantiles (values not in range are removed):
# * `filters_quantile` - quantiles are calculated from the distribution across the entire data column; the values in square brackets specify the quantiles
# * `filters_quantile_iqr` - IQR filter in a sliding window (only the local data distribution is taken into account); the parameter specifies the IQR multiplier (1.5 by default; increasing it will filter out less data)  
# * 'window_size_days' time span of the sliding IQR window in days  

# %% id="asO_t2tZmiD0"
filters_quantile = QuantileFilterConfig()
filters_quantile_iqr = QuantileIQRFilterConfig()

filters_quantile.enabled = True
filters_quantile.tgt_cols['co2_flux'] = [0.01, 0.99]
filters_quantile.tgt_cols['ch4_flux'] = [0.01, 0.99]
filters_quantile.tgt_cols['co2_strg'] = [0.01, 0.99]

filters_quantile_iqr.enabled = False
filters_quantile_iqr.window_size_days = 7
filters_quantile_iqr.tgt_cols['co2_flux'] = 1.5
filters_quantile_iqr.tgt_cols['ch4_flux'] = 1.5

if not config.from_file:
    # indirect default validation on assigment is not triggered above due to nested dictionary, 
    # and nested is used for one-line syntax; so config validation better be triggered manually:
    QuantileFilterConfig.model_validate(filters_quantile)
    QuantileIQRFilterConfig.model_validate(filters_quantile_iqr)
    config.filters.quantile = filters_quantile
    config.filters.quantile_iqr = filters_quantile_iqr

# %% [markdown] id="cPiTN288UaP3"
# Parameters for filtering by deviation from the neighboring points: MAD and Hampel filters.

# %% id="2b3eBVFUq3AU"
filters_madhampel = {}
# filters_madhampel = {i:{'z': 5.5, 'hampel_window': 10} for i in cols_to_investigate if 'p_1_1_1' not in i}
# Hard filtering: 'z'=4. Mild filtering: 'z'=7
filters_madhampel['co2_flux'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['ch4_flux'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['le'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['h'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['co2_strg'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['ta_1_1_1'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['rh_1_1_1'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['vpd_1_1_1'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['swin_1_1_1'] = {'z': 8.0, 'hampel_window': 10}
filters_madhampel['ppfd_1_1_1'] = {'z': 8.0, 'hampel_window': 10}

if not config.from_file:
    config.filters.madhampel = filters_madhampel

# %% [markdown] id="wVF1vDm4EauW"
# # Data import and validation

# %% id="Xw5TapK10EhR"
res = try_auto_detect_input_files(config, gl)
(config.data_import.input_files, config.data_import.import_mode,
 config.metadata.site_name, config.data_export.ias.out_fname_ver_suffix, config.calc.has_meteo) = res
data, meteo_cols, config.calc.has_meteo = import_data(config)
time_col, data_freq = config.data_import.time_col, config.data_import.time_freq

gl.points_per_day = int(pd.Timedelta('24h') / data_freq)

# %% id="C8lLDYOWzH2d"
data.columns = data.columns.str.lower()
if not config.calc.has_meteo:
    data["rh_1_1_1"] = data['rh']
    # TODO QOA 1 different units? Elg biomet kPa, but mean 8.6 ?
    data["vpd_1_1_1"] = data['vpd']

# %% [markdown] id="ipknrLaeByCT"
# Checking for correct data type (example: presence of text instead of numbers):

# %% id="8LawdKUbB1_m"
cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength',
                'rh_1_1_1', 'vpd_1_1_1', 'rg_1_1_1', 'p_rain_1_1_1',
                'co2_signal_strength_7500_mean', 'CO2SS'.lower(), 'co2_signal_strength',
                'ch4_signal_strength_7500_mean', 'ch4SS'.lower(), 'ch4_signal_strength',
                'p_1_1_1', 'ta_1_1_1', 'co2_strg', 'le', 'h']

data_type_error_flag = False
for col in cols_2_check:
    if col not in data.columns:
        continue
    error_positions = data[col].fillna(0).apply(pd.to_numeric, errors='coerce').isna()
    if error_positions.any():
        ff_logger.error(
            f"""Check input files for {col} column near:\n {error_positions[error_positions == True].index.strftime('%d-%m-%Y %H:%M').values} in {'biomet' if len(meteo_cols) > 0 and col in meteo_cols else 'data'} file"""
        )
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

for col in data.columns:
    # Eddypro renames
    if col == 'u*':
        print(f"renaming {col} to u_star")
        data = data.rename(columns={col: 'u_star'})
    if 'co2_signal_strength' in col:
        print(f"renaming {col} to co2_signal_strength")
        data = data.rename(columns={col: 'co2_signal_strength'})
    if col in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()] or 'co2_signal_strength' in col:
        print(f"renaming {col} to co2_signal_strength")
        data = data.rename(columns={col: 'co2_signal_strength'})
    if col in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()] or 'ch4_signal_strength' in col:
        print(f"renaming {col} to ch4_signal_strength")
        data = data.rename(columns={col: 'ch4_signal_strength'})
    
    # Biomet renames
    if col == 'ppfd_in_1_1_1':
        print(f"renaming {col} to ppfd_1_1_1")
        data = data.rename(columns={col: 'ppfd_1_1_1'})
    if col == 'sw_in_1_1_1':
        print(f"renaming {col} to swin_1_1_1")
        data = data.rename(columns={col: 'swin_1_1_1'})
    
    if col == "rh_1_1_1":
        have_rh_flag = True
    if col == "vpd_1_1_1":
        have_vpd_flag = True
    if col in ['swin_1_1_1', 'sw_in_1_1_1']:
        have_swin_flag = True
    if col == 'par':
        have_par_flag = True
    if col == 'rg_1_1_1':
        have_rg_flag = True
    if col == 'p_1_1_1':
        have_p_flag = True
    if col == 'p_rain_1_1_1':
        have_pr_flag = True
    if col == 'ppfd_1_1_1':
        have_ppfd_flag = True

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
    logE = 23.5518 - (2937.4 / temp_k) - 4.9283 * np.log10(temp_k)
    ehpa = np.power(10, logE)
    if not have_vpd_flag:
        print("calculating vpd_1_1_1 from rh_1_1_1 and air temperature")
        data['vpd_1_1_1'] = ehpa - (ehpa * data['rh_1_1_1'] / 100)
    if not have_rh_flag:
        # TODO QOA 1 possibly an error
        # OA: check tg for the formula
        print("estimating rh_1_1_1 from air temperature")
        data['rh_1_1_1'] = ehpa

if not (have_par_flag or have_swin_flag):
    print("NO PAR and SWin")
else:
    if not have_par_flag:
        data['par'] = data['swin_1_1_1'] / 0.47  # SWin=PAR*0.47
    if not have_swin_flag:
        data['swin_1_1_1'] = 0.47 * data['par']

for col in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()]:
    # print(data.columns.to_list())
    if col in data.columns.to_list():
        print(f"renaming {col} to co2_signal_strength")
        data = data.rename(columns={col: 'co2_signal_strength'})

for col in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()]:
    # print(data.columns.to_list())
    if col in data.columns.to_list():
        print(f"renaming {col} to ch4_signal_strength")
        data = data.rename(columns={col: 'ch4_signal_strength'})

if not config.calc.has_meteo or 'ta_1_1_1' not in data.columns:
    data['ta_1_1_1'] = data['air_temperature'] - 273.15
    ff_logger.info("No Ta_1_1_1 column found, replaced by 'air_temperature'")

df_ias_export = data.copy()
try_compare_stats(data, repo_dir / 'misc/expected_stats.xlsx')

# %% [markdown] id="soyyX-MCbaXt"
# ## Calculating NEE from CO2_flux and storage

# %% [markdown] id="lqWwGSMObro4"
# Checking the storage. The storage calculated by one vertical level in EddyPro (full output - co2_strg column) is not always reliable. Correctness is checked by the proper diurnal course: there should be an accumulation during the night, and a sharp decrease in the morning.

# %% [markdown] id="2yqwO7Uhcjmz"
# Filtering co2_strg to remove values above and below threshold quantiles. Filling co2_strg gaps of 3 points or less with linear interpolation. The resulting filtered and filled co2_strg values are plotted. You make a decision whether to sum co2_flux and co2_strg to obtain NEE or to continue working with co2_flux.

# %% id="cjt05XXtbr69"
# Gaps shorter than 3 30-mins ranges are linearly interpolated
if config.calc.calc_nee and 'co2_strg' in data.columns:
    tmp_data = data.copy()
    tmp_data['co2_strg_tmp'] = tmp_data['co2_strg'].copy()
    tmp_filter_db = {'co2_strg_tmp': []}
    if config.filters.quantile.enabled and 'co2_strg' in config.filters.quantile.tgt_cols.keys():
        tmp_q_config = QuantileFilterConfig(enabled=True,
                                            tgt_cols={'co2_strg_tmp': config.filters.quantile.tgt_cols['co2_strg']})
    else:
        tmp_q_config = QuantileFilterConfig(enabled=False)
    tmp_filter_db = {'co2_strg_tmp': []}
    tmp_data, tmp_filter_db = quantile_filter(tmp_data, tmp_filter_db, tmp_q_config)
    
    # TODO 1 co2_strg - iqr or same as previous	
    # tgt_cols = config.filters.quantile.tgt_cols
    # if 'co2_strg' in config.filters.quantile.tgt_cols.keys():
    #     tmp_q_config = QuantileFilterConfig(enabled=True, window_size_days=7,
    #                                         tgt_cols={'co2_strg_tmp': tgt_cols['co2_strg']})
    # else:
    #     tmp_q_config = QuantileFilterConfig(enabled=False)
    # tmp_filter_db = {'co2_strg_tmp': []}
    # tmp_data, tmp_filter_db = quantile_filter(tmp_data, tmp_filter_db, config.debug, tmp_q_config)	
    
    tmp_data.loc[~get_column_filter(tmp_data, tmp_filter_db, 'co2_strg_tmp').astype(bool), 'co2_strg_tmp'] = np.nan
    # tmp_data['co2_strg_tmp'] = tmp_data['co2_strg_tmp'].interpolate(limit=3)
    # tmp_data['co2_strg_tmp'].fillna(bg.calc_rolling(tmp_data['co2_strg_tmp'], rolling_window=10 , step=gl.points_per_day, min_periods=4))
    basic_plot(tmp_data, ['co2_strg_tmp'], config.metadata.site_name, tmp_filter_db, steps_per_day=gl.points_per_day)
    if 'co2_strg_tmp_quantilefilter' in tmp_data:
        print(tmp_q_config, tmp_filter_db, tmp_data['co2_strg_tmp_quantilefilter'].value_counts())

# %% id="2IQ7W6pslYF-"
# Decide whether to sum co2_flux and co2_strg_filtered_filled to obtain NEE
if not config.from_file:
    # Keep False to work with co2_flux without co2_strg
    # Change to True to obtain NEE and use to it in the next cells
    config.calc.calc_with_strg = False
ff_logger.info(f"config.calc.calc_with_strg is set to {config.calc.calc_with_strg}")

# %% id="ueuvsNxYdtgs"
if config.calc.calc_nee and 'co2_strg' in data.columns:
    if config.calc.calc_with_strg:
        data['nee'] = (tmp_data['co2_flux'] + tmp_data['co2_strg_tmp']).copy()
    else:
        data['nee'] = data['co2_flux'].copy()
    del tmp_data
    if 'nee' not in cols_to_investigate:
        cols_to_investigate.append('nee')
    
    if not config.from_file:
        for filter_config in [config.filters.qc, config.filters.meteo, config.filters.min_max,
                              config.filters.window,
                              config.filters.quantile.tgt_cols, config.filters.quantile_iqr.tgt_cols,
                              config.filters.madhampel]:
            if 'co2_flux' in filter_config:
                filter_config['nee'] = filter_config['co2_flux']


# %% [markdown] id="mUgwuaFYribB"
# # Overview of statistics for the columns of interest

# %% id="dhcplCMbXtkK"
cols_to_investigate = [p for p in cols_to_investigate if p in data.columns]

# %% id="YfusqiotOi3n"
data.loc[:, cols_to_investigate].describe()

fig, axs = plt.subplots(ncols=min(3, len(cols_to_investigate)), nrows=int(np.ceil(len(cols_to_investigate) / 3)),
                        squeeze=False, figsize=(13, 8))

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

# %% [markdown] id="soyyX-MCbиXt"
# ## by footprint

# %% id="mAdYXJ4dSRbJ"

# renames from IAS: 'x_peak': 'FETCH_MAX_1_1_1', 'x_70%': 'FETCH_70_1_1_1', 'x_90%': 'FETCH_90_1_1_1',
# config_footprint = ['h', 'le', 'sh_1_1_1', 'ch4_flux']
config_footprint = []

if not config.from_file:
    config.filters.footprint = config_footprint
    
# with debug_plot_changes(config.debug, data, cols, None, 'fetch_filter'):
data = basic_filter(data, src_col='FETCH_FILTER', src_bad_value=0, tgt_cols=config.filters.footprint)


# %% [markdown] id="BL_6XxGGsCBK"
# ## using quality flags

# %% id="GGwe7_uU1C8U"
plot_data, filters_db = qc_filter(plot_data, filters_db, config.filters.qc)

# %% [markdown] id="M_gKSTNYyzjS"
# ## accounting for CO2SS and CH4SS

# %% id="viq7BZue9Ett"
plot_data, filters_db = meteorological_co2ss_filter(plot_data, filters_db, config.filters.meteo)

# %% id="5RrPfxfiJGhN"
plot_data, filters_db = meteorological_ch4ss_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="qwqVDeH6y73_"
# ## plausible RH values

# %% id="11isfvNZ9FGu"
plot_data, filters_db = meteorological_rh_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="oSX2h9QzzFkT"
# ## rain events

# %% id="jz696mc09FlB"
if config.calc.has_meteo:
    plot_data, filters_db = meteorological_rain_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="Xy2y00P1zJtZ"
# ## day-time and night-time plausible ranges

# %% id="ED_Qh6TS0Qkc"
if config.calc.has_meteo:
    plot_data, filters_db = meteorological_night_filter(plot_data, filters_db, config.filters.meteo)

# %% id="X3Vguu8MK635"
if config.calc.has_meteo:
    plot_data, filters_db = meteorological_day_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="fzfTJdNe68Eu"
# ## winter period filtering, determine the dates!

# %% id="wJ87D57S7A91"
if ('winter_nee_limits' in config.filters.meteo.keys()) or ('winter_ch4_flux_limits' in config.filters.meteo.keys()):
    plot_albedo(plot_data, filters_db)

# %% id="Z_RAYINf67PO"
if config.calc.has_meteo:
    unroll_filters_db = filters_db.copy()
    if not config.from_file:
        config.filters.winter_date_ranges = [
            ['01.01.2023 00:00', '26.03.2023 23:30'],
            ['13.11.2023 00:00', '31.12.2023 23:30'],
        ]
    # date_ranges = []
    # date_ranges.append(['25.8.2014 00:00', '26.8.2014 00:00'])
    plot_data, filters_db = winter_filter(plot_data, filters_db, config.filters.meteo,
                                          config.filters.winter_date_ranges)

# %% [markdown] id="UAdRtCPGq6_y"
# # Statistical data filtering

# %% [markdown] id="LcwZplknsHJv"
# ## by minimum and maximum acceptable values

# %% id="FyJaM1zC1DDg"
# if config.calc.has_meteo:
plot_data, filters_db = min_max_filter(plot_data, filters_db, config.filters.min_max)

# %% [markdown] id="j62U1dw8sTEm"
# ## by quantiles

# %% id="aNQ4XDK01DME"
# if config.calc.has_meteo:
plot_data, filters_db = quantile_filter(plot_data, filters_db, config.filters.quantile)
plot_data, filters_db = quantile_iqr_filter(plot_data, filters_db, config.debug, config.filters.quantile_iqr)

# %% [markdown] id="7Sg76Bwasnb4"
# ## by deviation from the average diurnal course

# %% id="uoDvHhoQ2MMe"
plot_data, filters_db = std_window_filter(plot_data, filters_db, config.filters.window)

# %% [markdown] id="iXl5RdINss9D"
# ## MAD & Hampel outliers filtering
# %% id="gl9cImVr2MO3"
unroll_filters_db = filters_db.copy()
plot_data, tmp_filter = mad_hampel_filter(plot_data, filters_db, config.filters.madhampel)

# %% [markdown] id="iu8MLKyh1AFk"
# ## Manual filtering
#
# If you need to remove some intervals manually
#

# %% id="ADy534At0_fN"
#  the filter excludes values from the first to the last one inclusively
if not config.from_file:
    config.filters.man_ranges = [
        # ['1.5.2023 00:00', '1.6.2023 00:00'],
        # ['25.8.2023 12:00', '25.8.2023 12:00'],
    ]
for man_range in config.filters.man_ranges:
    plot_data, tmp_filter = manual_filter(plot_data, filters_db, col_name="nee", man_range=man_range, value=0,
                                          manual_config=man_range)

# %% [markdown] id="quGbtDaJ_gID"
# ## Summary table of filter results

# %% id="Pg78qGJ9_miW"
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

ff_logger.info("What percentage of data from all data (in %) was eliminated:")
df_stats = fdf_df.iloc[1] / len(plot_data) * 100
ff_logger.info('\n' + df_stats.to_string())

# %% [markdown] id="gA_IPavss0bq"
# # Drawing graphs

# %% [markdown] id="ijPM6mnJtMv8"
# ## Plotting the results of data filtering

# %% id="50Xhczc-BRc2"
plot_terator = iter(cols_to_investigate)

# %% [markdown] id="uat4oESzU4__"
# To free up memory and ensure the proper work of the Google Colab, the graphs will be displayed one by one when the cell is rerun.

# %% id="NhNoFAd7DqNN"
col2plot = next(plot_terator, False)

# Insert the parameter of interest: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1, co2_signal_strength, ch4_flux
col2plot = 'nee'

# Or comment the previous line and rerun the cell for the switching to the next parameter
if col2plot:
    make_filtered_plot(plot_data, col2plot, col2plot, config.metadata.site_name, filters_db)
else:
    print("No more data, start from the begining!")
    plot_terator = iter(cols_to_investigate)

# %% id="ZG_wF2qW-Qwb"
# #linear gapfilling, limit is the permitted maximal number of the consecutive missed values
# for col in cols_to_investigate:
#   plot_data[col] = plot_data[col].interpolate(limit=5)

# %% id="VtJ8wyx2-XCX"
# #Gapfilling with the diurnal course
# for col in cols_to_investigate:
#   plot_data[col].fillna(bg.calc_rolling(plot_data[col], rolling_window=10, step=gl.points_per_day, min_periods=7))

# %% [markdown] id="MwuXRVTMtBz2"
# ## Plotting the average diurnal course for the filtered data

# %% id="pWDTiucTgRlI"
plot_terator = iter(cols_to_investigate)

# %% id="COKiwe7020D4"
# The example of the calculation of the diurnal course

col2plot = next(plot_terator, False)
# Can be chosen manually
# col2plot = 'h'#"co2_flux"

# Insert the parameter of interest: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
col2plot = ['nee', 'le']
# Or rerun the cell to switch to the next parameter
if col2plot:
    basic_plot(plot_data, col2plot, config.metadata.site_name, filters_db, steps_per_day=gl.points_per_day)
else:
    print("No more data, start from the begining!")
    plot_terator = iter(cols_to_investigate)

# %% [markdown] id="RKEg6YBstXMp"
# ## Heat maps of fluxes for the filtered data

# %% id="mCUJYURKEL-f"
# Insert the parameter of interest: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
for col in ['nee', 'le', 'h']:
    # Or rerun the cell to switch to the next parameter
    plot_nice_year_hist_plotly(plot_data, col, time_col, filters_db)

# %% [markdown] id="EFscf-JZt3_R"
# # Writing the output files

# %% [markdown] id="dokSxicNtdva"
# ## A file for REddyProc

# %% [markdown] id="tDqsi61kSeak"
# Creating a header for the REddyProc file and save the required variables, the filtering is taken into account. The output file has the 3rd level.

# %% id="YVu2UrCzLqb4"
output_template = {
    'Year': ['-'], 'DoY': ['-'], 'Hour': ['-'], 'NEE': ['umol_m-2_s-1'], 'LE': ['Wm-2'], 'H': ['Wm-2'],
    'Rg': ['Wm-2'], 'Tair': ['degC'], 'Tsoil': ['degC'], 'rH': ['%'], 'VPD': ['hPa'], 'Ustar': ['ms-1'],
    'CH4flux': ['umol_m-2_s-1']
}
rep_df = plot_data.copy()
for column, filter in filters_db.items():
    filter = get_column_filter(rep_df, filters_db, column)
    rep_df.loc[~filter.astype(bool), column] = np.nan

gl.rep_level3_fpath = gl.out_dir / f"REddyProc_{config.metadata.site_name}_{int(plot_data[time_col].dt.year.median())}.txt"
export_rep_level3(gl.rep_level3_fpath, rep_df, time_col, output_template, config, gl.points_per_day)

# %% [markdown] id="e50f7947"
# ## A file for Information and Analytical System used in the RuFlux network (IAS)
# Level 2 file, written from the input data **without taking into account** filtering  
#
# Option `config.data_export.ias.split_intervals` also specifies the number of exported files: one per month `IasExportIntervals.MONTH`, one per year `IasExportIntervals.YEAR`, or all data in a single file `IasExportIntervals.ALL`.

# %% id="yaLoIQmtzaYd"
if not config.from_file:
    config.data_export.ias.split_intervals = IasExportIntervals.YEAR

if config.calc.has_meteo:
    swin_vals = data['swin_1_1_1'] if 'swin_1_1_1' in data.columns else None
    export_ias(gl.out_dir, config.metadata.site_name, config.data_export.ias.out_fname_ver_suffix,
               config.data_export.ias.split_intervals,
               df_ias_export, time_col=time_col, swin_vals=swin_vals)

# %% [markdown] id="Pm8hiMrb_wRW"
# ## File for FAT
# Level 3 file (filtered data) ready for input into the Flux Analysis Tool

# %% [markdown] id="0ll51nOal6Lz"
# ![image.png](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA8EAAAAiCAYAAAB/cNuxAAAOHUlEQVR4nO2d69WrKhPHJ2udXsQO0sP7QdJButASzOe3ATsIfjg9PB2EVJPD4CV4jUk03v6/tdfeO4oKAwwMDPDPw0AAAAAAAAAAAMAO+GfuCAAAAAAAAAAAAL8CRjAAAAAAAAAAgN3gGMGK5OFEaS2AF95Ix6J6UUck/AvdnUvB9UFKFrcF+RdB14d5Z+M5c+2mqf7K36IpEhEddS1+qyPLM3Jkn8Hp802+1a+DXmz5NGXTltv2+mDxQrrpmGYtwqsgl2FwpUelILrlc4ickRfddMimIpcvwlDRBujh7cPGUPJAp9bCR9zw1cr2Hsnqs5JtZcG9116GhpTDPZSzbvZdx7P+5D2ra/Hfs4122+uu//84rmvTFcuX7fZ1y/LzYAI+TsP4tk1jJjioGFRcaHw6aKfymn8PppZzOF2Eswk6kMgLk4gVhcqnKDIFsyxcJvLyQmTCzNmWKSnNXzGRMPHkOJk4xrGcL0Jg0QSNAQbwNumJpOqX4xA5Iy+6qcuGO2O+PFY6XZ+EeaJb7re0DxuEy26xcQbLLBJ7NsjaEKYNDegSJUYutQEpnZC6B+Y+X20rQ0PK4T7K2Sv2Wcc1JeruxEmSfrWLjYhfh5mIdemKNch267plDXkwAQtKwwt3aEnqcbWjJ1kn1hSY3ACulBdO0FUb4zgy9iVb9qbgqpCULyk6Z7O+OpJ0oZBuMysEqc620PNo0OVgjPWbnjU+AGwbj8JQmEYsIi33PGP7W+Q5IDol3MR3jrQOCfPiK7X24cPIgvUjzxSY9j/RcWWQWyeK7kHcW75el0OUszZQx8EugG4BEzJgTbCkrBwp8//EGI8BXWVbsJhCzycOxpOtbBirUJEvIzrzNTsJ/KNOcGOq3Z1ClxSHnrkkzJ94ZrdsAHaAUQBXfaBIxWhkNofTPljFv1NyD6mCuV3sfg+XgxNFic5nZph8lmMUTyuUs/kYLvvStZMJrnSlEyXn3LjoqiN5f02Gmi7Fs9aN9UyJ6bfZS6cDHeruot2RaLqOXs0rim87LrK98Z2KD3XFfmW7HN2y3zyofruZlty2qy2VbZeBsQX/laT+56Szp05U0xBS+GHUuxi0MZYQXuFtYGInOgxZQUdzQ/2ZgDILUbhF+36WqEX0CUxmSCNwlRdAeVz/6E/KFajlevDzmGyPNtnur4P7PTIOKfJ51LVduQ+RM/JiOCpJbaMnvwwzhEr7sEvYQ0pTeHtkbZxt8J9eUHuBZ11Ortti4a4o+58bWg5Rzqosro5z38pOduT1wHZszefPNibddcQ+nJoQN3o8BBVrN2V0Jq1v5uPOGkD990HsU2PgGAPDtD3Fu+2ArOiL71R8qCt2LttF6Jad54H7vda08LpsYwCLcqks3+uQgZGPKl7Hsqp4GGcu6tY260rDt0lwGHF3aE1s/1Yt5Nyf30Q6XkpvgF2388IeL8Up/Uuaa3zyme+Z4rMlsA51JNjrIjjk+wQ0b2NN8Hc0Bgjs6Kz8PgxB7q/hwR35/CmOdjO33VFzW+xyVxxSDkGTxddx07G6e5LORVfPegemeT/kVR3xTPEpH7Teer5udCg/xKOwtJYElfZOb3yn4kNdsXfZLkG37D0PnO+1pkUllLK8i6i4M/jn+nMONp6ho3/yd/LM/Hn6OjrICNb6Tp4QdjMp766pL+vEcSHGLgBgUUh1peTA+wa0WMHgK8YaRPikM1y2DzumuSust8P179x5iciPFMVK2KVRYUth+tTg2ns5W3od1zwLIs6d5b6/jmSehNPQ/u5X8Z2KT3QFZDu/bkEeDPjePSX/cKnfef1cRyz77o3FACNYEXsUCDbFjUClV9/1uQgW0eXesV4YAACKhkwmo6/rAHPhtA97xfS6TmngHAnI7lzRvHGaCXGW5PkJKW0PNiM1WrFAOZuPYbIX2Xo40+WVzW7ryzqSeRLKH2Zvb3yn4kNdAdnOr1uQBwXtabHf82T7kZU9bt5ZPGvB9b3z3ti8MILV85xPaaOUuzfX1tLmPt28Pk92veqX5K4IZUZZAx1rZAGYGxHHFPBssDf1+B6Ynnr7sE/saLX37GjoKKKUtwaZfhB7ediBcklJxI2vGin5KGfz8Ybsraegeu7i6/S7XteRO6ly4yNF0YWPjeEPTuic3BPfqfhYV0C28+sW5EFOR1rMn+B0cjZAdTYk7sss6+ruPpcNSth3ir/J62jDCK771LNh+3BnfU3he9yyc4Gf4bznwuVFkM84mTjaiXneFS1IKZk5VmB9tG865tmjtZZT3teEJHVN6HC6VxqxIXJGXszPy/Zhh5QbQOZuYCyTa+DTychK7m49taCzJPJ5M5MvygXK2Xx8LPviRJCy3xWW6/d668j/2S8osIfYHA7PnWwnH/Doie90n/xQV0C2NLtuQR7kdKXF9O1uYdU2LO71frT5nN3w1L6znobxbTnHCOaF3QM3irIHHcfDwrLRPMP+UyLWVI3iYxmz1KPSlWdiM5t+/ZTKAd5v1AfQQW2ziPKyqxOGyBl50c1Y8nsVBnnA8FmSsnE107fVFvFBe5VWs+0tQF3/jPXU8Wre80xQsT6wp46wJ6H559habmp9GbeNfvf/Le/rju/3jK0rINv5dQvyIKM9LUV8Wm7U49n6u92mnNqWG3F3aAAAAAAAsDvssTCKZOGZY4+x8X66DvIt1hTfNcWVWVt8h7C2NK0tvjMBIxgAAAAAAHRjO9UXunfc5p159VXToXBdzK8t1oudZ5+WEl/Idn6QB7sERjAAAAAAAOhm0DK4D5a/NVw6f8hMy/UaQLbzgzx4zZxpmQgYwQAAAAAAAAAAdgOMYAAAAAAAAAAAuwFG8BjkawmIt/X+mcN9dgaXktVv6kiQr2oHVtv4aYrLg7zHikJ1DYX30/SPDeS5SqbKi/LdE+XHLDrjQyDjwd9y15Ptqv72lpH8LM76ZS+s6lUwH6jjv2PvuuJdoFvAhMAI/hZjIB2MoRQGXB1/CZ+Z5tFFu6esa0qUUa3u4dL2sqa7J8ZVCLkiF7xZgCx+S4rOaz2zFfIEDlPmx2w6Y2FsRcb8rVOabZwii4vZoNpBX+mxr4OCOwlq56AqeSBfHiGfLbOVOj4W0BWTAN0CPgVG8JeoP2FHnLS8/FwRi6NpRS4Jj4XlI2Sa9D2gIEjJteVUkpInRx4Vq28iYH7HwYWixDRuK7XaIE9QMmF+zKkzFsUmZGw6sFFqZ3Kq/a22cyOBizwb6+Xk6luwOTZRx8cCuuJXQLeAoWzTCM7dJ2So6XLJnE6s4jHVwXd+d7mf8CjSqfSv8Ci8dY9ayjhTXXrM+A9FnimgiP7Mx+3ZXyqhNDjTTZi0lxe1vS/OLQn4Uk61l3V/Zy1AnuPScGPKRrx1/CAl3pRVPoJeMEiOP8yP2XQGZNzK6Hq5Szb27MUAA1V1rLx0bx61P/Nm+dsDqOOtzNr36gO6YlqgW8CIbNMItqRGSd/o8RB5BfCNEnd+R4mpBC2zeebeSYd0e+T3OKyM6LzI9QWChHc3tlo2qqpN6+IJc+0sTQuRp69QvLLrHR/KqY6K6EJGbp3fWQOQ528ZKCvuhOUuZNkIOq8DMmGP3Akc6RuvXtOXH4vWGZDx1/TJhiZYGrF2bBkguj507ywMe9QYoeZhjExtxzY/xxLLQd4AdXwxQFdMC3QLGJkNG8HOiJsxZDzzT+X3XZO7+rOCuwaUz9mSv4jvJ7jrWIkSxdEV7NdL4p5k6Xu5fvULORWUimlFjVUrkOdvGSgrK/PQcSGTFIce+ZxBL33IfpQfi9UZkPHX9Mnm/KM4rAVrBHA+NjexSU8HOrgX7OY1RShJys1Q1rkrcXKdH9TxxQBdMR3QLWACSiPY7oKbu7bwCMpNRJXfu1lgzor3xiNFB7rYC0+XnLqMliATnqX0fF77cCZ9N0acbV0knYOTNeJopPWrXWnProtWxbRGIM/lwTPyL7pX33/jm/xYmc5oAzLuiXefbIYaALsgpZPPLodB69365jV1qq6wjAeZjgjq+PRAV0wFdMsS2KKdWBrBItb0qIwGytrvHeFu5sCjl76kIyvvhowWQD6q9Rdl61dVcVl4RiGb69oz8f6+ujfLB1nZbM5ggzwXh92wTFWvaX1vDfvxN77NjzXpjBYg457P9slGnEl6PkWRHkUvrJvA5iNxh5MNmnc6ROwKmwZOOWA30miKSO4W1PHpga6YCuiWJbBFO3HD7tCfYUc6dPysZNb1R88ap36yWcpIEXnyqVjtOlZep1POZo5Nsc6if23G+oA8R6MYUNDFRmMR8aBh+1huD7xh2YnzJC7XWWVLfvjH37hxLhmeH7PqDMh4enplw26hAV1O+bo/+XzMzj7o/Z1XKdWNQmHkofpnZ1zsDJonn4fTRRGlfJIqps1Qx9cEdMWkQLeAsYERXEPEylayg7PAgF0tZGvo2kHdqXnuQj93C+BZynt6p+Do1GhuONMLpSYuaoqP8s7JRpGkpetSzkpdIlwgz7Hg9VAR+UWaTFquQUrJB+9Rt9C6yRXV0u7uKGm6rUHfyI95dQZk3PLi0WXcKRt7++nG6a5L4zCP1zsObRBBscrkJV+4KZZPcP4qn/xD7ghrZHcNfDqdhr9ju6COt7x4EX2vJtAV0wLdAsZlm0awdal543f14TfObOMF950v+hmtLkhD4vaNnFiZz5/0SYA8x6Mpy6JT86as6udNdoXruzdZfsyrMyDjxovH18tdshl6f+v0lqUh+dGWvw/aoEr8CNTxxosX0fdqBbpiXKBbwIRs0wgGAAAAAAAAAABagBEMAAAAAAAAAGA3wAgGAAAAAAAAALAbYAQDAAAAAAAAANgN/wEMdGIfq5jj3QAAAABJRU5ErkJggg==)

# %% id="w9hkPLkB_zd1"
if config.calc.has_meteo:
    fat_output_template = {
        'DoY': ['--'], r'u*': ['m s-1'], 'H': ['W m-2'], 'lE': ['-'], 'NEE': ['umol m-2 s-1'],
        'PPFD': ['umol m-2 s-1'], 'Ta': ['oC'], 'VPD': ['kPa'], 'PPFD_gapfilling': ['umol m-2 s-1'],
        'Ta_gapfilling': ['oC'], 'VPD_gapfilling': ['kPa'], 'period': ['--']
    }
    
    fat_df = plot_data.copy()
    for column, filter in filters_db.items():
        filter = get_column_filter(fat_df, filters_db, column)
        fat_df.loc[~filter.astype(bool), column] = np.nan
    
    export_fat(fat_df, fat_output_template, time_col, gl, config)
    del fat_df

# %% [markdown] id="GQ1bpermu8eq"
# ## File with all filtered data
# The file contains the original variables (fluxes, meteorological variables). The "tmp_datetime" column is the result of forming a single date-time from the two columns of the full output file - date, time. The "datetime" column is the result of the date-time correction for the tmp_datetime column. "datetime_meteo" is the result of the date-time correction for the "timestamp_1" column. The file contains flags for each filter to each variable (fluxes, meteorology) in binary format: 1 means that filter was not applied, 0 - applied.

# %% id="pk1lGANovC5U"
full_column_list = [c for c in plot_data.columns]
full_column_list = full_column_list.insert(0, full_column_list.pop(full_column_list.index(time_col)))
if 'date' in plot_data.columns:
    plot_data.loc[plot_data['date'].isna(), 'date'] = plot_data[time_col].dt.date
if 'time' in plot_data.columns:
    plot_data.loc[plot_data['time'].isna(), 'time'] = plot_data[time_col].dt.time

all_fpath = gl.out_dir / 'output_all.csv'
plot_data.fillna(-9999).to_csv(all_fpath, index=None, columns=full_column_list)
ff_logger.info(f"Basic file saved to {all_fpath}")

# %% [markdown] id="-MSrgUD0-19l"
# ## Summary file of filtered results
# Short output file after filtering. Contains important input variables (meteorological parameters and fluxes), filtered important variables (index _filtered), integral flag for each variable, average diurnal cycles in 30- and 10-day windows for filtered variables.

# %% id="22dPWc2u-6IG"
columns_to_save = ['Date', 'Time', 'DoY', 'ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg',
                   'ch4_flux', 'u_star']

basic_df = plot_data.copy()

basic_df['Date'] = basic_df[time_col].dt.date
basic_df['Time'] = basic_df[time_col].dt.time
basic_df['DoY'] = np.round(
    basic_df[time_col].dt.dayofyear + basic_df[time_col].dt.hour / 24. + basic_df[time_col].dt.minute / 24. / 60.,
    decimals=3)

if not config.calc.has_meteo:
    basic_df['ta_1_1_1'] = basic_df['air_temperature'] - 273.15
# meteo
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
    # print(f"{col}(_[1-9]){{1,4}})")
    col_pos = [bool(re.fullmatch(f"{col}(_[1-9]){{1,4}}", col_in)) for col_in in basic_df.columns]
    if not any(col_pos):
        continue
    else:
        real_col = basic_df.columns[np.argmax(col_pos)]
        basic_df[col] = basic_df[real_col]

# Filtered fluxes
for col in ['nee', 'h', 'le', 'co2_strg', 'ch4_flux']:
    if col not in basic_df.columns:
        continue
    basic_df[f"{col}_filtered"] = basic_df[col]
    filter = get_column_filter(basic_df, filters_db, col)
    basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
    columns_to_save.append(f"{col}_filtered")

# Filtered meteo
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
    if col not in basic_df.columns:
        continue
    basic_df[f"{col}_filtered"] = basic_df[col]
    filter = get_column_filter(basic_df, filters_db, col)
    basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
    columns_to_save.append(f"{col}_filtered")

# Flags
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg', 'nee',
            'ch4_flux']:  # ['nee', 'ch4', 'le', 'h']:
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
    basic_df[f'{col_out}_10d'] = bg.calc_rolling(basic_df[f"{col}_filtered"], rolling_window=10, step=gl.points_per_day,
                                                 min_periods=7)
    basic_df[f'{col_out}_30d'] = bg.calc_rolling(basic_df[f"{col}_filtered"], rolling_window=30, step=gl.points_per_day,
                                                 min_periods=7)
    columns_to_save.append(f'{col_out}_10d')
    columns_to_save.append(f'{col_out}_30d')

basic_df = basic_df[[col for col in columns_to_save if col in basic_df.columns]]
basic_df = basic_df.fillna(-9999)

summary_fpath = gl.out_dir / 'output_summary.csv'
basic_df.to_csv(summary_fpath, index=None)
ff_logger.info(f"New basic file saved to {summary_fpath}")
# %% [markdown] id="775a473e"
# # Processing with the REddyProc tool
# This block performs 1) filtering by the friction velocity threshold (u* threshold), 2) filling gaps in meteorological variables and 30-minute fluxes, 3) separating NEE into gross primary production (GPP) and ecosystem respiration (Reco), 4) calculating daily, monthly, annual averages and the average diurnal cycle by months.

# %% [markdown] id="034b04a5"
# ## Filtering and gapfilling
#
# `config_reddyproc` are the settings that correspond to the options of [the online tool](https://www.bgc-jena.mpg.de/REddyProc/ui/REddyProc.php).
#
# **It is necessary to check:**  
#
# Enabling detection of the conditions of weak turbulence  
# `is_to_apply_u_star_filtering=True`  
# The Eddy Covariance method is applicable only in the conditions of the developed turbulence. When the friction velocity (*uStar* column) is below a certain threshold, the CO2 flux may be underestimated. Flux data in these conditions are replaced by gaps.
#
# Switch between season marking methods, with the saturation level determined separately for each season. `Continuous` - seasons start in March, June, September, and December, December is included in the *next* year. `WithinYear` treats each year separately. `User` divides the year by the user-defined *season* column.  
# `u_star_seasoning="Continuous"`  
# Uncertainty estimation of the u threshold* (bootstrap)  
# `is_bootstrap_u_star=False`  
#
# Compared to the original REddyProc tool, this notebook adds the ability to substitute a custom threshold value in cases where the threshold cannot be calculated (e.g., if data are lacking or solar income radiation *Rg* is missing). For grassland ecosystems, you can use a minimal threshold of `0.01`, for forest ecosystems - `0.1`, to disable substitution - `None`.  
# `ustar_threshold_fallback=0.01`  
# REddyProc by default applies the uStar threshold only at night, which requires the *Rg* column to determine day/night-time. The following experimental option allows to use theoretical value `"Rg_th_Py"` or `"Rg_th_REP"`, or to ignore the absence of *Rg* and apply the threshold to all data, regardless of the time of day - `""`:  
# `ustar_rg_source="Rg"`  
#
# If an error occurs during filtering, a warning appears in the cell log and the cell reruns with a transition to the gap filling. 
# Gap filling in the 30-minute fluxes corresponds to the online tool and is enabled by default.
#
# Enable and select one or both methods of partitioning the CO2 flux into the gross primary production (GPP) and the ecosystem respiration (Reco). The method `Reichstein05` performs the separation based on the night-time data, the method `Lasslop10` uses the day-time data.  
# `is_to_apply_partitioning=True`  
# `partitioning_methods=["Reichstein05", "Lasslop10"]`  
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
# Filling gaps in 30-minute fluxes  
# `is_to_apply_gap_filling=True`  
#
# **Additional options (consistent with previous sections):**  
#
# The name of the station, added to the names of the output files:  
# `site_id=config.meta.site_name`  
# The file from which the time series are loaded:  
# `input_file=str(gl.rep_level3_fpath)`  
# The directory to which the tool writes test graphs, basic statistics on gaps, filled series:  
# `output_dir=str(gl.out_dir / 'reddyproc')`
# %% id="278caec5"

config_reddyproc = RepConfig(
    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # "Rg_th_Py", "Rg_th_REP" - estimate by theoretical algs,
    # "Rg" - by real data, "" - ignore Rg and filter both days and nights
    ustar_rg_source="Rg",
    is_bootstrap_u_star=False,
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
    site_id=config.metadata.site_name,
    u_star_method="RTw",
    is_to_apply_gap_filling=True,
    input_file=str(gl.rep_level3_fpath),
    output_dir=str(gl.out_dir / 'reddyproc'),
)

if not config.from_file:
    config.reddyproc = config_reddyproc
config.reddyproc.input_file = config_reddyproc.input_file
config.reddyproc.output_dir = config_reddyproc.output_dir
config.reddyproc.site_id = config_reddyproc.site_id

ipython_enable_word_wrap()

prepare_rg(config.reddyproc)
ensure_empty_dir(config.reddyproc.output_dir)
gl.rep_out_info, config.reddyproc = reddyproc_and_postprocess(config.reddyproc, gl.repo_dir)

# %% [markdown] id="0bed439c"
# ## Selected graphs
# Displays individual graphs from the online tool in a convenient form for checking.  
# The filled data, graphs and statistics can be downloaded in one archive by clicking the **Download reddyproc outputs** button.
#
# **Additional options:**  
#   
# The order and set of graphs are formed automatically in the variable `output_sequence`, which can be changed or re-declared using tags.  
# Tags for this particular version of the notebook will be visible after the cell is run by calling `display_tag_info`.

# %% id="e66a94ab"
rep_out_dir = Path(config.reddyproc.output_dir)
tag_handler = RepImgTagHandler(main_path=rep_out_dir, rep_cfg=config.reddyproc, rep_out_info=gl.rep_out_info,
                               img_ext='.png')
rog = RepOutputGen(tag_handler)

output_sequence: tuple[str | list[str], ...] = (
    "## Heat maps",
    rog.hmap_compare_row('NEE_*'),
    rog.hmap_compare_row('LE_f'),
    rog.hmap_compare_row('H_f'),
    "## Diurnal course",
    rog.diurnal_cycle_row('NEE_*'),
    rog.diurnal_cycle_row('LE_f'),
    rog.diurnal_cycle_row('H_f'),
    "## 30-minute fluxes and daily averages",
    rog.flux_compare_row('NEE_*'),
    rog.flux_compare_row('LE_f'),
    rog.flux_compare_row('H_f')
)

roh = RepOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=gl.rep_out_info)
roh.prepare_images_safe()
gl.rep_arc_exclude_files = roh.img_proc.raw_img_duplicates

rep_arc_path = rep_out_dir / (gl.rep_out_info.fnames_prefix + '.zip')
create_archive(arc_path=rep_arc_path, dirs=rep_out_dir, top_dir=rep_out_dir,
               include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=roh.img_proc.raw_img_duplicates)

colab_add_download_button(rep_arc_path, 'Download reddyproc outputs')

roh.display_images_safe()

tag_handler.display_tag_info(roh.extended_tags())

# %% [markdown] id="HEead6faY22W"
# # Downloading results
#
# The results of all the segments of the notebook can be downloaded in one archive using the **Download outputs** button.  
#
# If the button below does not appear, you need to run the cell again or download the output files in the Files section, output directory. In the summary files with indexes in the name _hourly (daily variations of filtered and filled variables), _daily (average daily values), _monthly (average monthly values) and _yearly (values for the year, if there is less data - for the entire processing period) the index _sqc means the percentage of values remaining after filtering (but without taking into account the REddyProc filter on u*), and the columns with indexes _f mean the final filled data after all the cells of the notebook.

# %% id="E4rv4ucOX8Yz"
FFConfig.save(config, gl.out_dir / f'config_{config.metadata.site_name}.yaml', add_comments=True)

arc_path = gl.out_dir / 'FluxFilter_output.zip'
create_archive(arc_path=arc_path, dirs=[gl.out_dir, config.reddyproc.output_dir], top_dir=gl.out_dir,
               include_fmasks=['*.png', '*.csv', '*.txt', '*.log', '*.yaml'], exclude_files=gl.rep_arc_exclude_files)
colab_add_download_button(arc_path, 'Download outputs')
