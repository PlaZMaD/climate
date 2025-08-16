COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES = {
    'CO2SS'.lower(): 'co2_signal_strength',
    # 'co2_signal_strength_7500_mean': 'co2_signal_strength',
    'co2_signal_strength.{1,}': 'co2_signal_strength',

    'CH4SS'.lower(): 'ch4_signal_strength',
    # 'ch4_signal_strength_7700_mean': 'ch4_signal_strength',
    'ch4_signal_strength.{1,}': 'ch4_signal_strength'
}

# TODO 1 QOA try to use import and export table
# can you say that 2-4 levels are done on unique set of cols, no duplicates or dupe cols from formats (biomet vs eddy vpd)?
COLS_CSF_TO_SCRIPT_U_RENAMES = {
    'FC': 'co2_flux', 'FC_QC': 'qc_co2_flux', 'LE_QC': 'qc_LE', 'H_QC': 'qc_H', 'TAU': 'Tau', 'TAU_QC': 'qc_Tau',
    'USTAR': 'u*', 'TA_1_1_1': 'Ta_1_1_1', 'RH_1_1_1': 'RH_1_1_1', 'T_SONIC': 'sonic_temperature',
    'WS_RSLT': 'MWS_1_1_1', 'CO2': 'co2_mole_fraction', 'CO2_sig_strgth_Min': 'co2_signal_strength_7500_mean',
    'FETCH_MAX': 'x_peak', 'FETCH_90': 'x_90%', 'FETCH_70': 'x_70%', 'MO_LENGTH_1_1_1': 'L', 'ZL_1_1_1': '(z-d)/L'
}

COLS_CSF_USED_NORENAME_IMPORT = [
    'LE', 'H',
    'co2_signal_strength', 'ch4_signal_strength' # not raw, check COLS_CSF_TO_SCRIPT_U_REGEX_RENAMES
]
COLS_CSF_UNUSED_NORENAME_IMPORT = [
    # TODO 1 QOA only warn for unknown cols, don't stop? import them or skip?
    'FC_mass', 'FC_samples', 'ET', 'ET_QC', 'ET_samples', 'LE', 'LE_samples', 'H', 'H_samples', 'Bowen_ratio', 'TSTAR',
    'TKE', 'e', 'e_sat', 'PA', 'PA_SIGMA', 'VPD', 'U', 'U_SIGMA', 'V', 'V_SIGMA', 'W', 'W_SIGMA', 'T_SONIC_SIGMA',
    'sonic_azimuth', 'WS', 'WD_SONIC', 'WD_SIGMA', 'WD', 'WS_MAX', 'CO2_SIGMA', 'CO2_mixratio', 'CO2_mixratio_SIGMA',
    'CO2_density', 'CO2_density_SIGMA', 'H2O', 'H2O_SIGMA', 'H2O_mixratio', 'H2O_mixratio_SIGMA', 'H2O_density',
    'H2O_density_SIGMA', 'H2O_sig_strgth_Min', 'sun_azimuth', 'sun_elevation', 'hour_angle', 'sun_declination',
    'air_mass_coeff', 'daytime', 'FETCH_80', 'FETCH_FILTER', 'FETCH_INTRST', 'FP_FETCH_INTRST', 'FTPRNT_EQUATION'
]
COLS_CSF_NORENAME_IMPORT = COLS_CSF_UNUSED_NORENAME_IMPORT + COLS_CSF_USED_NORENAME_IMPORT
COLS_CSF_UNUSED_NORENAME_IMPORT_DICT = {k: k.lower() for k in COLS_CSF_NORENAME_IMPORT}

COLS_CSF_IGNORED = [
    'RECORD'
]

# TODO 2 test handling unit/str conversions between import and export if name is same
COLS_CSF_TIME = ['TIMESTAMP']

# COLS_SCRIPT_TO_CSF_RENAMES = {k.lower(): v for k, v in COLS_CSF_TO_SCRIPT_E_RENAMES.items()}

COLS_CSF_IMPORT_MAP = COLS_CSF_UNUSED_NORENAME_IMPORT_DICT | COLS_CSF_TO_SCRIPT_U_RENAMES

COLS_CSF_KNOWN = list(COLS_CSF_IMPORT_MAP.keys()) + COLS_CSF_TIME + COLS_CSF_IGNORED

CSF_HEADER_DETECTION_COLS = COLS_CSF_KNOWN
