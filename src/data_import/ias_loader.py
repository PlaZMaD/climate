import logging
from pathlib import Path

import numpy as np
import pandas as pd

import bglabutils.basic as bg
from src.data_import.table_loader import load_table_from_file
from src.helpers.py_helpers import invert_dict, sort_fixed
from src.data_import.ias_error_check import set_lang, draft_check_ias
from src.helpers.pd_helpers import df_get_unique_cols, df_ensure_cols_case

# TODO 1 fix ias export to match import
# possibly extract to abstract time series converter class later?
# currently 4 column names variations are possible: IAS file, EddyPro file, notebook import, export (after all the processing)

# TODO Q store in table file instead (some cols are branching, like rain <-> heavey rain); other problems if table?
# specifically mark cols used in the script and unused?
# TODO 1 add missing from ias_error_check.known_columns
COLS_EDDYPRO_TO_IAS = {
	# specifically about conversion of file formats,
	# SCRIPT_TO_IAS != EDDYPRO_TO_IAS because script renames some of them during run
	"co2_flux": "FC_1_1_1", "qc_co2_flux": "FC_SSITC_TEST_1_1_1",
	"LE": "LE_1_1_1", "qc_LE": "LE_SSITC_TEST_1_1_1",
	"H": "H_1_1_1", "qc_H": "H_SSITC_TEST_1_1_1",
	"Tau": "TAU_1_1_1", "qc_Tau": "TAU_SSITC_TEST_1_1_1",
	"co2_strg": "SC_1_1_1", "co2_mole_fraction": "CO2_1_1_1",
	"h2o_mole_fraction": "H2O_1_1_1", "sonic_temperature": "T_SONIC_1_1_1",
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

	# TODO 1 are they correct, i.e. if conversion/rename happens as expected in the notebook?
	"Ta_1_1_1": "TA_1_1_1",
	"u*": "USTAR_1_1_1",
	"PPFD_1_1_1": "PPFD_IN_1_1_1",
	"Rh_1_1_1": "RH_1_1_1", "VPD_1_1_1": "VPD_1_1_1", "H2O_STR": "H2O_STR",

	# Optional
	'H_strg': 'SH_1_1_1', 'LE_strg': 'SLE_1_1_1',
}
COLS_EDDYPROL_TO_IAS = {k.lower(): v for k, v in COLS_EDDYPRO_TO_IAS.items()}
# IAS optional rules are more complex and placed into IAS check tool
COLS_IAS_TO_SCRIPT = invert_dict(COLS_EDDYPROL_TO_IAS)

COLS_SCRIPT_TO_IAS = {
	# only overrides of COLS_EDDYPRO_TO_IAS
	"u_star": "USTAR_1_1_1", "vpd_1_1_1": "VPD_1_1_1"
}
COLS_UNUSED_IAS = [
	# Script does not use, buu should keep (?) them during chain:
	# IAS import (rename to lower) -> script processing -> IAS export (rename back to upper)
	"PA_1_1_1",

	# Special cases:
	# albedo is calculated in the script instead of using this column
	'ALB_1_1_1',

	# TODO 1 P_1_1_1, P_RAIN are supported
	# TODO 1 problem: previously p_1_1_1 was not droppoing to outputs because it may be generated during script col
	# currently, it will because all these cols are included; what to do?
	'FH2O_1_1_1', 'P_1_1_1',
	'TS_1_2_1', 'TS_1_3_1', 'TS_1_4_1',
	'T_DP_1_1_1', 'U_SIGMA_1_1_1', 'VPD_PI_1_1_1', 'V_SIGMA_1_1_1', 'WD_1_1_1', 'WTD_1_1_1', 'W_SIGMA_1_1_1'
]
COLS_UNUSED_IAS_TO_SCRIPT = {k: k.lower() for k in COLS_UNUSED_IAS}

IAS_HEADER_DETECTION_COLS = COLS_EDDYPRO_TO_IAS.values()
COLS_IAS_TIME = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']


