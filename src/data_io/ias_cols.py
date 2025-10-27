'''
current renames EDDYPRO? -> SCRIPT to check
'u*' -> u_star"
'ppfd_in_1_1_1' -> ppfd_1_1_1"
'sw_in_1_1_1' -> swin_1_1_1"
'''

# which cols used in the script and unused?
# currently 4 column names variations are possible:
# IAS file, EddyPro file, script import, export (after all the processing)

# V: import all possible, even if it may prevent expected calculations (add warning on extra cols)
# OA: imported cols for ias must be exported same way (except ones which are generated) (existed on import and generated cases?)

# TODO 1 test all new generated cols will still be exported to ias OA:ok V:ok
#     test P_RAIN_1_1_1 will be not real data; lazy solution is to export anyway

# TODO 1 QOA should 'nee' -> 'NEE_PI', 'rg_1_1_1', 'par' be imported from ias?
#     V: _PI are generated, lvl+ (don't export, but import?)

from src.helpers.py_collections import invert_dict

COLS_IAS_USED_NORENAME_IMPORT = [
    # Script uses cols without renames (but lowercases on import)
    'WD_1_1_1',
    'TS_1_1_1', 'TS_2_1_1', 'TS_3_1_1',
    
    'RH_1_1_1',  # 'RH_1_1_1' <- 'RH_1_1_1' or ~'VPD_1_1_1'
    'P_1_1_1',  # 'P_1_1_1' <- 'P_1_1_1' or 'P_RAIN_1_1_1'
    'P_RAIN_1_1_1',  # 'P_RAIN_1_1_1' <- 'P_RAIN_1_1_1' or 'P_1_1_1'
    'TA_1_1_1',  # 'TA_1_1_1' <- 'TA_1_1_1' or 'air_temperature'
    
    # TODO 1 QOA: ALB_1_1_1 must be ignored (WARNING) (opposite of V: import it)
    'ALB_1_1_1',  # 'ALB_1_1_1' <- 'ALB_1_1_1' or 'swin_1_1_1', 'swout_1_1_1'
    
    # moved to COLS_IAS_CONVERSION_IMPORT
    # 'VPD_PI_1_1_1'
    # TODO QOA 2 ias: import other _PI cols or not? V: skip, _PI are cols of level > 2 vs OA: import
]
COLS_IAS_UNUSED_NORENAME_IMPORT = [
    # Script does not use, but may requre on export or import, for example:
    # IAS import (rename to lower) -> script processing -> IAS export (rename back to upper)
    # note: _1_1_1 can be dynamic, but will make occurence search bad
    'H2O_STR_1_1_1', 'FH2O_1_1_1',
    'TS_1_2_1', 'TS_1_3_1', 'TS_1_4_1',
    'T_DP_1_1_1', 'U_SIGMA_1_1_1', 'V_SIGMA_1_1_1', 'WTD_1_1_1', 'W_SIGMA_1_1_1',
    'FCH4_CMB_1_1_1', 'SPEC_PRI_REF_OUT_1_1_1', 'SPEC_PRI_TGT_IN_1_1_1', 'THROUGHFALL_1_1_1', 'MTCI_1_1_1',
    'FO3_1_1_1',
    'FO3_SSITC_TEST_1_1_1', 'NDVI_1_1_1', 'T_CANOPY_1_1_1', 'TCARI_1_1_1', 'H2O_STR_1_1_1', 'FN2O_CMB_1_1_1',
    'RECO_PI_1_1_1', 'EVI_1_1_1', 'P_SNOW_1_1_1', 'H_PI_1_1_1', 'R_UVB_1_1_1', 'PRI_1_1_1', 'WD_SIGMA_1_1_1',
    'T_SONIC_SIGMA_1_1_1', 'SPEC_NIR_IN_1_1_1', 'SW_BC_IN_1_1_1', 'T_BOLE_1_1_1', 'FNO2_1_1_1', 'SPEC_PRI_REF_IN_1_1_1',
    'MCRI_1_1_1', 'SPEC_RED_IN_1_1_1', 'STEMFLOW_1_1_1',
    'NO_1_1_1', 'NO2_1_1_1', 'APAR_1_1_1', 'PBLH_1_1_1', 'WS_MAX_1_1_1',
    'FETCH_FILTER_1_1_1', 'REDCl_1_1_1', 'PPFD_DIR_1_1_1', 'SPEC_PRI_TGT_OUT_1_1_1', 'FN2O_1_1_1', 'SPEC_NIR_OUT_1_1_1',
    'FETCH_80_1_1_1', 'PPFD_DIF_1_1_1', 'SAP_DT_1_1_1', 'LE_PI_1_1_1', 'SAP_FLOW_1_1_1', 'FNO_1_1_1', 'NEE_PI_1_1_1',
    'RUNOFF_1_1_1', 'SW_DIF_1_1_1', 'FCH4_PI_1_1_1', 'LEAF_WET_1_1_1', 'N2O_1_1_1', 'R_UVA_1_1_1', 'PPFD_BC_IN_1_1_1',
    'D_SNOW_1_1_1', 'SPEC_RED_OUT_1_1_1', 'NIRV_1_1_1', 'FC_CMB_1_1_1', 'FNO_CMB_1_1_1', 'CO2C13_1_1_1',
    'PPFD_OUT_1_1_1',
    'DBH_1_1_1', 'GPP_PI_1_1_1', 'FNO2_CMB_1_1_1',
    'SR_1_1_1', 'O3_1_1_1', 'REP_1_1_1',
    'PA_1_1_1', 'SG_1_1_1', 'SB_1_1_1',
]
COLS_IAS_NORENAME_IMPORT = COLS_IAS_UNUSED_NORENAME_IMPORT + COLS_IAS_USED_NORENAME_IMPORT
COLS_IAS_NORENAME_EXPORT = COLS_IAS_NORENAME_IMPORT

