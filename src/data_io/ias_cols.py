# TODO Q 2 store in table file instead (some cols are branching, like rain <-> heavey rain); other problems if table?
# specifically mark cols used in the script and unused?
# currently 4 column names variations are possible:
# IAS file, EddyPro file, notebook import, export (after all the processing)

from src.helpers.py_helpers import invert_dict

COLS_EDDYPRO_TO_IAS = {
	'co2_flux': 'FC_1_1_1', 'qc_co2_flux': 'FC_SSITC_TEST_1_1_1',
	'LE': 'LE_1_1_1', 'qc_LE': 'LE_SSITC_TEST_1_1_1',
	'H': 'H_1_1_1', 'qc_H': 'H_SSITC_TEST_1_1_1',
	'Tau': 'TAU_1_1_1', 'qc_Tau': 'TAU_SSITC_TEST_1_1_1',
	'co2_strg': 'SC_1_1_1', 'co2_mole_fraction': 'CO2_1_1_1',
	'h2o_mole_fraction': 'H2O_1_1_1', 'sonic_temperature': 'T_SONIC_1_1_1',
	'Swin_1_1_1': 'SW_IN_1_1_1', 'Swout_1_1_1': 'SW_OUT_1_1_1',
	'Lwin_1_1_1': 'LW_IN_1_1_1', 'Lwout_1_1_1': 'LW_OUT_1_1_1',
	'Rn_1_1_1': 'NETRAD_1_1_1', 'MWS_1_1_1': 'WS_1_1_1',
	'Ts_1_1_1': 'TS_1_1_1',
	'Pswc_1_1_1': 'SWC_1_1_1', 'Pswc_2_1_1': 'SWC_2_1_1', 'Pswc_3_1_1': 'SWC_3_1_1',
	'SHF_1_1_1': 'G_1_1_1', 'SHF_2_1_1': 'G_2_1_1', 'SHF_3_1_1': 'G_3_1_1', 'L': 'MO_LENGTH_1_1_1',
	'(z-d)/L': 'ZL_1_1_1',
	'x_peak': 'FETCH_MAX_1_1_1', 'x_70%': 'FETCH_70_1_1_1', 'x_90%': 'FETCH_90_1_1_1',
	'ch4_flux': 'FCH4_1_1_1', 'qc_ch4_flux': 'FCH4_SSITC_TEST_1_1_1', 'ch4_mole_fraction': 'CH4_1_1_1',
	'ch4_strg': 'SCH4_1_1_1', 'ch4_signal_strength': 'CH4_RSSI_1_1_1', 'co2_signal_strength': 'CO2_STR_1_1_1',

	# TODO 1 are they correct, i.e. if conversion/rename happens as expected in the notebook?
	'Ta_1_1_1': 'TA_1_1_1',
	'u*': 'USTAR_1_1_1',
	'PPFD_1_1_1': 'PPFD_IN_1_1_1',
	'Rh_1_1_1': 'RH_1_1_1', 'VPD_1_1_1': 'VPD_1_1_1',

	# Optional
	'H_strg': 'SH_1_1_1', 'LE_strg': 'SLE_1_1_1',
}
# TODO 1 add missing from ias_error_check.known_columns
# TODO 1 compare to COLS_EDDYPRO_TO_IAS, find optimal way
COLS_EDDYPRO_TO_IAS_DUPE = {
	# specifically about conversion of file formats,
	# SCRIPT_TO_IAS != EDDYPRO_TO_IAS because script renames some of them during run
	# was duplicated previously, used in export
	# also check export:
	# 		df['SH_1_1_1'] = df['h_strg']
	# 	if 'le_strg' in df.columns:
	# 		df['SLE_1_1_1'] = df['le_strg']
	'co2_flux': 'FC_1_1_1', 'qc_co2_flux': 'FC_SSITC_TEST_1_1_1',
	'LE': 'LE_1_1_1', 'qc_LE': 'LE_SSITC_TEST_1_1_1',
	'H': 'H_1_1_1', 'qc_H': 'H_SSITC_TEST_1_1_1',
	'Tau': 'TAU_1_1_1',	'qc_Tau': 'TAU_SSITC_TEST_1_1_1',
	'co2_strg': 'SC_1_1_1', 'co2_mole_fraction': 'CO2_1_1_1',
	'h2o_mole_fraction': 'H2O_1_1_1', 'sonic_temperature': 'T_SONIC_1_1_1',
	'Swin_1_1_1': 'SW_IN_1_1_1', 'Swout_1_1_1': 'SW_OUT_1_1_1',
	'Lwin_1_1_1': 'LW_IN_1_1_1', 'Lwout_1_1_1': 'LW_OUT_1_1_1',
	'PPFD_1_1_1': 'PPFD_IN_1_1_1',
	'Rn_1_1_1': 'NETRAD_1_1_1', 'MWS_1_1_1': 'WS_1_1_1',
	'Pswc_1_1_1': 'SWC_1_1_1', 'Pswc_2_1_1': 'SWC_2_1_1', 'Pswc_3_1_1': 'SWC_3_1_1',
	'SHF_1_1_1': 'G_1_1_1', 'SHF_2_1_1': 'G_2_1_1', 'SHF_3_1_1': 'G_3_1_1', 'L': 'MO_LENGTH_1_1_1',
	'(z-d)/L': 'ZL_1_1_1',
	'x_peak': 'FETCH_MAX_1_1_1', 'x_70%': 'FETCH_70_1_1_1',	'x_90%': 'FETCH_90_1_1_1',
	'ch4_flux': 'FCH4_1_1_1', 'qc_ch4_flux': 'FCH4_SSITC_TEST_1_1_1', 'ch4_mole_fraction': 'CH4_1_1_1',
	'ch4_strg': 'SCH4_1_1_1', 'ch4_signal_strength': 'CH4_RSSI_1_1_1', 'co2_signal_strength': 'CO2_STR_1_1_1',

	'rh_1_1_1': 'RH_1_1_1',
	'Ta_1_1_1': 'TA_1_1_1',
	'Ts_1_1_1': 'TS_1_1_1',
	# TODO 1 duplicates COLS_UNUSED_IAS, comment out and include dynamically?
	'Pa_1_1_1': 'PA_1_1_1',
	'Ts_2_1_1': 'TS_2_1_1', 'Ts_3_1_1': 'TS_3_1_1',
	# TODO 1 COLS_SCRIPT_TO_IAS2
	'u_star': 'USTAR_1_1_1', 'vpd_1_1_1': 'VPD_1_1_1',
}

