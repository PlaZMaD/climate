'''
Unused draft for ias reading far away from being finished
'''
import re

import pandas as pd

import src.helpers.os_helpers  # noqa: F401
from src.helpers.io_helpers import find_in_files


def repair_ias():
    # draft to fix ias_2 output of script to be same as ias_2 input
    # disabling all filters in the script should perform similary to this function
    
    cols = ['ch4_flux', 'co2_flux', 'H', 'LE', 'co2_strg', 'u*', 'VPD']
    cols_bio = ['RH_1_1_1', 'Ta_1_1_1']
    
    map_fo_to_ias = {'u*': 'USTAR_1_1_1', 'PPFD_1_1_1': 'PPFD_IN_1_1_1', 'Rh_1_1_1': 'RH_1_1_1', 'VPD': 'VPD_1_1_1'}
    
    mapl = {k.lower(): v for k, v in map.items()}
    cols_map = {c: mapl[c.lower()] for c in cols}
    cols_map_bio = {c: mapl[c.lower()] for c in cols_bio}
    ias: pd.DataFrame = pd.read_csv('tv_fy4_2015_v01.csv')
    
    src = pd.read_csv('IAS_only_Ckd_FO_2015.csv', skiprows=[0, 2], encoding='utf8')
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


def load_via_bglabutils(fpath):
    def my_datetime_converter(x):
        return pd.to_datetime(x['TIMESTAMP_START'], format='%Y%m%d%H%M')
    
    config = {
        'debug': False,
        '-9999_to_nan': True,
        'repair_time': False,
        'time': {
            'column_name': 'datetime',
            'converter': my_datetime_converter
        },
        'path': [fpath]
    }
    
    data, time = bg.load_df(config)
    return data[next(iter(data))]


def check_with_bglabutils(fpath, data):
    data_bgl = load_via_bglabutils(fpath).drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis='columns')
    data_cmpr = data[1:-1]
    df1, df2 = df_get_unique_cols(data_cmpr, data_bgl)
    
    if df1.columns.size + df2.columns.size > 0:
        raise Exception(f'bglabutils.load_df loads different ias table. df1: {df1.columns} df2: {df2.columns}')


def test_import():
    # config_meteo['path'] = 'tv_fy4_2022_v01.xlsx'#'BiometFy4_2016.csv'#'BiometNCT_2011-22.csv'
    # draft: load same data from eddypro and ias and compare that mathing
    data = data.rename(columns={'vpd_1_1_1': 'vpd'}).drop('ppfd_1_1_1', axis='columns')
    from src.helpers.pd_helpers import df_get_unique_cols
    config['mode'] = 'EDDYPRO_1'
    config['path'] = ['IAS_only_Ckd_FO_2015.csv']
    data1, time1, biomet_columns1, data_freq1, config_meteo1 = load_eddypro_fulloutput(config, config_meteo)
    data1.columns = data1.columns.str.lower()
    data1 = data1.drop(['filename', 'date', 'time', 'timestamp_1', 'tmp_datetime', 'datetime_meteo'], axis=1)
    d, d1 = df_get_unique_cols(data[1:], data1)
    d1 = d1[d.columns]
    test = pd.DataFrame.compare(d[d1.columns], d1, align_axis='columns')
    
    check_with_bglabutils(fpath, df)


def test_conversion():
    # draft: load ias, convert to eddypro, convert to ias, save ias, check no damage happened
    pass


def test_tmp_cols_mathcing():
    from src.data_io.ias_io import COLS_IAS_IMPORT_MAP, COLS_IAS_TIME, COLS_IAS_UNUSED_NORENAME_IMPORT
    ias_import_cols = list(COLS_IAS_IMPORT_MAP.keys()) + COLS_IAS_TIME + COLS_IAS_UNUSED_NORENAME_IMPORT
    from src.data_io.ias_error_check import known_columns
    
    def first(s: str):
        if s in COLS_IAS_TIME:
            return s
        m = re.match('(.*)_\d_\d_\d', s)
        return m[1]
    
    ias_import_col_placeholders = [first(c) for c in ias_import_cols]
    
    # ensure no spaces
    bugs = [c for c in known_columns if ' ' in c]
    assert len(bugs) == 0
    
    unpoc_col_placeholders = {known_columns} - {ias_import_col_placeholders}
    # unpoc_cols = [c + '_' for c in unpoc_col_placeholders]
    
    # matches_ = {uc: find_in_files('.', '^(?!.*ias_error_check).*\.(py|R|r)$', uc) for uc in unpoc_cols}
    matches = {uc: find_in_files('.', '^(?!.*ias_error_check).*\.(py|R|r)$', uc) for uc in unpoc_col_placeholders}
    
    pass