def load_ias_file_safe(fpath):
	# with log_exception(...) instead
	try:
		data = load_table_from_file(fpath)
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
	# TODO Q 1 remove and fix export instead? IAS has only 1 year after import,
	#  export will not fire without timstamp on the next year

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

	known_correct_ias_cols = (list(COLS_IAS_TO_SCRIPT.keys()) + COLS_IAS_TIME + [time_col] + COLS_UNUSED_IAS)
	df = df_ensure_cols_case(df, known_correct_ias_cols, ignore_missing=True)

	unknown_cols = df.columns.difference(known_correct_ias_cols)
	if len(unknown_cols) > 0:
		msg = "Неизвестные ИАС переменные: \n",      str(unknown_cols)
		logging.exception(msg)
		raise NotImplementedError(msg)

	unsupported_cols = df.columns.intersection(COLS_UNUSED_IAS)
	if len(unsupported_cols) > 0:
		print('Переменные, которые не используются в тетради (присутствуют только в загрузке - сохранении): \n',
		      unsupported_cols.to_list())
		logging.warning('Unsupported by notebook IAS vars (only save loaded): \n' + str(unsupported_cols.to_list()))

	df = df.rename(columns=COLS_IAS_TO_SCRIPT)
	print("Переменные после загрузки: \n", df.columns.to_list())

	# TODO 1 'timestamp_1', 'datetime'?
	expected_biomet_cols = np.strings.lower(['Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1',
	                                         'Lwout_1_1_1', 'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1'])
	biomet_cols_index = df.columns.intersection(expected_biomet_cols)
	return df, biomet_cols_index


