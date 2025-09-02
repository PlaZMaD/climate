import logging
from pathlib import Path

from src.data_io.csf_import import import_csf
from src.data_io.data_import_modes import ImportMode, InputFileType
from src.data_io.eddypro_loader import load_eddypro
from src.data_io.ias_io import import_ias
from src.ffconfig import FFConfig
from src.data_io.csf_cols import CSF_HEADER_DETECTION_COLS
from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS, EDDYPRO_HEADER_DETECTION_COLS
from src.data_io.ias_cols import IAS_HEADER_DETECTION_COLS
from src.data_io.parse_fnames import try_parse_ias_fname, try_parse_eddypro_fname, try_parse_csf_fname
from src.data_io.table_loader import load_table_from_file
from src.helpers.io_helpers import ensure_path
from src.helpers.py_helpers import ensure_list

SUPPORTED_FILE_EXTS_LOWER = ['.csv', '.xlsx', '.xls']


class AutoImportException(Exception):
    pass


def detect_file_type(fpath: Path, nrows=4) -> InputFileType:
    df = load_table_from_file(fpath, nrows=nrows, header_row=None)

    # may be also consider exact header row place
    ias_cols = (set(IAS_HEADER_DETECTION_COLS), InputFileType.IAS)
    biomet_cols = (set(BIOMET_HEADER_DETECTION_COLS), InputFileType.EDDYPRO_BIOMET)
    eddypro_cols = (set(EDDYPRO_HEADER_DETECTION_COLS), InputFileType.EDDYPRO_FO)
    csf_cols = (set(CSF_HEADER_DETECTION_COLS), InputFileType.CSF)
    detect_col_targets = [ias_cols, biomet_cols, eddypro_cols, csf_cols]

    def match_ratio(sample: set, target: set):
        return len(sample & target) / len(sample)

    # upper/lower case is yet skipped intentionally
    header_matches = []
    for i, row in df.iterrows():
        fixed_row = row.dropna()
        for cols_set, ftype in detect_col_targets:
            mr = match_ratio(set(fixed_row), cols_set)
            header_matches += [(i, ftype, mr)]

    positive_matches = [m for m in header_matches if m[2] > 0.5]

    if len(positive_matches) == 1:
        _, ftype, _ = positive_matches[0]
        logging.info(f'Detected file {fpath} as {ftype}')
        return ftype
    else:
        guesses = '\n'.join([f'{i} {mr:0.2f} {ftype}' for i, ftype, mr in header_matches])
        logging.warning(f'Cannot detect file type {fpath}, row guesses are: \n'
                        f'{guesses}')
        return InputFileType.UNKNOWN


def detect_known_files(input_dir='.', from_list: list[Path] = None) -> dict[Path, InputFileType]:
    if not from_list:
        root_files = list(Path(input_dir).glob('*.*'))
        input_files = [f for f in root_files if f.suffix.lower() in SUPPORTED_FILE_EXTS_LOWER]
    else:
        input_files = from_list
    input_file_types = {f: detect_file_type(f) for f in input_files}
    return {k: v for k, v in input_file_types.items() if v != InputFileType.UNKNOWN}


def change_if_auto(option, new_option=None, new_option_call=None,
                   auto: str | ImportMode = 'auto',
                   ok_msg=None, skip_msg=None):
    # new_option_call can be used instead of new_option to optimise out new option detection:
    # if not auto, detection will be skipped

    if option != auto:
        if skip_msg:
            logging.warning(skip_msg)
        return option

    if new_option_call:
        assert new_option is None
        new_option = new_option_call()

    if ok_msg:
        logging.info(ok_msg)
    return new_option