# COLS_IAS_UNUSED_NORENAME_IMPORT_DICT = {k: k.lower() for k in COLS_IAS_NORENAME_EXPORT}
COLS_IAS_NORENAME_EXPORT_DICT = {k.lower(): k for k in COLS_IAS_NORENAME_EXPORT}

# TODO 3 possible data integrity check to implement - from old ias instructions
# во входных биометах "Rg_1_1_1" должно быть тождествено равно "Swin_1_1_1", это то же самое.
# Если нет Swin_1_1_1, нужно написать туда значения из Rg_1_1_1


COLS_SCRIPT_E_TO_IAS_RENAMES = {
    # originates from conversion of file formats,
    
    # closely matches to columns which are renamed in the script on IAS export
    # only columns which are renamed in the script, not including ones with just changed case
    
    # TODO 1 test for no import renames (fx-lfs/todo)
    # Reminder: instead of
    # IAS -> (lower) -> SCRIPT,
    # some cols here may be yet silently fixed
    # IAS -> EDDYPRO -> (auto fix/repair after load) -> SCRIPT
    # EDDYPRO -> (auto fix/repair after load) fixes either should be:
    # - extracted to eddypro load
    # - generalised columns repair step
    # - simplified to a table with multiple + regex to one
    # check COLS_EDDYPRO_TO_IAS_RENAMES which is derived from this dict
    
    'co2_flux': 'FC_1_1_1', 'qc_co2_flux': 'FC_SSITC_TEST_1_1_1',
    'LE': 'LE_1_1_1', 'qc_LE': 'LE_SSITC_TEST_1_1_1',
    'H': 'H_1_1_1', 'qc_H': 'H_SSITC_TEST_1_1_1',
    'Tau': 'TAU_1_1_1', 'qc_Tau': 'TAU_SSITC_TEST_1_1_1',
    'co2_strg': 'SC_1_1_1', 'co2_mole_fraction': 'CO2_1_1_1',
    'h2o_mole_fraction': 'H2O_1_1_1', 'sonic_temperature': 'T_SONIC_1_1_1',
    'Lwin_1_1_1': 'LW_IN_1_1_1', 'Lwout_1_1_1': 'LW_OUT_1_1_1',
    'Rn_1_1_1': 'NETRAD_1_1_1', 'MWS_1_1_1': 'WS_1_1_1',
    'Pswc_1_1_1': 'SWC_1_1_1', 'Pswc_2_1_1': 'SWC_2_1_1', 'Pswc_3_1_1': 'SWC_3_1_1',
    'SHF_1_1_1': 'G_1_1_1', 'SHF_2_1_1': 'G_2_1_1', 'SHF_3_1_1': 'G_3_1_1', 'L': 'MO_LENGTH_1_1_1',
    '(z-d)/L': 'ZL_1_1_1',
    'x_peak': 'FETCH_MAX_1_1_1', 'x_70%': 'FETCH_70_1_1_1', 'x_90%': 'FETCH_90_1_1_1',
    'ch4_flux': 'FCH4_1_1_1', 'qc_ch4_flux': 'FCH4_SSITC_TEST_1_1_1', 'ch4_mole_fraction': 'CH4_1_1_1',
    
    # TODO 1 is it ok they are different? co2_signal_strength vs ch4_signal_strength
    # E: seems it was ok, but better to check
    
    # TODO QOA 1 ch4_signal_strength not in eddy or any specification? E: -> OA
    # IAS: CH4_RSSI_1_1_1 (%) CH4 Received Signal Strength Indicator
    # IAS: CO2_STR (-) СО2 signal strength
    # FF manual: CH42SS (CH4 Signal Strength или RSSI)	(-) <- does not match
    
    'ch4_strg': 'SCH4_1_1_1', 'ch4_signal_strength': 'CH4_RSSI_1_1_1', 'co2_signal_strength': 'CO2_STR_1_1_1',
    'H_strg': 'SH_1_1_1', 'LE_strg': 'SLE_1_1_1',
    
    # possibly cols which are generated if missing
    'PPFD_1_1_1': 'PPFD_IN_1_1_1',
    'Swin_1_1_1': 'SW_IN_1_1_1', 'Swout_1_1_1': 'SW_OUT_1_1_1',
    'u_star': 'USTAR_1_1_1',
    
    # TODO QOA 1 seems these were csf cols added, but they are not supposed to be imported from IAS, are they?
    # 'wind_dir': 'WD_SONIC', 'v_var': 'V_SIGMA', 'h2o_mixing_ratio': 'H2O_mixratio',
    
    # only case changed, moved to COLS_IAS_NORENAME
    # 'Rh_1_1_1': 'RH_1_1_1', 'Ta_1_1_1': 'TA_1_1_1', 'Ts_1_1_1': 'TS_1_1_1',
    # 'Pa_1_1_1': 'PA_1_1_1',
    # 'Ts_2_1_1': 'TS_2_1_1', 'Ts_3_1_1': 'TS_3_1_1',
    
    # moved to COLS_IAS_CONVERSION_IMPORT
    # 'VPD_1_1_1': 'VPD_PI_1_1_1'
}

COLS_IAS_CONVERSION_IMPORT = {'VPD_PI_1_1_1': 'vpd_1_1_1'}

COLS_SCRIPT_TO_IAS_RENAMES = {k.lower(): v for k, v in COLS_SCRIPT_E_TO_IAS_RENAMES.items()}
COLS_IAS_EXPORT_MAP = COLS_SCRIPT_TO_IAS_RENAMES | COLS_IAS_NORENAME_EXPORT_DICT
COLS_IAS_CONVERSION_EXPORT = invert_dict(COLS_IAS_CONVERSION_IMPORT)

COLS_IAS_IMPORT_MAP = invert_dict(COLS_IAS_EXPORT_MAP)

COLS_IAS_TIME = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']

COLS_IAS_KNOWN = list(COLS_IAS_IMPORT_MAP.keys()) + list(COLS_IAS_CONVERSION_IMPORT.keys()) + COLS_IAS_TIME
IAS_HEADER_DETECTION_COLS = COLS_IAS_KNOWN
