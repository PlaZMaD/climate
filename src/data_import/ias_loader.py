import logging
from copy import copy
from pathlib import Path
import numpy as np
import pandas as pd

import bglabutils.basic as bg
from src.helpers.py_helpers import invert_dict
from src.data_import.ias_error_check import set_lang, draft_check_ias
from src.helpers.pd_helpers import df_get_unique_cols, df_ensure_cols_case

# TODO fix ias export to match import
# possibly extract to abstract time series converter class later?
# possibly store in table file instead?
# currently 4 column names variations are possible: IAS file, EddyPro file, notebook import, export (after all the processing)

COLS_EDDYPRO_TO_IAS = {
	# specifically about conversion of file formats,
	# SCRIPT_TO_IAS != EDDYPRO_TO_IAS because script renames some of them during run
	"co2_flux": "FC_1_1_1", "qc_co2_flux": "FC_SSITC_TEST_1_1_1",
	"LE": "LE_1_1_1", "qc_LE": "LE_SSITC_TEST_1_1_1",
	"H": "H_1_1_1", "qc_H": "H_SSITC_TEST_1_1_1",
	"Tau": "TAU_1_1_1", "qc_Tau": "TAU_SSITC_TEST_1_1_1",
	"co2_strg": "SC_1_1_1", "co2_mole_fraction": "CO2_1_1_1",
	"h2o_mole_fraction": "H2O_1_1_1", "sonic_temperature": "T_SONIC_1_1_1",
	"Ta_1_1_1": "TA_1_1_1", "Pa_1_1_1": "PA_1_1_1",
	"Swin_1_1_1": "SW_IN_1_1_1", "Swout_1_1_1": "SW_OUT_1_1_1",
	"Lwin_1_1_1": "LW_IN_1_1_1", "Lwout_1_1_1": "LW_OUT_1_1_1",
	"Rn_1_1_1": "NETRAD_1_1_1", "MWS_1_1_1": "WS_1_1_1",
	"Ts_1_1_1": "TS_1_1_1", "Ts_2_1_1": "TS_2_1_1", "Ts_3_1_1": "TS_3_1_1",
	"Pswc_1_1_1": "SWC_1_1_1", "Pswc_2_1_1": "SWC_2_1_1", "Pswc_3_1_1": "SWC_3_1_1",
	"SHF_1_1_1": "G_1_1_1", "SHF_2_1_1": "G_2_1_1", "SHF_3_1_1": "G_3_1_1", "L": "MO_LENGTH_1_1_1",
	"(z-d)/L": "ZL_1_1_1",
	"x_peak": "FETCH_MAX_1_1_1", "x_70%": "FETCH_70_1_1_1", "x_90%": "FETCH_90_1_1_1",
	"ch4_flux": "FCH4_1_1_1", "qc_ch4_flux": "FCH4_SSITC_TEST_1_1_1", "ch4_mole_fraction": "CH4_1_1_1",
	"ch4_strg": "SCH4_1_1_1", "ch4_signal_strength": "CH4_RSSI_1_1_1", "co2_signal_strength": "CO2_STR_1_1_1",

	# TODO are they correct?
	"u*": "USTAR_1_1_1",
	"PPFD_1_1_1": "PPFD_IN_1_1_1",
	"Rh_1_1_1": "RH_1_1_1", "VPD_1_1_1": "VPD_1_1_1",

	# Optional
	'H_strg': 'SH_1_1_1', 'LE_strg': 'SLE_1_1_1',
}
COLS_SCRIPT_TO_IAS = {
	# only overrides of COLS_EDDYPRO_TO_IAS
	"u_star": "USTAR_1_1_1", "vpd_1_1_1": "VPD_1_1_1"
}
COLS_NS_IAS = [
	# NS = Not Supported, i.e. cols ignored by script yet, but should be save-loaded
	'ALB_1_1_1',

	'FH2O_1_1_1', 'P_1_1_1',
	'TS_1_2_1', 'TS_1_3_1', 'TS_1_4_1',
	'T_DP_1_1_1', 'U_SIGMA_1_1_1', 'VPD_PI_1_1_1', 'V_SIGMA_1_1_1', 'WD_1_1_1', 'WTD_1_1_1', 'W_SIGMA_1_1_1'
]
COLS_NS_IAS_TO_SCRIPT = {k: k.lower() for k in COLS_NS_IAS}
COLS_EDDYPROL_TO_IAS = {k.lower(): v for k, v in COLS_EDDYPRO_TO_IAS.items()}

