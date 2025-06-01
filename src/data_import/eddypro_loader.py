import logging
from copy import copy
import bglabutils.basic as bg


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
