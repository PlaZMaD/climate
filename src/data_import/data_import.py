import logging
from copy import copy
from enum import Enum
from pathlib import Path

from src.data_import.eddypro_loader import BIOMET_HEADER_DETECTION_COLS, EDDYPRO_HEADER_DETECTION_COLS
from src.data_import.ias_loader import IAS_HEADER_DETECTION_COLS
from src.data_import.table_loader import load_table_from_file


class ImportMode(Enum):
	# extension and processing level
	EDDYPRO1 = 1
	IAS2 = 2
	CSF1 = 3
	AUTO = 4


class ExpectedFileType(Enum):
	# extension and processing level
	UNKNOWN = 0
	EDDYPRO = 1
	BIOMET = 2
	CSF = 3
	IAS = 4


def detect_import_type(fpath, header_rows=4) -> ExpectedFileType:
	df = load_table_from_file(fpath, nrows=header_rows, header=None)

	ias_s = (set(IAS_HEADER_DETECTION_COLS), ExpectedFileType.IAS)
	biomet_s = (set(BIOMET_HEADER_DETECTION_COLS), ExpectedFileType.BIOMET)
	eddypro_s = (set(EDDYPRO_HEADER_DETECTION_COLS), ExpectedFileType.EDDYPRO)
	targets = [ias_s, biomet_s, eddypro_s]

	def match_ratio(sample: set, target: set):
		return len(sample & target) / len(target)

	matches = []
	for _, row in df.iterrows():
		names = set(row)
		for cols_set, ftype in targets:
			mr = match_ratio(names, cols_set)
			if mr > 0.5:
				matches += [(mr, ftype)]

	if len(matches) == 1:
		mr, ftype = matches[0]
		print(f'Detected file {fpath} as {ftype}')
		return ftype
	else:
		print(f'Cannot detect file type {fpath}, guesses are {matches}')
		return ExpectedFileType.UNKNOWN


def detect_files():
	root_files = list(Path('.').glob('*.*'))
	supported_file_exts_lower = ['.csv', '.xlsx', '.xls']
	input_files = [f for f in root_files if f.suffix.lower() in supported_file_exts_lower]
	return {f: detect_import_type(f) for f in input_files}


def auto_detect_input_files(config: dict, config_meteo: dict, ias_output_prefix: str, ias_output_version: str):
	n_config, n_config_meteo = copy(config), copy(config_meteo)
	n_ias_output_prefix, n_ias_output_version = copy(ias_output_prefix), copy(ias_output_version)

	# TODO just set it, check later that all changed options were 'auto' and not misleading override happened
	def set_path_if_auto(config, fpath):
		if config['path'] == 'auto':
			config['path'] = ['eddy_pro result_SSB 2023.csv']
		else:
			logging.warning(
				"config['path'] must be 'auto' to be changed under config['mode'] = 'auto'. Value won't be changed.")
		return config

	assert config['mode'] in ['csf_', 'ias_2', 'eddypro_1', 'auto']
	if config['mode'] == 'auto':
		input_file_types = list(detect_files().items())

		fcount = len(input_file_types)
		if fcount == 0:
			raise Exception("Cannot find any input files while using config['mode'] = 'auto' ")
		elif fcount == 1:
			fpath, ftype = input_file_types[0]
			if ftype in [ExpectedFileType.BIOMET, ExpectedFileType.UNKNOWN]:
				raise Exception(f"Incorrect file type detected: {fpath}, {ftype}")

			# TODO merge options
			n_config['mode'] = {ExpectedFileType.IAS: 'ias_2', ExpectedFileType.EDDYPRO: 'eddypro_1',
			                    ExpectedFileType.CSF: 'csf_'}[ftype]
			n_config['path'] = fpath
			n_config_meteo['use_biomet'] = (ftype == ExpectedFileType.IAS)
			n_config_meteo['path'] = None
		elif fcount == 2:
			if input_file_types[1][1] == ExpectedFileType.EDDYPRO:
				input_file_types[0], input_file_types[1] = input_file_types[1], input_file_types[0]

			fe, te = input_file_types[0]
			fb, tb = input_file_types[1]
			if tb != ExpectedFileType.BIOMET or te != ExpectedFileType.EDDYPRO:
				raise Exception("config['mode'] = 'auto' with 2 files requires exactly: eddypro and biomet files")

			n_config['mode'] = 'eddypro_1'
			n_config['path'] = fe
			n_config_meteo['use_biomet'] = True
			n_config_meteo['path'] = fb
		else:
			raise Exception("config['mode'] = 'auto' currently does not support more than 2 files. Please specify list "
			                "of file names and mode manually.")

	if n_config['mode'] == 'ias_2' and n_config_meteo['path'] != '':
		logging.warning(f"config_meteo['path'] value = {n_config_meteo['path']} "
		                f"will be ignored due to ias_2 input mode which reads just single ias file")

	# TODO why ias_output_prefix is not part of config?
	if ias_output_prefix == 'auto':
		if n_config['mode'] != 'ias_2':
			raise Exception("ias_output_prefix = 'auto' currently requires n_config['mode'] = 'ias_2' ")
		n_ias_output_prefix = 'tv_fy4'

	if ias_output_version == 'auto':
		if n_config['mode'] != 'ias_2':
			raise Exception("ias_output_version = 'auto' currently requires n_config['mode'] = 'ias_2' ")
		n_ias_output_version = 'v01'

	logging.info('Detected next auto settings: %s', n_ias_output_prefix)
	return n_config, n_config_meteo, n_ias_output_prefix, n_ias_output_version
