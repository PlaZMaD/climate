from enum import Enum


class ImportMode(Enum):
    # extension and data level before import
    EDDYPRO_FO = 'EDDYPRO_FO'
    EDDYPRO_FO_AND_BIOMET = 'EDDYPRO_FO_AND_BIOMET'
    IAS = 'IAS'
    # CSF = 'CSF' # not tested
    CSF_AND_BIOMET = 'CSF_AND_BIOMET'
    AUTO = 'AUTO'


class InputFileType(Enum):
    # extension and processing level
    UNKNOWN = 'UNKNOWN'
    EDDYPRO_FO = 'EDDYPRO_FO'
    EDDYPRO_BIOMET = 'EDDYPRO_BIOMET'
    CSF = 'CSF'
    IAS = 'IAS'


class IasExportIntervals(Enum):
    ALL = 'ALL'
    YEAR = 'YEAR'
    MONTH = 'MONTH'


# TODO 3 ensure cut is applied to all import types
# DEBUG_NROWS = 31 * 3 * 24 * 2 * 2
DEBUG_NROWS = 31 * 3 * 24 * 2