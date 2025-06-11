import src.helpers.os_helpers  # noqa: F401

from src.data_import.data_import import auto_detect_input_files


def test_auto_detect_input_files():
	config, config_meteo, ias_output_prefix, ias_output_version = {'mode': 'auto', 'path': 'auto'}, {'path': 'auto'}, 'auto', ''
	n_config, n_config_meteo, n_ias_output_prefix, n_ias_output_version = (
		auto_detect_input_files(config, config_meteo, ias_output_prefix, ias_output_version))
	assert True