COLS_EDDYPROL_TO_IAS = {k.lower(): v for k, v in COLS_EDDYPRO_TO_IAS.items()}
# IAS optional rules are more complex and placed into IAS check tool
COLS_IAS_TO_SCRIPT = invert_dict(COLS_EDDYPROL_TO_IAS)

# unused
COLS_SCRIPT_TO_IAS2 = {
	# only overrides of COLS_EDDYPRO_TO_IAS
	'u_star': 'USTAR_1_1_1', 'vpd_1_1_1': 'VPD_1_1_1'
}

# TODO _1_1_1 can be dynamic
COLS_UNUSED_IAS = [
	# Script does not use, buu should keep (?) them during chain:
	# IAS import (rename to lower) -> script processing -> IAS export (rename back to upper)
	# eddypro has h2o_strg
	'H2O_STR_1_1_1',

	# TODO 1 used in fluxfilter
	'PA_1_1_1',

	# TODO 1 P_1_1_1, P_RAIN are supported
	# TODO 1 problem: previously p_1_1_1 was not droppoing to outputs because it may be generated during script col
	# currently, it will because all these cols are included; what to do?

	'FH2O_1_1_1', 'P_1_1_1',
	'TS_1_2_1', 'TS_1_3_1', 'TS_1_4_1', 'TS_2_1_1', 'TS_3_1_1',
	'T_DP_1_1_1', 'U_SIGMA_1_1_1', 'VPD_PI_1_1_1', 'V_SIGMA_1_1_1', 'WD_1_1_1', 'WTD_1_1_1', 'W_SIGMA_1_1_1',
	'FCH4_CMB_1_1_1', 'SPEC_PRI_REF_OUT_1_1_1', 'SPEC_PRI_TGT_IN_1_1_1', 'THROUGHFALL_1_1_1', 'MTCI_1_1_1',
	'FO3_SSITC_TEST_1_1_1', 'NDVI_1_1_1', 'T_CANOPY_1_1_1', 'TCARI_1_1_1', 'H20_STR_1_1_1', 'FN2O_CMB_1_1_1',
	'RECO_PI_1_1_1', 'EVI_1_1_1', 'P_SNOW_1_1_1', 'H_PI_1_1_1', 'R_UVB_1_1_1', 'PRI_1_1_1', 'WD_SIGMA_1_1_1',
	'T_SONIC_SIGMA_1_1_1', 'SPEC_NIR_IN_1_1_1', 'SW_BC_IN_1_1_1', 'T_BOLE_1_1_1', 'FNO2_1_1_1', 'SPEC_PRI_REF_IN_1_1_1',
	'MCRI_1_1_1', 'SPEC_RED_IN_1_1_1', 'STEMFLOW_1_1_1', 'NO2_1_1_1', 'APAR_1_1_1', 'PBLH_1_1_1', 'WS_MAX_1_1_1',
	'FETCH_FILTER_1_1_1', 'REDCl_1_1_1', 'PPFD_DIR_1_1_1', 'SPEC_PRI_TGT_OUT_1_1_1', 'FN2O_1_1_1', 'SPEC_NIR_OUT_1_1_1',
	'FETCH_80_1_1_1', 'PPFD_DIF_1_1_1', 'SAP_DT_1_1_1', 'LE_PI_1_1_1', 'SAP_FLOW_1_1_1', 'FNO_1_1_1', 'NEE_PI_1_1_1',
	'RUNOFF_1_1_1', 'SW_DIF_1_1_1', 'FCH4_PI_1_1_1', 'LEAF_WET_1_1_1', 'N2O_1_1_1', 'R_UVA_1_1_1', 'PPFD_BC_IN_1_1_1',
	'D_SNOW_1_1_1', 'SPEC_RED_OUT_1_1_1', 'NIRV_1_1_1', 'FC_CMB_1_1_1', 'FNO_CMB_1_1_1', 'CO2C13_1_1_1', 'PPFD_OUT_1_1_1',
	'DBH_1_1_1', 'GPP_PI_1_1_1',  'FNO2_CMB_1_1_1'

	# Special mentions:
	# albedo is calculated in the script instead of using this column
	'ALB_1_1_1',
]


