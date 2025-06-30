# this file is separate with intention to possibly move to colnames table later

# biomet cols are required not only in eddypro load, but also, for example, in ias check;
# probably biomet should be reworked to just a list of special cols, but as is for now
BIOMET_HEADER_DETECTION_COLS = [
	# just a sample, some cols may be missing
	'TIMESTAMP_1', 'Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1', 'Lwout_1_1_1',
	'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1'
]
EDDYPRO_HEADER_DETECTION_COLS = [
	# just a sample, some cols may be missing
	'filename', 'date', 'time', 'DOY', 'daytime', 'file_records', 'used_records', 'Tau',
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
	'dew_point_mean', 'co2_signal_strength_7500_mean'
]