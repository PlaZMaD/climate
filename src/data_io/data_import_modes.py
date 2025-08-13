from enum import Enum


class ImportMode(Enum):
    # extension and data level before import
    EDDYPRO_FO = 1
    EDDYPRO_FO_AND_BIOMET = 2
    IAS = 3
    CSF = 4
    AUTO = 5


class InputFileType(Enum):
    # extension and processing level
    UNKNOWN = 'UNKNOWN'
    EDDYPRO_FO = 'EDDYPRO_FO'
    EDDYPRO_BIOMET = 'EDDYPRO_BIOMET'
    CSF = 'CSF'
    IAS = 'IAS'
