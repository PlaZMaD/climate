import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.ias_cols import COLS_IAS_EXPORT_MAP, COLS_IAS_IMPORT_MAP, \
	COLS_IAS_KNOWN,COLS_IAS_TIME, COLS_IAS_UNUSED_NORENAME_IMPORT
from src.data_io.ias_error_check import set_lang, draft_check_ias
from src.data_io.table_loader import load_table_logged
from src.data_io.time_series_utils import df_init_time_draft
from src.helpers.pd_helpers import df_ensure_cols_case
from src.helpers.py_helpers import sort_fixed, intersect_list

# TODO 1 more tests of ias export to match import after export 1y fixed


def ias_table_extend_year(df: pd.DataFrame, time_col, na_placeholder):
	# TODO 1 appeared to be bugfix of bug introduced in 0.9.3, which skipped last year of IAS export
	# after bug fixed, extending year on import won't be nessesary anymore, remove whole func

	# add extra row, because main script expects currently for 2020 year extra row at the start of 2021
	# specifically, ias export currently requires 2 years, not 1
	# it does not look right, but not changing export yet
	freq = df.index.freq
	last_timestamp: pd.Timestamp = df.last_valid_index()
	next_timestamp = last_timestamp + freq
	if next_timestamp.year - last_timestamp.year == 1:
		new_row = df.loc[last_timestamp].copy()
		new_row.loc[time_col] = next_timestamp
		new_row.loc[df.columns != time_col] = na_placeholder
		# TODO QE 3 how to add new row properly with auto index?
		df.loc[next_timestamp] = new_row
		df.index.freq = freq
	return df


def process_ias_col_names(df: pd.DataFrame, time_col):
	print('Переменные в IAS: \n', df.columns.to_list())

	known_ias_cols = COLS_IAS_KNOWN + [time_col]
	df = df_ensure_cols_case(df, known_ias_cols, ignore_missing=True)

	unknown_cols = df.columns.difference(known_ias_cols)
	if len(unknown_cols) > 0:
		msg = 'Неизвестные ИАС переменные: \n', str(unknown_cols)
		logging.exception(msg)
		raise NotImplementedError(msg)

	unsupported_cols = df.columns.intersection(COLS_IAS_UNUSED_NORENAME_IMPORT)
	if len(unsupported_cols) > 0:
		# TODO 2 localize properly, remove prints (logging.* goes to stdout too)
		print('Переменные, которые не используются в тетради (присутствуют только в загрузке - сохранении): \n',
		      unsupported_cols.to_list())
		logging.warning('Unsupported by notebook IAS vars (only save loaded): \n' + str(unsupported_cols.to_list()))

	df = df.rename(columns=COLS_IAS_IMPORT_MAP)
	print('Переменные после загрузки: \n', df.columns.to_list())

	# TODO 2 QE prob remove whole biomet_cols_index from the script
	expected_biomet_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
	biomet_cols_index = df.columns.intersection(expected_biomet_cols)
	return df, biomet_cols_index


def import_ias(config, config_meteo):
	# TODO 2 move to ipynb?
	set_lang('ru')

	# TODO 2 merge with config, pack biomet into load routines only?
	assert config_meteo['use_biomet']

	# TODO QV 1 implement merge for iases if necessary
	if len(config['path']) != 1:
		raise NotImplemented(
			'Multiple IAS files detected. Multiple run or combining multiple files is not supported yet.')
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

	# TODO QE 2 (TIMESTAMP_START + TIMESTAMP_END) / 2?
	time_col = 'datetime'
	df[time_col] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
	df = df.drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis='columns')
	df = df_init_time_draft(df, time_col)

	print('Диапазон времени IAS (START): ', df.index[[0, -1]])
	logging.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))
	df = ias_table_extend_year(df, time_col, -9999)

	print('Replacing -9999 to np.nan')
	df.replace(-9999, np.nan, inplace=True)

	df, biomet_cols_index = process_ias_col_names(df, time_col)
	return df, time_col, biomet_cols_index, df.index.freq, config_meteo


