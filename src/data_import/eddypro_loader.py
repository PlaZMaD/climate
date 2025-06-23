import logging
from copy import copy
import bglabutils.basic as bg

BIOMET_HEADER_DETECTION_COLS = ['TIMESTAMP_1', 'Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1', 'Lwout_1_1_1',
                                'Swin_1_1_1', 'Swout_1_1_1',
                                'P_1_1_1']
EDDYPRO_HEADER_DETECTION_COLS = ['filename', 'date', 'time', 'DOY', 'daytime', 'file_records', 'used_records', 'Tau',
                                 'qc_Tau', 'H', 'qc_H', 'LE', 'qc_LE', 'co2_flux', 'qc_co2_flux', 'h2o_flux',
                                 'qc_h2o_flux', 'H_strg', 'LE_strg', 'co2_strg', 'h2o_strg', 'co2_v-adv', 'h2o_v-adv',
                                 'co2_molar_density', 'co2_mole_fraction', 'co2_mixing_ratio', 'co2_time_lag',
                                 'co2_def_timelag', 'h2o_molar_density', 'h2o_mole_fraction', 'h2o_mixing_ratio',
                                 'h2o_time_lag', 'h2o_def_timelag', 'sonic_temperature', 'air_temperature',
                                 'air_pressure', 'air_density', 'air_heat_capacity', 'air_molar_volume', 'ET',
                                 'water_vapor_density', 'e', 'es', 'specific_humidity', 'RH', 'VPD', 'Tdew', 'u_unrot',
                                 'v_unrot', 'w_unrot', 'u_rot', 'v_rot', 'w_rot', 'wind_speed', 'max_wind_speed',
                                 'wind_dir', 'yaw', 'pitch', 'roll', 'u*', 'TKE', 'L', '(z-d)/L', 'bowen_ratio', 'T*',
                                 'model', 'x_peak', 'x_offset', 'x_10%', 'x_30%', 'x_50%', 'x_70%', 'x_90%', 'un_Tau',
                                 'Tau_scf', 'un_H', 'H_scf', 'un_LE', 'LE_scf', 'un_co2_flux', 'co2_scf', 'un_h2o_flux',
                                 'h2o_scf', 'spikes_hf', 'amplitude_resolution_hf', 'drop_out_hf', 'absolute_limits_hf',
                                 'skewness_kurtosis_hf', 'skewness_kurtosis_sf', 'discontinuities_hf',
                                 'discontinuities_sf', 'timelag_hf', 'timelag_sf', 'attack_angle_hf',
                                 'non_steady_wind_hf', 'u_spikes', 'v_spikes', 'w_spikes', 'ts_spikes', 'co2_spikes',
                                 'h2o_spikes', 'chopper_LI-7500', 'detector_LI-7500', 'pll_LI-7500', 'sync_LI-7500',
                                 'mean_value_RSSI_LI-7500', 'u_var', 'v_var', 'w_var', 'ts_var', 'co2_var', 'h2o_var',
                                 'w/ts_cov', 'w/co2_cov', 'w/h2o_cov', 'vin_sf_mean', 'co2_mean', 'h2o_mean',
                                 'dew_point_mean', 'co2_signal_strength_7500_mean']


def load_biomet(config_meteo, data_freq):
	print("Проверяем корректность временных меток. Убираем повторы, дополняем пропуски. "
	      "На случай загрузки нескольких файлов. При загрузке одного делается автоматически.")

	data_meteo, time_meteo = bg.load_df(config_meteo)
	data_meteo = data_meteo[next(iter(data_meteo))]  # т.к. изначально у нас словарь

	meteo_freq = data_meteo.index.freq
	print("Диапазон времени метео: ", data_meteo.index[[0, -1]])
	logging.info(f"MeteoData loaded from {config_meteo['path']}")
	logging.info("Time range for meteo: " + " - ".join(data_meteo.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

	if data_freq != meteo_freq:
		print("Resampling meteo data")
		logging.info(f"Resampling meteo data")
		data_meteo = data_meteo.asfreq(data_freq)

	return data_meteo


def load_eddypro_fulloutput(config, config_meteo):
	# load of eddypro = full_output, optionally with biomet

	data, time = bg.load_df(config)
	data = data[next(iter(data))]  # т.к. изначально у нас словарь
	data_freq = data.index.freq

	print("Диапазон времени full_output: ", data.index[[0, -1]])
	logging.info(f"Data loaded from {config['path']}")
	logging.info("Time range for full_output: " + " - ".join(data.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

	if config_meteo['use_biomet']:
		data_meteo = load_biomet(config_meteo, data_freq)

	print("Колонки в FullOutput \n", data.columns.to_list())
	if config_meteo['use_biomet']:
		print("Колонки в метео \n", data_meteo.columns.to_list())

	# Сливаем в один DataFrame.
	if config_meteo['use_biomet']:
		data = data.join(data_meteo, how='outer', rsuffix='_meteo')
		data[time] = data.index
		data = bg.repair_time(data, time)
		if data[data_meteo.columns[-1]].isna().sum() == len(data.index):
			print("Bad meteo data range, skipping! Setting config_meteo ['use_biomet']=False")
			config_meteo['use_biomet'] = False

	biomet_columns = []
	if config_meteo['use_biomet']:
		biomet_columns = data_meteo.columns.str.lower()

	return data, time, biomet_columns, data_freq, config_meteo