# IAS optional rules are more complex and placed into IAS check tool

COLS_IAS_TO_SCRIPT = invert_dict(COLS_EDDYPROL_TO_IAS)
COLS_IAS_TIME = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']


def load_csv(fpath):
	return pd.read_csv(fpath)


def load_xls(fpath):
	data = pd.read_excel(fpath)
	if isinstance(data, dict):
		if len(data.values()) > 1:
			logging.error(_("Several lists in data file!"))
			assert False
		else:
			data = next(iter(data.values()))
	return data


def load_ias_file_by_ext(fpath):
	# probably extract to load table? can time repair be generalised operation on table?

	suffix = Path(fpath).suffix.lower()
	if suffix == '.csv':
		data = load_csv(fpath)
	elif suffix in ['.xls', '.xlsx']:
		data = load_xls(fpath)
	else:
		raise Exception(_(f"Unknown file type {suffix}. Select CSV, XLS or XLSX file."))
	return data


def load_ias_file_safe(fpath):
	# with log_exception(...) instead
	try:
		data = load_ias_file_by_ext(fpath)
	except Exception as e:
		logging.error(e)
		raise

	logging.info(f"File {fpath} loaded.\n")
	return data


def load_via_bglabutils(fpath):
	def my_datetime_converter(x):
		return pd.to_datetime(x['TIMESTAMP_START'], format='%Y%m%d%H%M')

	config = {
		'debug': False,
		'-9999_to_nan': True,
		'repair_time': False,
		'time': {
			'column_name': 'datetime',
			'converter': my_datetime_converter
		},
		'path': [fpath]
	}

	data, time = bg.load_df(config)
	return data[next(iter(data))]


def check_with_bglabutils(fpath, data):
	data_bgl = load_via_bglabutils(fpath).drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis='columns')
	data_cmpr = data[1:-1]
	df1, df2 = df_get_unique_cols(data_cmpr, data_bgl)

	if df1.columns.size + df2.columns.size > 0:
		raise Exception(f'bglabutils.load_df loads different ias table. df1: {df1.columns} df2: {df2.columns}')


def ias_table_extend_year(df: pd.DataFrame, time_step, time_col, na_placeholder):
	# TODO remove and fix export instead?
	# add extra row, because main script expects currently for 2020 year extra row at the start of 2021
	# specifically, ias export currently requires 2 years, not 1
	# it does not look right, but not changing export yet

	last_timestamp: pd.Timestamp = df[time_col].iloc[-1]
	next_timestamp = last_timestamp + time_step
	if next_timestamp.year - last_timestamp.year == 1:
		last_row: pd.Series = df.iloc[-1].copy()
		last_row.loc[time_col] = next_timestamp
		last_row.loc[df.columns != time_col] = na_placeholder

		df.loc[next_timestamp] = last_row
	return df


def process_col_names(df: pd.DataFrame, time_col):
	print("Переменные в IAS: \n", df.columns.to_list())

	known_correct_ias_cols = (list(COLS_IAS_TO_SCRIPT.keys()) + COLS_IAS_TIME + [time_col] + COLS_NS_IAS)
	df = df_ensure_cols_case(df, known_correct_ias_cols, ignore_missing=True)

	unknown_cols = df.columns.difference(known_correct_ias_cols)
	if len(unknown_cols) > 0:
		msg = "Неизвестные ИАС переменные: \n",      str(unknown_cols)
		logging.exception(msg)
		raise NotImplementedError(msg)

	unsupported_cols = df.columns.intersection(COLS_NS_IAS)
	if len(unsupported_cols) > 0:
		print("Колонки, поддержка которых в тетради пока отсутствует (присутствуют только в загрузке - сохранении): \n" +
		      str(unsupported_cols))
		logging.warning('Unsupported by notebook columns (only save loaded): \n' + str(unsupported_cols))

	df = df.rename(columns=COLS_IAS_TO_SCRIPT)
	print("Переменные после загрузки: \n", df.columns.to_list())

	# TODO 'timestamp_1', 'datetime'?
	expected_biomet_cols = np.strings.lower(['Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1',
	                                         'Lwout_1_1_1', 'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1'])
	biomet_cols_index = df.columns.intersection(expected_biomet_cols)
	return df, biomet_cols_index


