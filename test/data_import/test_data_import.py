import src.helpers.os_helpers  # noqa: F401

from src.data_import.data_import import auto_detect_input_files
from src.helpers.py_helpers import init_logging


def test_auto_detect_input_files():
	init_logging(to_stdout=False)
	config = {'mode': 'auto', 'path': 'auto'}
	config_meteo = {'use_biomet': 'auto', 'path': 'auto'}
	ias_output_prefix, ias_output_version = 'auto', ''

	n_config, n_config_meteo, n_ias_output_prefix, n_ias_output_version = (
		auto_detect_input_files(config, config_meteo, ias_output_prefix, ias_output_version))
	assert True
