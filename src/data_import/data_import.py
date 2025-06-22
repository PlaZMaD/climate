import dataclasses
import logging
import re
from copy import copy
from enum import Enum
from pathlib import Path
from typing import Dict

from src.data_import.eddypro_loader import BIOMET_HEADER_DETECTION_COLS, EDDYPRO_HEADER_DETECTION_COLS
from src.data_import.ias_loader import IAS_HEADER_DETECTION_COLS
from src.data_import.table_loader import load_table_from_file
from src.helpers.py_helpers import invert_dict

SUPPORTED_FILE_EXTS_LOWER = ['.csv', '.xlsx', '.xls']


class ImportMode(Enum):
	# extension and processing level
	EDDYPRO1 = 1
	EDDYPRO1_AND_BIOMET = 2
	IAS2 = 3
	CSF_ = 4
	AUTO = 5


class InputFileType(Enum):
	# extension and processing level
	UNKNOWN = 0
	EDDYPRO = 1
	BIOMET = 2
	CSF = 3
	IAS = 4


def detect_file_type(fpath: Path, header_rows=4) -> InputFileType:
	df = load_table_from_file(fpath, nrows=header_rows, header=None)

	ias_cols = (set(IAS_HEADER_DETECTION_COLS), InputFileType.IAS)
	biomet_cols = (set(BIOMET_HEADER_DETECTION_COLS), InputFileType.BIOMET)
	eddypro_cols = (set(EDDYPRO_HEADER_DETECTION_COLS), InputFileType.EDDYPRO)
	detect_col_targets = [ias_cols, biomet_cols, eddypro_cols]

	def match_ratio(sample: set, target: set):
		return len(sample & target) / len(target)

	# upper/lower case is yet skipped intentionally
	matches = []
	for _, row in df.iterrows():
		names = set(row)
		for cols_set, ftype in detect_col_targets:
			mr = match_ratio(names, cols_set)
			if mr > 0.5:
				matches += [(mr, ftype)]

	if len(matches) == 1:
		mr, ftype = matches[0]
		logging.info(f'Detected file {fpath} as {ftype}')
		return ftype
	else:
		logging.warning(f'Cannot detect file type {fpath}, guesses are {matches}')
		return InputFileType.UNKNOWN


def detect_input_files(input_dir='.') -> dict[Path, InputFileType]:
	root_files = list(Path(input_dir).glob('*.*'))
	input_files = [f for f in root_files if f.suffix.lower() in SUPPORTED_FILE_EXTS_LOWER]
	return {f: detect_file_type(f) for f in input_files}


def change_if_auto(option, new_option=None, new_option_call=None, ok_msg=None, skip_msg=None):
	# new_option_call can be used instead of new_option to optimise out new option detection:
	# if not auto, detection will be skipped

	if option != 'auto':
		if skip_msg:
			logging.warning(skip_msg)
		return option

	if new_option_call:
		assert new_option is None
		new_option = new_option_call()

	if ok_msg:
		logging.info(ok_msg)
	return new_option


def detect_input_mode(input_file_types: dict[Path, InputFileType]):
	input_ftypes = list(input_file_types.values())
	possible_input_modes = []

	if InputFileType.EDDYPRO in input_ftypes:
		if InputFileType.BIOMET not in input_ftypes:
			possible_input_modes += [ImportMode.EDDYPRO1]
		else:
			if input_ftypes.count(InputFileType.BIOMET) > 2:
				raise Exception('More than 2 biomet files detected')
			possible_input_modes += [ImportMode.EDDYPRO1_AND_BIOMET]

	if InputFileType.IAS in input_ftypes:
		possible_input_modes += [ImportMode.IAS2]

	if len(possible_input_modes) == 0:
		raise Exception(f'No input files detected, ensure correct files are placed into script dir')
	elif len(possible_input_modes) == 1:
		mode = possible_input_modes[0]
	else:
		raise Exception(f'Multiple input modes detected, cannot auto pick one')

	logging.info(f'Picked input mode: {mode}')
	return mode


