import logging

import numpy as np
import pandas as pd

from bglabutils import basic as bg, filters as bf
from src.plots import get_column_filter


def min_max_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    for col, limits in config.items():
        if col not in data.columns:
            print(f"No column with name {col}, skipping...")
            continue
        filter = get_column_filter(data, filters_db, col)

        if len(filter) == 0:
            filter = [1] * len(data.index)

        data[f"{col}_minmaxfilter"] = filter

        if col not in ['rh_1_1_1', 'swin_1_1_1', 'ppfd_1_1_1', 'swin_1_1_1']:
            data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
        else:
            if col == 'rh_1_1_1':
                data[col] = data[col].clip(upper=limits[1])
                data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
            else:
                data[col] = data[col].clip(lower=limits[0])
                if col not in ['swin_1_1_1']:
                    data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
                else:
                    data.loc[data.query(f"{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0

        if f"{col}_minmaxfilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_minmaxfilter")
        else:
            print("filter already exist but will be overwritten")
    logging.info(f"min_max_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def qc_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, limits in config.items():
        if col not in data.columns:
            print(f"No column with name {col}, skipping...")
            continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        data[f"{col}_qcfilter"] = filter
        if f"qc_{col}" not in data.columns and col != 'nee':
            print(f"No qc_{col} in data")
            continue
        if col != 'nee':
            data.loc[data[f"qc_{col}"] > config[col], f"{col}_qcfilter"] = 0
        else:
            data.loc[data[f"qc_co2_flux"] > config['co2_flux'], f"nee_qcfilter"] = 0

        if f"{col}_qcfilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_qcfilter")
        else:
            print("filter already exist but will be overwritten")
    logging.info(f"qc_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def std_window_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    for col, lconfig in config.items():
        sigmas = lconfig['sigmas']
        window_size = lconfig['window']
        min_periods = lconfig['min_periods']  # (window_size//2-1)
        points_per_day = int(pd.Timedelta('24h') / data_in.index.freq)  # lconfig['points_per_day']
        if col not in data.columns:
            print(f"No column with name {col}, skipping...")
            continue
        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        data[f"{col}_stdwindowfilter"] = filter
        data['tmp_col'] = data[col]
        data.loc[~filter.astype(bool), 'tmp_col'] = np.nan
        rolling_mean = bg.calc_rolling(data['tmp_col'], rolling_window=window_size, step=points_per_day,
                                       min_periods=min_periods)
        residuals = data['tmp_col'] - rolling_mean
        rolling_sigma = residuals.rolling(window=window_size * points_per_day, center=True, closed='both',
                                          min_periods=window_size * points_per_day // 2).std()
        data = data.drop(columns='tmp_col')
        # print(rolling_sigma, rolling_mean)
        upper_bound = rolling_mean + rolling_sigma * sigmas
        lower_bound = rolling_mean - rolling_sigma * sigmas
        upper_inds = upper_bound[upper_bound < data[col]].index
        lower_inds = lower_bound[lower_bound > data[col]].index
        data.loc[upper_inds, f"{col}_stdwindowfilter"] = 0
        data.loc[lower_inds, f"{col}_stdwindowfilter"] = 0
        # # print(len(lower_inds), len(upper_inds))
        # plt.plot(rolling_mean)
        # plt.title(col)
        # plt.show()

        if f"{col}_stdwindowfilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_stdwindowfilter")
        else:
            print("filter already exist but will be overwritten")
    logging.info(f"std_window_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_filter(
        data_in, filters_db_in, config
        # , file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
):
    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'h', 'le', 'ch4_flux']:

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_physFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_physFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_physFilter"] = filter

    if 'co2_signal_strength' in data.columns and 'CO2SS_min' in config.keys():
        data.loc[data['co2_signal_strength'] < config['CO2SS_min'], 'co2_flux_physFilter'] = 0
    else:
        print("No co2_signal_strength found")

    if 'ch4_signal_strength' in data.columns and 'CH4SS_min' in config.keys():
        data.loc[data['ch4_signal_strength'] < config['CH4SS_min'], 'ch4_flux_physFilter'] = 0
    else:
        print("No ch4_signal_strength found")

    if 'p_rain_limit' in config.keys():
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'co2_flux_physFilter'] = 0
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'h_physFilter'] = 0
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'le_physFilter'] = 0
        if 'rain_forward_flag' in config:
            rain_forward_flag = config['rain_forward_flag']
            for i in range(rain_forward_flag):
                ind = data.loc[data['p_rain_1_1_1'] > config['p_rain_limit']].index.shift(i, freq=file_freq)
                data.loc[ind, 'co2_flux_physFilter'] = 0
                data.loc[ind, 'h_physFilter'] = 0
                data.loc[ind, 'le_physFilter'] = 0

    if 'RH_max' in config.keys():
        RH_max = config['RH_max']
        data.loc[data['rh_1_1_1'] > RH_max, 'co2_flux_physFilter'] = 0
        data.loc[data['rh_1_1_1'] > RH_max, 'le_physFilter'] = 0
    logging.info(f"meteorological_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_rh_filter(
        data_in, filters_db_in, config
        # , file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
):
    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'le', 'nee']:

        if col not in data.columns:
            print(f"no {col}")
            continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_rhFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_rhFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_rhFilter"] = filter

    if 'RH_max' in config.keys() and 'rh_1_1_1' in data.columns:
        RH_max = config['RH_max']
        data.loc[data['rh_1_1_1'] > RH_max, 'co2_flux_rhFilter'] = 0
        if 'nee' in data.columns:
            data.loc[data['rh_1_1_1'] > RH_max, 'nee_rhFilter'] = 0
        data.loc[data['rh_1_1_1'] > RH_max, 'le_rhFilter'] = 0
    logging.info(f"meteorological_rh_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_night_filter(
        data_in, filters_db_in, config
        # , file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
):
    if "swin_1_1_1" not in data_in.columns:
        logging.info(f"meteorological_night_filter not applied, no SWIN found  \n")
        return data_in, filters_db_in

    if not config['use_night_filter']:
        logging.info(f"Night filter dissabled.")
        return data_in, filters_db_in

    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    col_of_interest = ["h", 'le', 'nee', 'co2_flux']

    for col in col_of_interest:
        if col not in data.columns:
            print(f"no {col} column")
            continue
        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_nightFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_nightFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_nightFilter"] = filter

    if "nee" in data.columns:
        data_night_index = data.query(f"swin_1_1_1<10&nee<{config['night_nee_min']}").index
        data.loc[data_night_index, f"nee_nightFilter"] = 0

    if "co2_flux" in data.columns:
        data_night_index = data.query("swin_1_1_1<10&co2_flux<0").index
        data.loc[data_night_index, f"co2_flux_nightFilter"] = 0

    data_night_index = data.query(
        f"(h<{config['night_h_limits'][0]}|h>{config['night_h_limits'][1]})&swin_1_1_1<10"
    ).index
    data.loc[data_night_index, f"h_nightFilter"] = 0

    data_night_index = data.query(
        f"(h<{config['night_le_limits'][0]}|h>{config['night_le_limits'][1]})&swin_1_1_1<10"
    ).index
    data.loc[data_night_index, f"le_nightFilter"] = 0

    # if 'nee' in data.columns:
    #   data_night_index = data.query(f'nee>{config["day_nee_max"]}&swin_1_1_1>=10').index
    #   data.loc[data_night_index, f"nee_nightFilter"] = 0
    logging.info(f"meteorological_night_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_day_filter(data_in, filters_db_in, config):  # , file_freq='30T'):
    if "swin_1_1_1" not in data_in.columns:
        logging.info(f"meteorological_day_filter not applied, no SWIN found  \n")
        return data_in, filters_db_in

    if not config['use_day_filter']:
        logging.info(f"Day filter dissabled.")
        return data_in, filters_db_in

    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    col_of_interest = ['nee']

    for col in col_of_interest:
        if col not in data.columns:
            print(f"no {col} column")
            continue
        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_dayFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_dayFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_dayFilter"] = filter

    if 'nee' in data.columns:
        data_day_index = data.query(f'nee>{config["day_nee_max"]}&swin_1_1_1>={config["day_swin_limit"]}').index
        data.loc[data_day_index, f"nee_dayFilter"] = 0
    logging.info(f"meteorological_day_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_co2ss_filter(
        data_in, filters_db_in, config
        # , file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
):
    file_freq = data_in.index.freq
    if 'CO2SS_min' not in config.keys():
        return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'nee']:

        if col not in data.columns:
            print(f"no {col} column")
            continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_co2ssFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_co2ssFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_co2ssFilter"] = filter

        if 'co2_signal_strength' in data.columns:
            data.loc[data['co2_signal_strength'] < config['CO2SS_min'], f'{col}_co2ssFilter'] = 0

        else:
            print("No co2_signal_strength found")
    logging.info(f"meteorological_co2ss_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_ch4ss_filter(
        data_in, filters_db_in, config
        # , file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
):
    file_freq = data_in.index.freq
    if 'CH4SS_min' not in config.keys():
        return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["ch4_flux"]:

        if col not in data.columns:
            print(f"no {col} column")
            continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_ch4ssFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_ch4ssFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_ch4ssFilter"] = filter

    if 'ch4_signal_strength' in data.columns:
        data.loc[data['ch4_signal_strength'] < config['CH4SS_min'], 'ch4_flux_ch4ssFilter'] = 0
    else:
        print("No ch4_signal_strength found")
    logging.info(f"meteorological_coh4ss_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_rain_filter(
        data_in, filters_db_in, config
        # , file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
):
    file_freq = data_in.index.freq
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'h', 'le', 'nee', "ch4_flux"]:
        if col not in data.columns:
            print(f"no {col}")
            continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_rainFilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_rainFilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_rainFilter"] = filter

    if 'p_rain_limit' in config.keys() and 'p_rain_1_1_1' in data.columns:
        if 'co2_flux' in data.columns:
            data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'co2_flux_rainFilter'] = 0
        if 'h' in data.columns:
            data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'h_rainFilter'] = 0
        if 'le' in data.columns:
            data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'le_rainFilter'] = 0
        if 'nee' in data.columns:
            data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'nee_rainFilter'] = 0
        if 'ch4_flux' in data.columns:
            data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'ch4_flux_rainFilter'] = 0

        if 'rain_forward_flag' in config:
            rain_forward_flag = config['rain_forward_flag']
            for i in range(rain_forward_flag):
                ind = data.loc[data['p_rain_1_1_1'] > config['p_rain_limit']].index.shift(i, freq=file_freq)
                ind = ind.intersection(data.index)
                if len(ind) == 0:
                    continue
                if 'nee' in data.columns:
                    data.loc[ind, 'nee_rainFilter'] = 0
                if 'ch4_flux' in data.columns:
                    data.loc[ind, 'ch4_flux_rainFilter'] = 0
                if 'co2_flux' in data.columns:
                    data.loc[ind, 'co2_flux_rainFilter'] = 0
                if 'h' in data.columns:
                    data.loc[ind, 'h_rainFilter'] = 0
                if 'le' in data.columns:
                    data.loc[ind, 'le_rainFilter'] = 0

    logging.info(f"meteorological_rain_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def quantile_filter(data_in, filters_db_in, config):
    if len(config) == 0:
        return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, limits in config.items():
        limit_down, limit_up = limits
        if col not in data.columns:
            print(f"No column with name {col}, skipping...")
            continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_quantilefilter" not in filters_db[col]:
            filters_db[col].append(f"{col}_quantilefilter")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_quantilefilter"] = filter
        up_limit = data.loc[data[f'{col}_quantilefilter'] == 1, col].quantile(limit_up)
        down_limit = data.loc[data[f'{col}_quantilefilter'] == 1, col].quantile(limit_down)
        f_inds = data.query(f"{col}_quantilefilter==1").index
        print("Quantile filter cut values: ", down_limit, up_limit)
        # data.loc[f_inds, f'{col}_quantilefilter'] = ((data.loc[f_inds, col] <= up_limit) & (data.loc[f_inds, col] >= down_limit)).astype(int)
        data.loc[data[col] > up_limit, f'{col}_quantilefilter'] = 0
        data.loc[data[col] < down_limit, f'{col}_quantilefilter'] = 0

        # print(col, (data.loc[f_inds, col] < down_limit).sum(), (data.loc[f_inds, col] > up_limit).sum(), len(data.loc[f_inds, col].index), ((data.loc[f_inds, col] < up_limit) & (data.loc[f_inds, col] > down_limit)).astype(int).sum())
        # print(filter.sum(), data[f'{col}_quantilefilter'].sum(), filter.sum() - data[f'{col}_quantilefilter'].sum())
    logging.info(f"quantile_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def mad_hampel_filter(data_in, filters_db_in, config):
    # TODO 2 why vpd_1_1_1 madhampel is different in single line 5299 for Lga 2023
    #  0.9.4 colab vs 0.9.5 local? seems also occured previously E: send data
    if len(config) == 0:
        return data_in, filters_db_in
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, lconfig in config.items():
        if col not in data.columns:
            print(f"No column with name {col}, skipping...")
            continue

        hampel_window = lconfig['hampel_window']
        z = lconfig['z']
        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
            filter = [1] * len(data.index)

        if f"{col}_madhampel" not in filters_db[col]:
            filters_db[col].append(f"{col}_madhampel")
        else:
            print("filter already exist but will be overwritten")

        data[f"{col}_madhampel"] = filter

        # hampel_window = 20
        print(f"Processing {col}")
        outdata = bf.apply_hampel_after_mad(data.loc[data[f'{col}_madhampel'] == 1, :], [col], z=z,
                                            window_size=hampel_window)
        data.loc[data[f'{col}_madhampel'] == 1, f'{col}_madhampel'] = outdata[f'{col}_filtered'].astype(int)
        data[f"{col}_madhampel"] = data[f"{col}_madhampel"].astype(int)

    logging.info(f"mad_hampel_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def manual_filter(data_in, filters_db_in, col_name, man_range, value, config):
    # TODO 1 function agrs seems wre duplicated, test man_range works same way

    data = data_in.copy()
    filters_db = filters_db_in.copy()
    filter = get_column_filter(data, filters_db, col_name)
    if len(filter) == 0:
        filter = [1] * len(data.index)
    data[f"{col_name}_manualFilter"] = filter
    # if range not in data.index:
    #   print('WARNING date range is not in index! Nothing is changed!')
    #   return data, filters_db
    try:
        man_start, man_stop = man_range

        dt_start = pd.to_datetime(man_start, dayfirst=True)
        dt_stop = pd.to_datetime(man_stop, dayfirst=True)
        if dt_start > dt_stop:
            raise KeyError("Check your dates")

        if dt_start < data.index[0] and (data.index[-1] >= dt_stop > data.index[0]):
            dt_start = data.index[0]
            print(f"Actual manual start: {dt_start}")

        if dt_stop > data.index[-1] and (data.index[0] <= dt_start < data.index[-1]):
            dt_stop = data.index[-1]
            print(f"Actual manual stop: {dt_start}")

        range_ = pd.date_range(dt_start, dt_stop, freq=data.index.freq)
        data.loc[range_, f"{col_name}_manualFilter"] = value
    except KeyError:
        print("ERROR! Check the date range!")
        return data, filters_db

    if f"{col_name}_manualFilter" not in filters_db[col_name]:
        filters_db[col_name].append(f"{col_name}_manualFilter")
    else:
        print("filter already exist but will be overwritten")
    logging.info(f"manual_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def winter_filter(data_in, filters_db_in, config, date_ranges):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    if ('winter_nee_limits' not in config.keys()) and ('winter_ch4_flux_limits' not in config.keys()):
        return data, filters_db

    printed_flag_start = False
    printed_flag_stop = False

    if 'winter_nee_limits' in config.keys():
        for col in ['nee', 'co2_flux']:
            if col not in data.columns:
                print(f"No column with name {col}, skipping...")
                continue

            filter = get_column_filter(data, filters_db, col)
            if len(filter) == 0:
                filter = [1] * len(data.index)
            data[f"{col}_winterFilter"] = filter
            try:
                for start, stop in date_ranges:
                    dt_start = pd.to_datetime(start, dayfirst=True)
                    dt_stop = pd.to_datetime(stop, dayfirst=True)

                    if dt_start > dt_stop:
                        raise KeyError("Check your dates, start > stop")

                    if dt_stop <= data.index[0] or dt_start >= data.index[-1]:
                        print(f'Warning, empty range {dt_start} - {dt_stop}!')
                        continue

                    if dt_start < data.index[0] and (dt_stop <= data.index[-1] and dt_stop > data.index[0]):
                        dt_start = data.index[0]
                        if not printed_flag_start:
                            print(f"Actual winter start: {dt_start}")
                            printed_flag_start = True

                    if dt_stop > data.index[-1] and (dt_start >= data.index[0] and dt_start < data.index[-1]):
                        dt_stop = data.index[-1]
                        if not printed_flag_stop:
                            print(f"Actual winter stop: {dt_start}")
                            printed_flag_stop = True

                    range = pd.date_range(dt_start, dt_stop, freq=data.index.freq)

                    inds_down = data.loc[range].query(f"{col}<{config['winter_nee_limits'][0]}").index
                    inds_up = data.loc[range].query(f"{col}>{config['winter_nee_limits'][1]}").index
                    data.loc[inds_up, f"{col}_winterFilter"] = 0
                    data.loc[inds_down, f"{col}_winterFilter"] = 0
            except KeyError:
                print("ERROR! Check the date range!")
                return data, filters_db

            if f"{col}_winterFilter" not in filters_db[col]:
                filters_db[col].append(f"{col}_winterFilter")
            else:
                print("filter already exist but will be overwritten")

    if 'winter_ch4_flux_limits' in config.keys():
        for col in ['ch4_flux']:
            if col not in data.columns:
                print(f"No column with name {col}, skipping...")
                continue

            filter = get_column_filter(data, filters_db, col)
            if len(filter) == 0:
                filter = [1] * len(data.index)
            data[f"{col}_winterFilter"] = filter
            try:
                for start, stop in date_ranges:

                    dt_start = pd.to_datetime(start, dayfirst=True)
                    dt_stop = pd.to_datetime(stop, dayfirst=True)

                    if dt_start > dt_stop:
                        raise KeyError("Check your dates, start > stop")

                    if dt_stop <= data.index[0] or dt_start >= data.index[-1]:
                        print(f'Warning, empty range {dt_start} - {dt_stop}!')
                        continue

                    if dt_start < data.index[0] and (dt_stop <= data.index[-1] and dt_stop > data.index[0]):
                        dt_start = data.index[0]
                        if not printed_flag_start:
                            print(f"Actual winter start: {dt_start}")
                            printed_flag_start = True

                    if dt_stop > data.index[-1] and (dt_start >= data.index[0] and dt_start < data.index[-1]):
                        dt_stop = data.index[-1]
                        if not printed_flag_stop:
                            print(f"Actual winter stop: {dt_start}")
                            printed_flag_stop = True

                    range = pd.date_range(dt_start, dt_stop, freq=data.index.freq)

                    inds_down = data.loc[range].query(f"{col}<{config['winter_ch4_flux_limits'][0]}").index
                    inds_up = data.loc[range].query(f"{col}>{config['winter_ch4_flux_limits'][1]}").index
                    data.loc[inds_up, f"{col}_winterFilter"] = 0
                    data.loc[inds_down, f"{col}_winterFilter"] = 0
            except KeyError:
                print("ERROR! Check the date range!")
                return data, filters_db

            if f"{col}_winterFilter" not in filters_db[col]:
                filters_db[col].append(f"{col}_winterFilter")
            else:
                print("filter already exist but will be overwritten")

    logging.info(f"winter_filter applied with the next config: \n {config}  \n Date range: {date_ranges} \n")
    return data, filters_db
