import logging
from pathlib import Path
import numpy as np
import pandas as pd

import bglabutils.basic as bg
from src.data_import.ias_error_check import set_lang, draft_check_ias
from src.helpers.pd_helpers import df_intersect_cols


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
	try:
		data = load_ias_file_by_ext(fpath)
	except Exception as e:
		logging.error(e)
		raise

	logging.info(f"File {fpath} loaded.\n")
	return data


def load_via_bglabutils(fpath):
	config = {}
	config['debug'] = False
	config['-9999_to_nan'] = True
	config['repair_time'] = False

	config['time'] = {}
	config['time']['column_name'] = 'datetime'

	def my_datetime_converter(x):
		return pd.to_datetime(x['TIMESTAMP_START'], format='%Y%m%d%H%M')

	config['time']['converter'] = my_datetime_converter
	config['path'] = [fpath]

	data, time = bg.load_df(config)
	return data[next(iter(data))]


def check_with_bglabutils(fpath, data):
	data_verify = load_via_bglabutils(fpath)
	df1, df2 = df_intersect_cols(data[1:], data_verify)
	assert df1 == df2


def rename_cols_ias_to_eddy(df_ias: pd.DataFrame):
	eddy_to_ias_map = {
		"co2_flux": "FC_1_1_1", "qc_co2_flux": "FC_SSITC_TEST_1_1_1", "LE": "LE_1_1_1",
		"qc_LE": "LE_SSITC_TEST_1_1_1", "H": "H_1_1_1", "qc_H": "H_SSITC_TEST_1_1_1", "Tau": "TAU_1_1_1",
		"qc_Tau": "TAU_SSITC_TEST_1_1_1", "co2_strg": "SC_1_1_1", "co2_mole_fraction": "CO2_1_1_1",
		"h2o_mole_fraction": "H2O_1_1_1", "sonic_temperature": "T_SONIC_1_1_1", "u_star": "USTAR_1_1_1",
		"Ta_1_1_1": "TA_1_1_1", "Pa_1_1_1": "PA_1_1_1", "Swin_1_1_1": "SW_IN_1_1_1",
		"Swout_1_1_1": "SW_OUT_1_1_1",
		"Lwin_1_1_1": "LW_IN_1_1_1", "Lwout_1_1_1": "LW_OUT_1_1_1", "PPFD_1_1_1": "PPFD_IN_1_1_1",
		"Rn_1_1_1": "NETRAD_1_1_1", "MWS_1_1_1": "WS_1_1_1", "Ts_1_1_1": "TS_1_1_1",
		"Ts_2_1_1": "TS_2_1_1",
		"Ts_3_1_1": "TS_3_1_1", "Pswc_1_1_1": "SWC_1_1_1", "Pswc_2_1_1": "SWC_2_1_1",
		"Pswc_3_1_1": "SWC_3_1_1",
		"SHF_1_1_1": "G_1_1_1", "SHF_2_1_1": "G_2_1_1", "SHF_3_1_1": "G_3_1_1", "L": "MO_LENGTH_1_1_1",
		"(z-d)/L": "ZL_1_1_1", "x_peak": "FETCH_MAX_1_1_1", "x_70%": "FETCH_70_1_1_1",
		"x_90%": "FETCH_90_1_1_1",
		"ch4_flux": "FCH4_1_1_1", "qc_ch4_flux": "FCH4_SSITC_TEST_1_1_1",
		"ch4_mole_fraction": "CH4_1_1_1",
		"ch4_strg": "SCH4_1_1_1",
		"ch4_signal_strength": "CH4_RSSI_1_1_1", "co2_signal_strength": "CO2_STR_1_1_1",
		"rh_1_1_1": "RH_1_1_1", "vpd_1_1_1": "VPD_1_1_1"
	}
	ias_to_eddy_map = {item.lower(): key for key, item in eddy_to_ias_map.items()}

	rename_map = {col: ias_to_eddy_map[col.lower()] for col in df_ias.columns if col.lower() in ias_to_eddy_map}
	unknown_cols = set(df_ias.columns) - set(rename_map.keys())

	if len(unknown_cols) > 0:
		raise Exception(f'Cannot process, next columns are not recognised: {unknown_cols}')

	return df_ias.rename(columns=rename_map)


def load_ias(config, config_meteo):
	# TODO move to ipynb?
	set_lang('ru')

	# TODO merge with config?
	assert config_meteo['use_biomet']

	# TODO merge
	if len(config['path']) != 1:
		raise Exception('Multiple IAS files are not supported yet')

	fpath = config['path'][0]
	draft_check_ias(fpath)
	df = load_ias_file_safe(fpath)
	check_with_bglabutils(fpath, df)

	df['datetime'] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
	time_col = 'datetime'
	df.index = df['datetime']

	print('Replacing -9999 to np.nan')
	df.replace(-9999, np.nan, inplace=True)

	'''
	ias_df = plot_data.copy()
	for column, filter in filters_db.items():
		filter = get_column_filter(ias_df, filters_db, column)
		ias_df.loc[~filter.astype(bool), column] = np.nan
	ias_df = ias_df.fillna(-9999)
	'''

	df = rename_cols_ias_to_eddy(df)

	'''
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']
	var_cols = [col_match[col] for col in col_match.keys() if col_match[col] in ias_df.columns]

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

	if 'h_strg' in ias_df.columns:
		ias_df['SH_1_1_1'] = ias_df['h_strg']
		var_cols.append('SH_1_1_1')
	if 'le_strg' in ias_df.columns:
		ias_df['SLE_1_1_1'] = ias_df['le_strg']
		var_cols.append('SLE_1_1_1')

	if 'SW_IN_1_1_1' in ias_df.columns:
		ias_df['SW_IN_1_1_1'] = df['swin_1_1_1']

	ias_year = ias_df[time_col].dt.year.min()
	var_cols.sort()
	col_list_ias = time_cols + var_cols + [time_col]
	print(col_list_ias)
	ias_df = ias_df[col_list_ias]

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
	'''

	# ias_filename = f"{ias_output_prefix}_{ias_year}_{ias_output_version}.csv"
	# ias_df.to_csv(os.path.join('output',ias_filename), index=False)
	# logging.info(f"IAS file saved to {os.path.join('output',ias_filename)}.csv")

	# TODO improve
	df.index.freq = df.index[2] - df.index[1]
	assert df.index.freq == df.index[-1] - df.index[-2]
	# TODO 'timestamp_1', 'datetime'?
	expected_biomet_columns = ['ta_1_1_1', 'rh_1_1_1', 'rg_1_1_1', 'lwin_1_1_1',
	                           'lwout_1_1_1', 'swin_1_1_1', 'swout_1_1_1', 'p_1_1_1']

	biomet_columns = list(set(df.columns.str.lower()) & set(expected_biomet_columns))
	return df, time_col, biomet_columns, df.index.freq, config_meteo