def load_ias(config, config_meteo):
	# TODO 1 move to ipynb?
	set_lang('ru')

	# TODO 2 merge with config, pack biomet into load routines only?
	assert config_meteo['use_biomet']


	# TODO 2 merge
	if len(config['path']) != 1:
		raise Exception('Combining multiple IAS files is not supported yet')
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
	# TODO 1 improve
	df.index.freq = df.index[2] - df.index[1]
	assert df.index.freq == df.index[-1] - df.index[-2]
	print("Диапазон времени IAS (START): ", df.index[[0, -1]])
	logging.info("Time range for full_output: " + " - ".join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
	df = ias_table_extend_year(df, df.index.freq, time_col, -9999)
	# TODO 1 improve
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


# TODO 2 rename as separate commit: something like data_import -> data_io, ias_loader - ias_processing ?, etc
def export_ias(out_dir: Path, ias_output_prefix, ias_output_version, df: pd.DataFrame, time_col: str, data_swin_1_1_1):
	# TODO 3 explicitly name new columns created as a result of processing in one of the args
	#  instead of hardcoding them in this function?

	# think about abstraction, i.e. how much script-aware should be ias import and export?
	# may be even merge each import and export routine?
	# TODO 3 may be add test: load ias -> convert to eddypro -> convert to ias -> save ias ?

	df = df.fillna(-9999)

	# duplicated in ias src.data_import.ias_loader
	col_match = {"co2_flux": "FC_1_1_1", "qc_co2_flux": "FC_SSITC_TEST_1_1_1", "LE": "LE_1_1_1",
	             "qc_LE": "LE_SSITC_TEST_1_1_1", "H": "H_1_1_1", "qc_H": "H_SSITC_TEST_1_1_1", "Tau": "TAU_1_1_1",
	             "qc_Tau": "TAU_SSITC_TEST_1_1_1", "co2_strg": "SC_1_1_1", "co2_mole_fraction": "CO2_1_1_1",
	             "h2o_mole_fraction": "H2O_1_1_1", "sonic_temperature": "T_SONIC_1_1_1", "u_star": "USTAR_1_1_1",
	             "Ta_1_1_1": "TA_1_1_1", "Pa_1_1_1": "PA_1_1_1", "Swin_1_1_1": "SW_IN_1_1_1",
	             "Swout_1_1_1": "SW_OUT_1_1_1",
	             "Lwin_1_1_1": "LW_IN_1_1_1", "Lwout_1_1_1": "LW_OUT_1_1_1", "PPFD_1_1_1": "PPFD_IN_1_1_1",
	             "Rn_1_1_1": "NETRAD_1_1_1", "MWS_1_1_1": "WS_1_1_1", "Ts_1_1_1": "TS_1_1_1", "Ts_2_1_1": "TS_2_1_1",
	             "Ts_3_1_1": "TS_3_1_1", "Pswc_1_1_1": "SWC_1_1_1", "Pswc_2_1_1": "SWC_2_1_1",
	             "Pswc_3_1_1": "SWC_3_1_1",
	             "SHF_1_1_1": "G_1_1_1", "SHF_2_1_1": "G_2_1_1", "SHF_3_1_1": "G_3_1_1", "L": "MO_LENGTH_1_1_1",
	             "(z-d)/L": "ZL_1_1_1", "x_peak": "FETCH_MAX_1_1_1", "x_70%": "FETCH_70_1_1_1",
	             "x_90%": "FETCH_90_1_1_1",
	             "ch4_flux": "FCH4_1_1_1", "qc_ch4_flux": "FCH4_SSITC_TEST_1_1_1", "ch4_mole_fraction": "CH4_1_1_1",
	             "ch4_strg": "SCH4_1_1_1",
	             "ch4_signal_strength": "CH4_RSSI_1_1_1", "co2_signal_strength": "CO2_STR_1_1_1",
	             "rh_1_1_1": "RH_1_1_1", "vpd_1_1_1": "VPD_1_1_1"}
	col_match = {key.lower(): item for key, item in col_match.items()}
	col_match |= invert_dict(COLS_UNUSED_IAS_TO_SCRIPT)

	df = df.rename(columns=col_match)
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']
	var_cols = [col_match[col] for col in col_match.keys() if col_match[col] in df.columns]

	# TODO 2 still not correct at some lines
	# year.min() == year.max() if full 1 year
	new_time = pd.DataFrame(
		index=pd.date_range(start=f"01.01.{df[time_col].dt.year.min()}", end=f"01.01.{df[time_col].dt.year.max()}",
		                    freq=df.index.freq, inclusive='left'))
	df = new_time.join(df, how='left')
	df[time_col] = df.index

	# TODO 1 incorrect DTime at the end, test myltiyear
	# TODO 1 ias load multyear
	df['TIMESTAMP_START'] = df[time_col].dt.strftime('%Y%m%d%H%M')
	time_end = df[time_col] + pd.Timedelta(0.5, "h")
	df['TIMESTAMP_END'] = time_end.dt.strftime('%Y%m%d%H%M')
	df['DTime'] = np.round(time_end.dt.dayofyear +
	                           1. / 48 * 2 * time_end.dt.hour +
	                           1. / 48 * (time_end.dt.minute // 30), decimals=3)

	if 'h_strg' in df.columns:
		df['SH_1_1_1'] = df['h_strg']
		var_cols.append('SH_1_1_1')
	if 'le_strg' in df.columns:
		df['SLE_1_1_1'] = df['le_strg']
		var_cols.append('SLE_1_1_1')

	# TODO Q why not added to var_cols, why duplicate in col_match with other case?
	# what is going on, move from arg to ipynb aware preps before export
	if 'SW_IN_1_1_1' in df.columns:
		df['SW_IN_1_1_1'] = data_swin_1_1_1

	ias_year = df[time_col].dt.year.min()
	sort_fixed(var_cols, fix_underscore=True)
	col_list_ias = time_cols + var_cols + [time_col]
	print(col_list_ias)
	df = df[col_list_ias]

	for year in df.index.year.unique():
		fname = f"{ias_output_prefix}_{year}_{ias_output_version}.csv"
		fpath = out_dir / fname

		save_data = df.loc[df[time_col].dt.year == year]
		save_data = save_data.drop(time_col, axis=1)
		save_data = save_data.fillna(-9999)
		if len(save_data.index) >= 5:
			save_data.to_csv(fpath, index=False)
			logging.info(f"IAS file saved to {fpath}")
		else:
			# TODO Q this seems should not be caught ?
			try:
				fpath.unlink(missing_ok=True)
			except Exception as e:
				print(e)

			print(f"not enough data for {year}")
			logging.info(f"{year} not saved, not enough data!")
	# fname = f"{ias_output_prefix}_{ias_year}_{ias_output_version}.csv"
	# ias_df.to_csv(os.path.join('output',fname), index=False)
	# logging.info(f"IAS file saved to {os.path.join('output',ias_filename)}.csv")