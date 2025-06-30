import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.ias_cols import COLS_IAS_EXPORT_MAP, COLS_IAS_IMPORT_MAP, \
	COLS_IAS_KNOWN, COLS_IAS_UNUSED_NORENAME_IMPORT
from src.data_io.ias_error_check import set_lang, draft_check_ias
from src.data_io.table_loader import load_table_logged
from src.helpers.pd_helpers import df_get_unique_cols, df_ensure_cols_case
from src.helpers.py_helpers import invert_dict, sort_fixed

# TODO 1 fix ias export to match import


def ias_table_extend_year(df: pd.DataFrame, time_step, time_col, na_placeholder):
	# TODO 2 Q possibly extract to abstract time series converter class later?
	# TODO Q 2 remove and fix export instead? IAS has only 1 year after import,
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
	print('Переменные в IAS: \n', df.columns.to_list())

	known_ias_cols = COLS_IAS_KNOWN + [time_col]
	df = df_ensure_cols_case(df, known_ias_cols, ignore_missing=True)

	unknown_cols = df.columns.difference(known_ias_cols)
	if len(unknown_cols) > 0:
		msg = 'Неизвестные ИАС переменные: \n',      str(unknown_cols)
		logging.exception(msg)
		raise NotImplementedError(msg)

	unsupported_cols = df.columns.intersection(COLS_IAS_UNUSED_NORENAME_IMPORT)
	if len(unsupported_cols) > 0:
		print('Переменные, которые не используются в тетради (присутствуют только в загрузке - сохранении): \n',
		      unsupported_cols.to_list())
		logging.warning('Unsupported by notebook IAS vars (only save loaded): \n' + str(unsupported_cols.to_list()))

	df = df.rename(columns=COLS_IAS_IMPORT_MAP)
	print('Переменные после загрузки: \n', df.columns.to_list())

	# TODO 2 'timestamp_1', 'datetime'? prob remove whole biomet_cols_index
	expected_biomet_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
	biomet_cols_index = df.columns.intersection(expected_biomet_cols)
	return df, biomet_cols_index


