from enum import Enum


class ImportMode(Enum):
    # extension and data level before import
    EDDYPRO_FO = 'EDDYPRO_FO'
    EDDYPRO_FO_AND_BIOMET = 'EDDYPRO_FO_AND_BIOMET'
    IAS = 'IAS'
    CSF = 'CSF'
    AUTO = 'AUTO'


class InputFileType(Enum):
    # extension and processing level
    UNKNOWN = 'UNKNOWN'
    EDDYPRO_FO = 'EDDYPRO_FO'
    EDDYPRO_BIOMET = 'EDDYPRO_BIOMET'
    CSF = 'CSF'
    IAS = 'IAS'
