BIOMET_HEADER_DETECTION_COLS = [
    # just a sample, some cols may be missing
    'TIMESTAMP_1', 'Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1', 'Lwout_1_1_1',
    'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1', 
    # added in 1.0.5
    'PPFD_1_1_1', 'Ts_1_1_1'
]

BIOMET_2_HEADER_DETECTION_COLS = [
    'date', 'time', 'DOY', 'CHK__1_1_1', 'DAQM_T_1_1_1', 'VIN_1_1_1', 'PPFD_1_1_1', 'P_RAIN_1_1_1', 
    'RH_1_1_1', 'RN_1_1_1', 'SHF_1_1_1', 'SHF_2_1_1', 'SHF_3_1_1', 'SWC_1_1_1', 'SWC_2_1_1', 
    'TA_1_1_1', 'TS_1_1_1', 'TS_2_1_1', 'TS_3_1_1',
    # added in 1.0.5
    'LWIN_1_1_1', 'LWOUT_1_1_1', 'SWOUT_1_1_1', 'SWIN_1_1_1', 'SHFSENS1', 'SHFSENS3', 'SHFSENS2', 'LOGGERTEMP', 'LOGGERPWR',
    'TCNR4_C_1_1_1', 'Relay_1_1_1', 'Relay_2_1_1', 'DRM_V_BATTERY_1_1_1', 'DRM_POWER_STATUS_1_1_1', 'DRM_V_MAIN_1_1_1', 'SENS_1_1_1', 'SENS_2_1_1', 'SENS_3_1_1',
    'SHFSENS_1_1_1', 'SHFSENS_2_1_1', 'SHFSENS_3_1_1'
]

BIOMET_USED_COLS = [
    'Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1', 'Lwout_1_1_1',
    'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1'
]

BIOMET_USED_COLS_LOWER = [c.lower() for c in BIOMET_USED_COLS]