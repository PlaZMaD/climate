BIOMET_HEADER_DETECTION_COLS = [
    # just a sample, some cols may be missing
    'TIMESTAMP_1', 'Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1', 'Lwout_1_1_1',
    'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1'
]

BIOMET_USED_COLS = [
    'Ta_1_1_1', 'RH_1_1_1', 'Rg_1_1_1', 'Lwin_1_1_1', 'Lwout_1_1_1',
    'Swin_1_1_1', 'Swout_1_1_1', 'P_1_1_1'
]

BIOMET_HEADER_DETECTION_COLS_LOWER = [c.lower() for c in BIOMET_HEADER_DETECTION_COLS]
BIOMET_USED_COLS_LOWER = [c.lower() for c in BIOMET_USED_COLS]