def load_ias(config, config_meteo):
	# TODO 2 move to ipynb?
	set_lang('ru')

	# TODO 2 merge with config, pack biomet into load routines only?
	assert config_meteo['use_biomet']

	# TODO 2 implement merge for iases if nessesary
	if len(config['path']) != 1:
		raise Exception('Combining multiple IAS files is not supported yet')
	fpath = config['path'][0]
	draft_check_ias(fpath)
	df = load_table_logged(fpath)
	''' from eddypro to ias
	for year in ias_df.index.year.unique():
		ias_filename = f'{ias_output_prefix}_{year}_{ias_output_version}.csv'
		save_data = ias_df.loc[ias_df[time_col].dt.year == year]
		save_data = save_data.drop(time_col, axis=1)
		save_data = save_data.fillna(-9999)
		if len(save_data.index) >= 5:
			save_data.to_csv(os.path.join('output', ias_filename), index=False)
			logging.info(f'IAS file saved to {os.path.join('output', ias_filename)}.csv')
		else:
			try:
				os.remove(os.path.join('output', ias_filename))
			except Exception as e:
				print(e)

			print(f'not enough df for {year}')
			logging.info(f'{year} not saved, not enough df!')
	# ias_filename = f'{ias_output_prefix}_{ias_year}_{ias_output_version}.csv'
	# ias_df.to_csv(os.path.join('output',ias_filename), index=False)
	'''


	df['datetime'] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
	df = df.drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis='columns')
	time_col = 'datetime'
	df.index = df['datetime']
	# TODO 1 improve
	df.index.freq = df.index[2] - df.index[1]
	assert df.index.freq == df.index[-1] - df.index[-2]
	print('Диапазон времени IAS (START): ', df.index[[0, -1]])
	logging.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
	df = ias_table_extend_year(df, df.index.freq, time_col, -9999)
	# TODO 1 improve
	df.index.freq = df.index[2] - df.index[1]
	''' from eddypro to ias
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']

	new_time = pd.DataFrame(
		index=pd.date_range(start=f'01.01.{ias_df[time_col].dt.year.min()}', end=f'01.01.{ias_df[time_col].dt.year.max()}',
							freq=ias_df.index.freq, inclusive='left'))
	ias_df = new_time.join(ias_df, how='left')
	ias_df[time_col] = ias_df.index

	ias_df['TIMESTAMP_START'] = ias_df[time_col].dt.strftime('%Y%m%d%H%M')
	ias_df['TIMESTAMP_END'] = (ias_df[time_col] + pd.Timedelta(0.5, 'H')).dt.strftime('%Y%m%d%H%M')
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


	df, biomet_cols_index = process_col_names(df, time_col)
	return df, time_col, biomet_cols_index, df.index.freq, config_meteo


def export_ias(out_dir: Path, ias_output_prefix, ias_output_version, df: pd.DataFrame, time_col: str, data_swin_1_1_1):
	# TODO 3 explicitly name new columns created as a result of processing in one of the args
	#  instead of hardcoding them in this function?

	# think about abstraction, i.e. how much script-aware should be ias import and export?
	# may be even merge each import and export routine?
	# TODO 2 may be add test: load ias -> convert to eddypro -> convert to ias -> save ias ?

	df = df.fillna(-9999)

	df = df.rename(columns=COLS_IAS_EXPORT_MAP)
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']
	var_cols = [COLS_IAS_EXPORT_MAP[col] for col in COLS_IAS_EXPORT_MAP.keys() if COLS_IAS_EXPORT_MAP[col] in df.columns]

	# TODO 1 still not correct at some lines
	# year.min() == year.max() if full 1 year
	new_time = pd.DataFrame(
		index=pd.date_range(start=f'01.01.{df[time_col].dt.year.min()}', end=f'01.01.{df[time_col].dt.year.max()}',
		                    freq=df.index.freq, inclusive='left'))
	df = new_time.join(df, how='left')
	df[time_col] = df.index

	# TODO 1 incorrect DTime at the end, test myltiyear
	# TODO 1 ias load multyear
	df['TIMESTAMP_START'] = df[time_col].dt.strftime('%Y%m%d%H%M')
	time_end = df[time_col] + pd.Timedelta(0.5, 'h')
	df['TIMESTAMP_END'] = time_end.dt.strftime('%Y%m%d%H%M')
	df['DTime'] = np.round(time_end.dt.dayofyear +
	                           1. / 48 * 2 * time_end.dt.hour +
	                           1. / 48 * (time_end.dt.minute // 30), decimals=3)

	# TODO 1 investigate where they belong: script aware or export aware or _separate colnames table_?
	if 'h_strg' in df.columns:
		df['SH_1_1_1'] = df['h_strg']
		var_cols.append('SH_1_1_1')
	if 'le_strg' in df.columns:
		df['SLE_1_1_1'] = df['le_strg']
		var_cols.append('SLE_1_1_1')

	# TODO Q 1 why not added to var_cols, why duplicate in COLS_IAS_EXPORT with other case?
	# what is going on, move from arg to ipynb aware preps before export
	if 'SW_IN_1_1_1' in df.columns:
		df['SW_IN_1_1_1'] = data_swin_1_1_1

	ias_year = df[time_col].dt.year.min()
	sort_fixed(var_cols, fix_underscore=True)
	col_list_ias = time_cols + var_cols + [time_col]
	print(col_list_ias)
	df = df[col_list_ias]

	for year in df.index.year.unique():
		fname = f'{ias_output_prefix}_{year}_{ias_output_version}.csv'
		fpath = out_dir / fname

		save_data = df.loc[df[time_col].dt.year == year]
		save_data = save_data.drop(time_col, axis=1)
		save_data = save_data.fillna(-9999)
		if len(save_data.index) >= 5:
			save_data.to_csv(fpath, index=False)
			logging.info(f'IAS file saved to {fpath}')
		else:
			# TODO Q 2 this seems should not be caught ?
			try:
				fpath.unlink(missing_ok=True)
			except Exception as e:
				print(e)

			print(f'not enough data for {year}')
			logging.info(f'{year} not saved, not enough data!')
	# fname = f'{ias_output_prefix}_{ias_year}_{ias_output_version}.csv'
	# ias_df.to_csv(os.path.join('output',fname), index=False)
	# logging.info(f'IAS file saved to {os.path.join("output",ias_filename)}.csv')