def detect_input_mode(input_file_types: dict[Path, InputFileType]) -> ImportMode:
    input_ftypes = list(input_file_types.values())
    possible_input_modes = []

    if InputFileType.EDDYPRO_FO in input_ftypes:
        if InputFileType.EDDYPRO_BIOMET not in input_ftypes:
            possible_input_modes += [ImportMode.EDDYPRO_FO]
        else:
            # TODO QOA 1 is multiple supported?
            # if input_ftypes.count(InputFileType.EDDYPRO_BIOMET) > 1:
            #     raise AutoImportException('More than 2 biomet files detected')
            possible_input_modes += [ImportMode.EDDYPRO_FO_AND_BIOMET]

    if InputFileType.IAS in input_ftypes:
        possible_input_modes += [ImportMode.IAS]

    if InputFileType.CSF in input_ftypes:
        possible_input_modes += [ImportMode.CSF]

    if len(possible_input_modes) == 0:
        raise AutoImportException(
            f'No import modes possible, ensure input files are in the script folder and review log.')
    elif len(possible_input_modes) == 1:
        mode = possible_input_modes[0]
    else:
        raise AutoImportException(f'Multiple input modes possible: {possible_input_modes}, cannot auto pick.\n'
                                  "Remove some files or specify manually config['path'].")

    return mode


def detect_auto_config_ias(input_file_types: dict[Path, InputFileType]):
    paths = list(input_file_types.keys())
    return try_parse_ias_fname(paths[0].name)


def detect_auto_config_csf(input_file_types: dict[Path, InputFileType]):
    paths = list(input_file_types.keys())
    return try_parse_csf_fname(paths[0].name)


def detect_auto_config_eddypro(input_file_types: dict[Path, InputFileType]):
    # 1 or 0 biomet files are already ensured
    config_path = [k for k, v in input_file_types.items() if v == InputFileType.EDDYPRO_FO]
    return try_parse_eddypro_fname(Path(config_path[0]).name)


def auto_detect_input_files(config: FFConfig):
    # noinspection PyPep8Naming
    IM = ImportMode

    if config.input_files == 'auto':
        # logging.info("Detecting input files due to config['path'] = 'auto' ")
        input_files_auto = detect_known_files()
        config.input_files = change_if_auto(config.input_files, input_files_auto,
                                            ok_msg=f'Detected input files: {input_files_auto}')
    elif type(config.input_files) in [list, str]:
        user_fpaths = ensure_list(config.input_files, transform_func=ensure_path)
        config.input_files = detect_known_files(from_list=user_fpaths)
    elif type(config.input_files) is dict:
        config.input_files = {Path(fpath): ftype for fpath, ftype in config.input_files.items()}
    else:
        raise ValueError(f'{config.input_files=}')

    config.import_mode = detect_input_mode(config.input_files)
    logging.info(f'Detected import mode: {config.import_mode}')

    # TODO 2 update cells descs to match exact config naming after updating config options
    if config.import_mode == IM.IAS:
        res = detect_auto_config_ias(config.input_files)
    elif config.import_mode == IM.CSF:
        res = detect_auto_config_csf(config.input_files)
    elif config.import_mode in [IM.EDDYPRO_FO, IM.EDDYPRO_FO_AND_BIOMET]:
        res = detect_auto_config_eddypro(config.input_files)
    else:
        raise NotImplementedError
    ias_site_name_auto, ias_output_version_auto = res

    config.site_name = change_if_auto(config.site_name, ias_site_name_auto,
                                      ok_msg=f'Auto picked site name: {ias_site_name_auto}')
    config.ias_output_version = change_if_auto(config.ias_output_version, ias_output_version_auto,
                                               ok_msg=f'Auto picked ias version: {ias_output_version_auto}')

    config.has_meteo = config.import_mode in [IM.CSF, IM.IAS, IM.EDDYPRO_FO_AND_BIOMET]
    return config.input_files, config.import_mode, config.site_name, config.ias_output_version, config.has_meteo


def try_auto_detect_input_files(*args, **kwargs):
    try:
        return auto_detect_input_files(*args, **kwargs)
    except AutoImportException as e:
        logging.error(e)
        raise


def import_data(config: FFConfig):
    if config.import_mode in [ImportMode.EDDYPRO_FO, ImportMode.EDDYPRO_FO_AND_BIOMET]:
        res = load_eddypro(config)
    elif config.import_mode == ImportMode.IAS:
        res = import_ias(config)
    elif config.import_mode == ImportMode.CSF:
        res = import_csf(config)
    else:
        raise Exception(f"Please double check value of config['mode'], {config['mode']} is probably typo")

    paths = ensure_list(config.input_files.keys(), transform_func=str)
    logging.info(f"Data loaded from {paths}")

    return res