'''
Draft far away from being finished
'''

import numpy as np
import pandas as pd

from helpers.py_helpers import invert_dict



def rapair_ias():
    # draft to fix ias_2 output of script to be same as ias_2 input
    # disabling all filters in the script should perform similary to this function

    cols = ['ch4_flux', 'co2_flux', 'H', 'LE', 'co2_strg', 'u*', 'VPD']
    cols_bio = ['RH_1_1_1', 'Ta_1_1_1']

    map = {"co2_flux": "FC_1_1_1", "qc_co2_flux": "FC_SSITC_TEST_1_1_1",
        "LE": "LE_1_1_1", "qc_LE": "LE_SSITC_TEST_1_1_1",
        "H": "H_1_1_1", "qc_H": "H_SSITC_TEST_1_1_1",
        "Tau": "TAU_1_1_1", "qc_Tau": "TAU_SSITC_TEST_1_1_1",
        "co2_strg": "SC_1_1_1", "co2_mole_fraction": "CO2_1_1_1",
        "h2o_mole_fraction": "H2O_1_1_1", "sonic_temperature": "T_SONIC_1_1_1",
        "Ta_1_1_1": "TA_1_1_1", "Pa_1_1_1": "PA_1_1_1",
        "Swin_1_1_1": "SW_IN_1_1_1", "Swout_1_1_1": "SW_OUT_1_1_1",
        "Lwin_1_1_1": "LW_IN_1_1_1", "Lwout_1_1_1": "LW_OUT_1_1_1",
        "Rn_1_1_1": "NETRAD_1_1_1", "MWS_1_1_1": "WS_1_1_1",
        "Ts_1_1_1": "TS_1_1_1", "Ts_2_1_1": "TS_2_1_1", "Ts_3_1_1": "TS_3_1_1",
        "Pswc_1_1_1": "SWC_1_1_1", "Pswc_2_1_1": "SWC_2_1_1", "Pswc_3_1_1": "SWC_3_1_1",
        "SHF_1_1_1": "G_1_1_1", "SHF_2_1_1": "G_2_1_1", "SHF_3_1_1": "G_3_1_1", "L": "MO_LENGTH_1_1_1",
        "(z-d)/L": "ZL_1_1_1",
        "x_peak": "FETCH_MAX_1_1_1", "x_70%": "FETCH_70_1_1_1", "x_90%": "FETCH_90_1_1_1",
        "ch4_flux": "FCH4_1_1_1", "qc_ch4_flux": "FCH4_SSITC_TEST_1_1_1", "ch4_mole_fraction": "CH4_1_1_1",

        "u*": "USTAR_1_1_1", "PPFD_1_1_1": "PPFD_IN_1_1_1", "Rh_1_1_1": "RH_1_1_1", "VPD": "VPD_1_1_1",
    }

    mapl = {k.lower(): v for k, v in  map.items()}
    cols_map = {c: mapl[c.lower()] for c in cols}
    cols_map_bio = {c: mapl[c.lower()] for c in cols_bio}
    ias: pd.DataFrame = pd.read_csv('tv_fy4_2015_v01.csv')

    src = pd.read_csv('IAS_only_Ckd_FO_2015.csv', skiprows=[0,2], encoding='utf8')
    src_bio = pd.read_csv('IAS_only_Ckd_biomet_2015.csv', skiprows=[1], encoding='utf8')
    # src_bio.loc[src_bio.index[-1] + 1] = src_bio.iloc[-1]
    src_bio = src_bio.shift(1)
    src_bio = src_bio.fillna(-9999)
    src = src.fillna(-9999)

    dlen = len(src)
    ias_cols = list(cols_map.values())
    ias_cols_bio = list(cols_map_bio.values())
    '''
    cmpr_ias = ias[ias_cols][5361: 5361 + dlen]
    cmpr_src = src[cols]
    cmpr_src.columns = ias_cols
    cmpr_src.index = cmpr_ias.index
    pd.DataFrame.compare(cmpr_ias, cmpr_src)
    '''

    new_src = src[cols].rename(columns=map)
    new_src.index = range(5361, 5361 + dlen)
    ias.loc[5361:5361 + dlen - 1, ias_cols] = new_src
    ias.loc[:, ias_cols_bio] = src_bio[cols_bio].rename(columns=map)
    ias.to_csv('tv_fy4_2015_v01_fix.csv', index=False, na_rep='-9999')



def test_import():
    # config_meteo['path'] = 'tv_fy4_2022_v01.xlsx'#'BiometFy4_2016.csv'#'BiometNCT_2011-22.csv'
    # draft: load same data from eddypro and ias and compare that mathing
    # TODO remove, extract to test
    data = data.rename(columns={'vpd_1_1_1': 'vpd'}).drop('ppfd_1_1_1', axis='columns')
    from helpers.pd_helpers import df_get_unique_cols, df_intersect_cols
    config['mode'] = 'EDDYPRO_1'
    config['path'] = ['IAS_only_Ckd_FO_2015.csv']
    data1, time1, biomet_columns1, data_freq1, config_meteo1 = load_eddypro_fulloutput(config, config_meteo)
    data1.columns = data1.columns.str.lower()
    data1 = data1.drop(['filename', 'date', 'time', 'timestamp_1', 'tmp_datetime', 'datetime_meteo'], axis=1)
    d, d1 = df_get_unique_cols(data[1:], data1)
    d1 = d1[d.columns]
    test = pd.DataFrame.compare(d[d1.columns], d1, align_axis='columns')


def test_conversion():
    # draft: load ias, convert to eddypro, convert to ias, save ias, check no damage happened
    pass