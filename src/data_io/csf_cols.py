''' original list
'FC', 'FC_mass', 'FC_QC', 'FC_samples', 'ET', 'ET_QC', 'ET_samples',
'LE', 'LE_QC', 'LE_samples', 'H', 'H_QC', 'H_samples', 'Bowen_ratio',
'TAU', 'TAU_QC', 'USTAR', 'TSTAR', 'TKE', 
'e', 'e_sat', 'PA', 'PA_SIGMA', 'VPD',
'U', 'U_SIGMA', 'V', 'V_SIGMA', 'W', 'W_SIGMA', 'T_SONIC', 'T_SONIC_SIGMA', 'sonic_azimuth',
'WS', 'WS_RSLT', 'WD_SONIC', 'WD_SIGMA', 'WD', 'WS_MAX',
'CO2', 'CO2_SIGMA', 'CO2_mixratio', 'CO2_mixratio_SIGMA', 'CO2_density', 'CO2_density_SIGMA',
'H2O', 'H2O_SIGMA', 'H2O_mixratio', 'H2O_mixratio_SIGMA', 'H2O_density', 'H2O_density_SIGMA',
'CO2_sig_strgth_Min', 'H2O_sig_strgth_Min', 'sun_azimuth', 'sun_elevation', 'hour_angle',
'sun_declination', 'air_mass_coeff', 'daytime', 'FETCH_MAX', 'FETCH_90', 'FETCH_80', 'FETCH_70',
'FETCH_FILTER', 'FETCH_INTRST', 'FP_FETCH_INTRST', 'FTPRNT_EQUATION'
 '''

# TODO 1 QOA WRONG
TMP_ALL_LIST = [
    'FC', 'FC_mass', 'FC_QC', 'FC_samples', 'ET', 'ET_QC', 'ET_samples',
    'LE', 'LE_QC', 'LE_samples', 'H', 'H_QC', 'H_samples', 'Bowen_ratio',
    'TAU', 'TAU_QC', 'USTAR', 'TSTAR', 'TKE',
    'e', 'e_sat', 'PA', 'PA_SIGMA', 'VPD',
    'U', 'U_SIGMA', 'V', 'V_SIGMA', 'W', 'W_SIGMA', 'T_SONIC', 'T_SONIC_SIGMA', 'sonic_azimuth',
    'WS', 'WS_RSLT', 'WD_SONIC', 'WD_SIGMA', 'WD', 'WS_MAX',
    'CO2', 'CO2_SIGMA', 'CO2_mixratio', 'CO2_mixratio_SIGMA', 'CO2_density', 'CO2_density_SIGMA',
    'H2O', 'H2O_SIGMA', 'H2O_mixratio', 'H2O_mixratio_SIGMA', 'H2O_density', 'H2O_density_SIGMA',
    'CO2_sig_strgth_Min', 'H2O_sig_strgth_Min', 'sun_azimuth', 'sun_elevation', 'hour_angle',
    'sun_declination', 'air_mass_coeff', 'daytime', 'FETCH_MAX', 'FETCH_90', 'FETCH_80', 'FETCH_70',
    'FETCH_FILTER', 'FETCH_INTRST', 'FP_FETCH_INTRST', 'FTPRNT_EQUATION']

COLS_CSF_IGNORED = [
    'RECORD'
]

COLS_CSF_USED_NORENAME_IMPORT = [
    *TMP_ALL_LIST,
    'TA_1_1_1',
    'RH_1_1_1',
]
COLS_CSF_UNUSED_NORENAME_IMPORT = [
    'TA_SIGMA_1_1_1',
    'T_DP_1_1_1',
]
COLS_CSF_NORENAME_IMPORT = COLS_CSF_UNUSED_NORENAME_IMPORT + COLS_CSF_USED_NORENAME_IMPORT
COLS_CSF_UNUSED_NORENAME_IMPORT_DICT = {k: k.lower() for k in COLS_CSF_NORENAME_IMPORT}

# TODO 2 handling unit/str conversions between import and export if name is same?
COLS_CSF_TIME = ['TIMESTAMP']

# COLS_SCRIPT_TO_CSF_RENAMES = {k.lower(): v for k, v in COLS_CSF_TO_SCRIPT_E_RENAMES.items()}
COLS_CSF_IMPORT_MAP = COLS_CSF_UNUSED_NORENAME_IMPORT_DICT

COLS_CSF_KNOWN = list(COLS_CSF_IMPORT_MAP.keys()) + COLS_CSF_TIME + COLS_CSF_IGNORED
CSF_HEADER_DETECTION_COLS = COLS_CSF_KNOWN