def auto_config_ias_input(input_file_types: dict[Path, InputFileType]):
	config_path = list(input_file_types.keys())
	config_meteo_use_biomet = True
	config_meteo_path = None

	fname = str(config_path[0])
	ias_name_match = re.match(r"(.*)_(\d{2,4})_(v\d{1,3})", fname)
	if ias_name_match:
		ias_output_prefix = ias_name_match.group(1)
		ias_output_version = ias_name_match.group(3)
	else:
		logging.warning(f'Cannot parse ias file name {fname} for site_id and version, using defaults')
		ias_output_prefix = 'unknown_site'
		ias_output_version = 'vNN'

	return config_path, config_meteo_use_biomet, config_meteo_path, ias_output_prefix, ias_output_version


def auto_config_eddypro_input(input_file_types: dict[Path, InputFileType]):
	# 1 or 0 biomet is already ensured

	config_path = [k for k, v in input_file_types.items() if v == InputFileType.EDDYPRO]

	biomets = [k for k, v in input_file_types.items() if v == InputFileType.BIOMET]
	if len(biomets) == 1:
		config_meteo_use_biomet = True
		config_meteo_path = biomets[0]
	else:
		config_meteo_use_biomet = False
		config_meteo_path = None

	ias_output_prefix = 'unknown_site'
	ias_output_version = 'vNN'

	return config_path, config_meteo_use_biomet, config_meteo_path, ias_output_prefix, ias_output_version


def auto_detect_input_files(config: dict, config_meteo: dict, ias_output_prefix: str, ias_output_version: str):
	# TODO Q why 2 configs intead of one? merge options?
	i_m = ImportMode
	assert type(config['mode']) is i_m

	if config['mode'] == i_m.AUTO:
		logging.info("Detecting input files due to config['mode'] = .AUTO ")
		input_file_types = detect_input_files()
		config['mode'] = detect_input_mode(input_file_types)
	else:
		input_file_types = None

	if config['mode'] in [i_m.EDDYPRO1, i_m.EDDYPRO1_AND_BIOMET] and ias_output_prefix == 'auto':
		logging.warning("ias_output_prefix = 'auto' currently is not supported with eddypro mode")
	if config['mode'] == [i_m.EDDYPRO1, i_m.EDDYPRO1_AND_BIOMET] and ias_output_version == 'auto':
		logging.warning("ias_output_version = 'auto' currently is not supported with eddypro mode")

	# TODO 3 update messages after updating config options
	mode_calls = {i_m.IAS2: auto_config_ias_input,
	              i_m.EDDYPRO1: auto_config_eddypro_input, i_m.EDDYPRO1_AND_BIOMET: auto_config_eddypro_input}
	mode_call = mode_calls.get(config['mode'], None)
	if mode_call:
		config_path, config_meteo_use_biomet, config_meteo_path, ias_output_prefix_d, ias_output_version_d = mode_call(input_file_types)
		config['path'] = change_if_auto(config['path'], new_option=config_path,
		                                skip_msg="config['path'] option is not 'auto'. Auto path detection skipped.")
		config_meteo['use_biomet'] = change_if_auto(config_meteo['use_biomet'], new_option=config_meteo_use_biomet,
		                                            skip_msg="config_meteo['use_biomet'] option is not 'auto'. Auto detection skipped.")
		config_meteo['path'] = change_if_auto(config_meteo['path'], new_option=config_meteo_path,
		                                      skip_msg="config_meteo['path'] option is not 'auto'. Auto detection skipped.")
		# TODO Q why ias_output_prefix is not part of config?
		ias_output_prefix = change_if_auto(ias_output_prefix, ias_output_prefix_d)
		ias_output_version = change_if_auto(ias_output_version, ias_output_version_d)
	else:
		raise NotImplementedError

	if config['mode'] == 'ias_2' and config_meteo['path'] is not None:
		logging.warning(f"config_meteo['path'] value = {config_meteo['path']} "
		                f"will be ignored due to ias_2 input mode (ias file includes biomet)")

	return config, config_meteo, ias_output_prefix, ias_output_version