def load_ias(config, config_meteo):
	# TODO move to ipynb?
	set_lang('ru')

	# TODO merge with config, pack biomet into load routines only?
	assert config_meteo['use_biomet']


	# TODO merge
	if len(config['path']) != 1:
		raise Exception('Multiple IAS files are not supported yet')
	fpath = config['path'][0]
	draft_check_ias(fpath)
	df = load_ias_file_safe(fpath)
	''' from eddypro to ias
	for year in ias_df.index.year.unique():
		ias_filename = f"{ias_output_prefix}_{year}_{ias_output_version}.csv"
		save_data = ias_df.loc[ias_df[time_col].dt.year == year]
		save_data = save_data.drop(time_col, axis=1)
		save_data = save_data.fillna(-9999)
		if len(save_data.index) >= 5:
			save_data.to_csv(os.path.join('output', ias_filename), index=False)
			logging.info(f"IAS file saved to {os.path.join('output', ias_filename)}.csv")
		else:
			try:
				os.remove(os.path.join('output', ias_filename))
			except Exception as e:
				print(e)

			print(f"not enough df for {year}")
			logging.info(f"{year} not saved, not enough df!")
	# ias_filename = f"{ias_output_prefix}_{ias_year}_{ias_output_version}.csv"
	# ias_df.to_csv(os.path.join('output',ias_filename), index=False)
	'''


	df['datetime'] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
	df = df.drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis="columns")
	time_col = 'datetime'
	df.index = df['datetime']
	# TODO improve
	df.index.freq = df.index[2] - df.index[1]
	assert df.index.freq == df.index[-1] - df.index[-2]
	print("Диапазон времени IAS (START): ", df.index[[0, -1]])
	logging.info("Time range for full_output: " + " - ".join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
	df = ias_table_extend_year(df, df.index.freq, time_col, -9999)
	# TODO improve
	df.index.freq = df.index[2] - df.index[1]
	''' from eddypro to ias
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']

	new_time = pd.DataFrame(
		index=pd.date_range(start=f"01.01.{ias_df[time_col].dt.year.min()}", end=f"01.01.{ias_df[time_col].dt.year.max()}",
							freq=ias_df.index.freq, inclusive='left'))
	ias_df = new_time.join(ias_df, how='left')
	ias_df[time_col] = ias_df.index

	ias_df['TIMESTAMP_START'] = ias_df[time_col].dt.strftime('%Y%m%d%H%M')
	ias_df['TIMESTAMP_END'] = (ias_df[time_col] + pd.Timedelta(0.5, "H")).dt.strftime('%Y%m%d%H%M')
	ias_df['DTime'] = np.round(
		ias_df[time_col].dt.dayofyear + 1. / 48 * 2 * ias_df[time_col].dt.hour + 1. / 48 * (ias_df[time_col].dt.minute // 30),
		decimals=3)
	'''


	print('Replacing -9999 to np.nan')
	df.replace(-9999, np.nan, inplace=True)
	''' from eddypro to ias	
	ias_df = plot_data.copy()
	for column, filter in filters_db.items():
		filter = get_column_filter(ias_df, filters_db, column)
		ias_df.loc[~filter.astype(bool), column] = np.nan
	ias_df = ias_df.fillna(-9999)
	'''


	try:
		if config['debug']:
			check_with_bglabutils(fpath, df)
	except Exception as e:
		logging.info('Unexpected check with bglabutils: ', e)


	df, biomet_cols_index = process_col_names(df, time_col)
	return df, time_col, biomet_cols_index, df.index.freq, config_meteo
