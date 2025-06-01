import logging
from pathlib import Path
import numpy as np
import pandas as pd

import bglabutils.basic as bg
from helpers.py_helpers import invert_dict
from src.data_import.ias_error_check import set_lang, draft_check_ias
from src.helpers.pd_helpers import df_get_unique_cols, df_repair_cols_case

# TODO fix ias export to match import
# possibly extract to abstract time series converter class later?
# possibly store in table file instead?
COLS_EDDYPRO_TO_IAS_MUST = {
	"co2_flux": "FC_1_1_1", "qc_co2_flux": "FC_SSITC_TEST_1_1_1",
	"LE": "LE_1_1_1", "qc_LE": "LE_SSITC_TEST_1_1_1",
	"H": "H_1_1_1", "qc_H": "H_SSITC_TEST_1_1_1",
	"Tau": "TAU_1_1_1", "qc_Tau": "TAU_SSITC_TEST_1_1_1",
	"co2_strg": "SC_1_1_1", "co2_mole_fraction": "CO2_1_1_1",
	"h2o_mole_fraction": "H2O_1_1_1", "sonic_temperature": "T_SONIC_1_1_1", "u_star": "USTAR_1_1_1",
	"Ta_1_1_1": "TA_1_1_1", "Pa_1_1_1": "PA_1_1_1",
	"Swin_1_1_1": "SW_IN_1_1_1", "Swout_1_1_1": "SW_OUT_1_1_1",
	"Lwin_1_1_1": "LW_IN_1_1_1", "Lwout_1_1_1": "LW_OUT_1_1_1",
	"PPFD_1_1_1": "PPFD_IN_1_1_1",
	"Rn_1_1_1": "NETRAD_1_1_1", "MWS_1_1_1": "WS_1_1_1",
	"Ts_1_1_1": "TS_1_1_1", "Ts_2_1_1": "TS_2_1_1", "Ts_3_1_1": "TS_3_1_1",
	"Pswc_1_1_1": "SWC_1_1_1", "Pswc_2_1_1": "SWC_2_1_1", "Pswc_3_1_1": "SWC_3_1_1",
	"SHF_1_1_1": "G_1_1_1", "SHF_2_1_1": "G_2_1_1", "SHF_3_1_1": "G_3_1_1", "L": "MO_LENGTH_1_1_1",
	"(z-d)/L": "ZL_1_1_1",
	"x_peak": "FETCH_MAX_1_1_1", "x_70%": "FETCH_70_1_1_1", "x_90%": "FETCH_90_1_1_1",
	"ch4_flux": "FCH4_1_1_1", "qc_ch4_flux": "FCH4_SSITC_TEST_1_1_1", "ch4_mole_fraction": "CH4_1_1_1",
	"ch4_strg": "SCH4_1_1_1", "ch4_signal_strength": "CH4_RSSI_1_1_1", "co2_signal_strength": "CO2_STR_1_1_1",
	"rh_1_1_1": "RH_1_1_1", "vpd_1_1_1": "VPD_1_1_1"
}
COLS_EDDYPRO_TO_IAS_OPTIONAL = {
	'h_strg': 'SH_1_1_1', 'le_strg': 'SLE_1_1_1', 'swin_1_1_1': 'SW_IN_1_1_1'
}

# IAS optional rules are more complex and placed into IAS check tool
COLS_IAS_TO_EDDYPRO = invert_dict(COLS_EDDYPRO_TO_IAS_MUST) | invert_dict(COLS_EDDYPRO_TO_IAS_OPTIONAL)
COLS_IAS_TO_EDDYPRO_SPECIAL = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']


def load_csv(fpath):
	return pd.read_csv(fpath)


def load_xls(fpath):
	data = pd.read_excel(fpath)
	if len(data) > 1:
		raise Exception(_("Several lists in data file!"))
	data = next(iter(data.values()))
	return data


def load_ias_file_by_ext(fpath):
	suffix = Path(fpath).suffix.lower()
	if suffix == '.csv':
		data = load_csv(fpath)
	elif suffix == ['.xls', '.xlsx']:
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
	data_bgl = load_via_bglabutils(fpath)
	data_cmpr = data[1:]
	df1, df2 = df_get_unique_cols(data_cmpr, data_bgl)

	if not (df1.columns + df2.columns).empty:
		raise Exception(f'bglabutils.load_df loads different ias table. df1: {df1.columns} df2: {df2.columns}')


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
	time_col = 'datetime'
	df.index = df['datetime']
	# TODO improve
	df.index.freq = df.index[2] - df.index[1]
	assert df.index.freq == df.index[-1] - df.index[-2]
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
		check_with_bglabutils(fpath, df)
	except Exception as e:
		logging.info('Unexpected check with bglabutils: ', e)


	known_correct_cols = list(COLS_IAS_TO_EDDYPRO.keys()) + COLS_IAS_TO_EDDYPRO_SPECIAL
	df = df_repair_cols_case(df, known_correct_cols, ignore_missing=True)
	df = df.rename(columns=COLS_IAS_TO_EDDYPRO)


	# TODO 'timestamp_1', 'datetime'?
	expected_biomet_columns = ['ta_1_1_1', 'rh_1_1_1', 'rg_1_1_1', 'lwin_1_1_1',
							   'lwout_1_1_1', 'swin_1_1_1', 'swout_1_1_1', 'p_1_1_1']
	biomet_columns = list(set(df.columns.str.lower()) & set(expected_biomet_columns))

	return df, time_col, biomet_columns, df.index.freq, config_meteo