def export_ias_prepare_time_cols(df: pd.DataFrame, time_col):
	# possibly will be applied later to each year separately

	# TODO QE QV 1 new_time_index is incorrect if ddata does not contain next year extra row,
	# year.min() == year.max() if full 1 year, last year skipped - bug introduced  0.9.2 -> 0.9.3
	new_time_index = pd.date_range(start=f'01.01.{df[time_col].dt.year.min()}',
	                               end=f'01.01.{df[time_col].dt.year.max()}',
	                               freq=df.index.freq, inclusive='left')
	df_new_time = pd.DataFrame(index=new_time_index)
	df = df_new_time.join(df, how='left')
	df[time_col] = df.index

	df['TIMESTAMP_START'] = df[time_col].dt.strftime('%Y%m%d%H%M')
	time_end = df[time_col] + pd.Timedelta(0.5, 'h')
	df['TIMESTAMP_END'] = time_end.dt.strftime('%Y%m%d%H%M')

	# TODO QE QV 1 365, 366, 1 (current) -> 365, 366, 367 (IAS docs specification)
	day_part = (time_end.dt.hour * 60 * 60 + time_end.dt.minute * 60 + time_end.dt.second) / (24.0 * 60 * 60)
	df['DTime'] = time_end.dt.dayofyear + np.round(day_part, decimals=3)

	# original floating point routine had %
	# s_in_day = pd.Timedelta(days=1).total_seconds()
	# span = time_end - time_end[0] + pd.Timedelta(0.5, 'h')
	# day_part = span.dt.seconds % s_in_day / s_in_day
	# df['DTime'] = np.round(span.dt.days + 1 + day_part, decimals=3)
	return df


def export_ias(out_dir: Path, ias_output_prefix, ias_output_version, df: pd.DataFrame, time_col: str, data_swin_1_1_1):
	# TODO QE 2 explicitly attr/mark new columns created as a result of processing in one of the args
	#  instead of hardcoding them in this function?

	# think about abstraction, i.e. how much script-aware should be ias import and export?
	# may be even merge each import and export routine?
	# TODO 3 may be add test: load ias -> convert to eddypro -> convert to ias -> save ias ?

	df = df.fillna(-9999)

	df = df.rename(columns=COLS_IAS_EXPORT_MAP)
	var_cols = intersect_list(df.columns, COLS_IAS_EXPORT_MAP.values())
	sort_fixed(var_cols, fix_underscore=True)

	df = export_ias_prepare_time_cols(df, time_col)

	# TODO QE 1 why they were separate ifs? moved to COLS_IAS_EXPORT_MAP
	'''
	if 'h_strg' in df.columns:
		df['SH_1_1_1'] = df['h_strg']
		var_cols.append('SH_1_1_1')
	if 'le_strg' in df.columns:
		df['SLE_1_1_1'] = df['le_strg']
		var_cols.append('SLE_1_1_1')
	'''

	# TODO QE 1 why SW_IN_1_1_1 was not added to var_cols? why data col?
	#  was swin_1_1_1 changed during script run and unchanged data is exported? any other similar cases?
	if 'SW_IN_1_1_1' in df.columns:
		# assert df['SW_IN_1_1_1'] == data_swin_1_1_1
		df['SW_IN_1_1_1'] = data_swin_1_1_1


	col_list_ias = COLS_IAS_TIME + var_cols + [time_col]
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
			# TODO QE 2 this seems should not be caught ?
			fpath.unlink(missing_ok=True)
			'''
			try:
				os.remove(os.path.join('output',ias_filename))
			except Exception as e:
				logging.exception(e)
			'''

			# print(f'not enough data for {year}')
			logging.info(f'{year} not saved, not enough data!')
	# ias_year = df[time_col].dt.year.min()
	# fname = f'{ias_output_prefix}_{ias_year}_{ias_output_version}.csv'
	# ias_df.to_csv(os.path.join('output',fname), index=False)
	# logging.info(f'IAS file saved to {os.path.join("output",ias_filename)}.csv')