'''
# TODO 1 investigate, used somewhere
'P_RAIN': [('FluxFilter.py'), ('src/data_io/ias_io.py')],

 'FO3': [('FluxFilter.py')],
 'NO': [('FluxFilter.py'), ('src/data_io/data_import.py'), ('src/data_io/parse_fnames.py')],
 'PA': [('FluxFilter.py'), ('src/data_io/ias_io.py'), ('src/helpers/py_helpers.py'), ('src/reddyproc/postprocess_graphs.py')],
 'SG': [('FluxFilter.py'), ('src/reddyproc/reddyproc_wrapper.r'), ('src/reddyproc/web_tool_sources_adapted.r')],
 'REP': [('FluxFilter.py'), ('src/cells_mirror/cell_reddyproc_process.py'), ('src/reddyproc/postprocess_calc_means.r'), ('src/reddyproc/preprocess_rg.py'), ('src/reddyproc/reddyproc_extensions.r'), ('src/reddyproc/web_tool_sources_adapted.r'), ('test/reddyproc/test_process.r')],
 'O3': [('FluxFilter.py')],
 'SB': [('FluxFilter.py'), ('src/data_io/parse_fnames.py'), ('test/data_io/test_ias_to_csv.py')],
 'SR': [('FluxFilter.py')],
'''


COLS_UNUSED_IAS_TO_SCRIPT = {k: k.lower() for k in COLS_UNUSED_IAS}

IAS_HEADER_DETECTION_COLS = COLS_EDDYPRO_TO_IAS.values()
COLS_IAS_TIME = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']
