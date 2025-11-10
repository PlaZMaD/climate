import pprint
from pathlib import Path

from src.data_io.csf_cols import CSF_HEADER_DETECTION_COLS
from src.config.config_types import InputFileType, ImportMode
from src.data_io.eddypro_cols import EDDYPRO_HEADER_DETECTION_COLS
from src.data_io.biomet_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.ias_cols import IAS_HEADER_DETECTION_COLS
from src.data_io.parse_fnames import try_parse_eddypro_fname, try_parse_ias_fname, try_parse_csf_fname
from src.data_io.utils.table_loader import load_table_from_file
from src.ff_logger import ff_logger
from src.config.ff_config import FFConfig, FFGlobals
from src.helpers.io_helpers import ensure_path
from src.helpers.py_collections import ensure_list, format_dict

SUPPORTED_FILE_EXTS_LOWER = ['.csv', '.xlsx', '.xls']


class AutoImportException(Exception):
    pass


def detect_file_type(fpath: Path, nrows=4) -> InputFileType:
    df = load_table_from_file(fpath, nrows=nrows, header_row=None)
    
    biomest_cs = set(BIOMET_HEADER_DETECTION_COLS)
    ias_cs = set(IAS_HEADER_DETECTION_COLS) - biomest_cs
    
    # not expected to contain
    # eddypro_cs = set(EDDYPRO_HEADER_DETECTION_COLS) - biomest_cs
    # csf_cs = set(CSF_HEADER_DETECTION_COLS) - biomest_cs
    
    eddypro_cs = set(EDDYPRO_HEADER_DETECTION_COLS)
    csf_cs = set(CSF_HEADER_DETECTION_COLS)
    
    # may be also consider exact header row place
    detect_col_targets = [
        (InputFileType.IAS, ias_cs),
        (InputFileType.EDDYPRO_BIOMET, biomest_cs),
        (InputFileType.EDDYPRO_FO, eddypro_cs),
        (InputFileType.CSF, csf_cs)
    ]
    
    def match_ratio(sample: set, target: set):
        return len(sample & target) / len(sample)
    
    # upper/lower case is yet skipped intentionally
    header_matches = []
    for i, row in df.iterrows():
        fixed_row = row.dropna()
        if len(fixed_row) == 0:
            continue
        
        for ftype, cols_set in detect_col_targets:
            mr = match_ratio(set(fixed_row), cols_set)
            header_matches += [(i, ftype, mr)]
    
    positive_matches = [m for m in header_matches if m[2] > 0.5]
    
    if len(positive_matches) == 1:
        _, ftype, _ = positive_matches[0]
        # ff_log.info(f'Detected file {fpath} as {ftype}') # duplicates
        return ftype
    else:
        guesses = '\n'.join([f'row: {i} match: {mr:0.2f} {ftype}' for i, ftype, mr in header_matches])
        ff_logger.warning(f'Cannot detect file type {fpath}, row guesses are: \n'
                          f'{guesses} \n'
                          f'Consider specifying file types manually according to import cell description.')
        return InputFileType.UNKNOWN


def detect_known_files(input_dir=None, from_list: list[Path] = None) -> dict[Path, InputFileType]:
    if not from_list:
        root_files = list(Path(input_dir).glob('*.*'))
        input_files = [f for f in root_files if f.suffix.lower() in SUPPORTED_FILE_EXTS_LOWER]
    else:
        input_files = from_list
    input_file_types = {f: detect_file_type(f) for f in input_files}
    
    valid_ftypes = set(InputFileType) - {InputFileType.UNKNOWN}
    valid_ftype_names = [enum.value for enum in valid_ftypes]
    unknown_input_files = {k: v for k, v in input_file_types.items() if v == InputFileType.UNKNOWN}
    unknown_input_fnames = [str(k) for k in unknown_input_files.keys()]
    input_files_pprint = pprint.pformat({str(k): v.value for k, v in input_file_types.items()})

    if len(unknown_input_files) > 0:
        raise AutoImportException('\n'
                                  f'Files {unknown_input_fnames} are not recognised. You can try one of the following solutions: \n'
                                  f'- Change columns to better match one of the example files in the introduction {valid_ftype_names}. \n'
                                  '- Download and edit one of the examples, while keeping datetime format and column names. \n'
                                  '- Specify file type manually by changing UNKNOWN to one of the known format types: \n\n'
                                  f"config.data_import.input_files = {input_files_pprint}")
    
    return input_file_types


def change_if_auto(option, new_option=None, new_option_call=None,
                   auto: str | ImportMode = 'auto',
                   ok_msg=None, skip_msg=None):
    # new_option_call can be used instead of new_option to optimise out new option detection:
    # if not auto, detection will be skipped
    
    if option != auto:
        if skip_msg:
            ff_logger.warning(skip_msg)
        return option
    
    if new_option_call:
        assert new_option is None
        new_option = new_option_call()
    
    if ok_msg:
        ff_logger.info(ok_msg)
    return new_option


def detect_input_mode(input_file_types: dict[Path, InputFileType]) -> ImportMode:
    input_ftypes = list(input_file_types.values())
    possible_input_modes = []
    
    if InputFileType.EDDYPRO_FO in input_ftypes:
        if InputFileType.EDDYPRO_BIOMET not in input_ftypes:
            possible_input_modes += [ImportMode.EDDYPRO_FO]
        else:
            # TODO 2 QOA test if multiple biomets are still supported
            possible_input_modes += [ImportMode.EDDYPRO_FO_AND_BIOMET]
    
    if InputFileType.IAS in input_ftypes:
        possible_input_modes += [ImportMode.IAS]
    
    if InputFileType.CSF in input_ftypes:
        if InputFileType.EDDYPRO_BIOMET not in input_ftypes:
            possible_input_modes += [ImportMode.CSF]
            ff_logger.critical('CSF without biomet is yet experimental mode.')
        else:
            possible_input_modes += [ImportMode.CSF_AND_BIOMET]
    
    if len(possible_input_modes) == 0:
        raise AutoImportException(
            f'No import modes possible, ensure input files are in the script folder and review log.')
    elif len(possible_input_modes) == 1:
        mode = possible_input_modes[0]
    else:
        raise AutoImportException(f'Multiple input modes possible: {possible_input_modes}, cannot auto pick.\n'
                                  "Remove some files or specify manually config.data_in.input_files = {...} .")
    
    return mode


def detect_fname_options(input_file_types: dict[Path, InputFileType], import_mode: ImportMode):
    IM, IFT = ImportMode, InputFileType
    parse_fname_source = {
        IM.EDDYPRO_FO: IFT.EDDYPRO_FO,
        IM.EDDYPRO_FO_AND_BIOMET: IFT.EDDYPRO_FO,
        IM.IAS: IFT.IAS,
        IM.CSF: IFT.CSF,
        IM.CSF_AND_BIOMET: IFT.CSF
    }[import_mode]
    parser = {
        IFT.EDDYPRO_FO: try_parse_eddypro_fname,
        IFT.IAS: try_parse_ias_fname,
        IFT.CSF: try_parse_csf_fname
    }[parse_fname_source]
    
    paths = [k for k, v in input_file_types.items() if v == parse_fname_source]
    
    if len(paths) > 1:
        paths_info = ensure_list(paths, transform_func=lambda x: str(Path(x).name))
        ff_logger.info(f'Multiple file names can be used to auto detect site name: {paths_info}, \n'
                       'Using the first one or specify manually in the options.')
    
    if len(paths) >= 1:
        ias_site_name_auto, ias_out_version_auto = parser(paths[0].name)
    else:
        ias_site_name_auto, ias_out_version_auto = None, None
    
    if ias_site_name_auto is None:
        ias_site_name_auto = 'unknown_site'
    if ias_out_version_auto is None:
        ias_out_version_auto = 'vNN'
    
    return ias_site_name_auto, ias_out_version_auto


def detect_input_files(config: FFConfig, gl: FFGlobals):
    # noinspection PyPep8Naming
    IM = ImportMode
    # TODO 2 do not change config here, consider moving all auto options to gl ?
    cfg_imp = config.data_import
    cfg_exp = config.data_export
    cfg_meta = config.metadata
    
    if cfg_imp.input_files == 'auto':
        # ff_log.info("Detecting input files due to config['path'] = 'auto' ")
        input_files_auto = detect_known_files(input_dir=gl.input_dir)
        input_files_info = format_dict(input_files_auto, separator=': ')
        cfg_imp.input_files = change_if_auto(cfg_imp.input_files, input_files_auto,
                                             ok_msg=f'Detected input files: {input_files_info}')
    elif type(cfg_imp.input_files) in [list, str]:
        user_fpaths = ensure_list(cfg_imp.input_files, transform_func=ensure_path)
        cfg_imp.input_files = detect_known_files(from_list=user_fpaths)
    elif type(cfg_imp.input_files) is dict:
        cfg_imp.input_files = {Path(fpath): ftype for fpath, ftype in cfg_imp.input_files.items()}
    else:
        raise ValueError(f'{cfg_imp.input_files=}')
    
    cfg_imp.import_mode = detect_input_mode(cfg_imp.input_files)
    ff_logger.info(f'Import mode: {cfg_imp.import_mode}')
    
    # TODO 1 update cells desc to match exact config naming after updating config options
    auto_site_name, auto_ias_ver = detect_fname_options(cfg_imp.input_files, cfg_imp.import_mode)
    
    cfg_meta.site_name = change_if_auto(cfg_meta.site_name, auto_site_name,
                                        ok_msg=f'Auto detected site name: {auto_site_name}')
    cfg_exp.ias.out_fname_ver_suffix = change_if_auto(cfg_exp.ias.out_fname_ver_suffix, auto_ias_ver,
                                                      ok_msg=f'Auto detected ias version: {auto_ias_ver}')
    
    # TODO 1 _has_meteo vs has_meteo, duplicates in import routines 
    has_meteo = cfg_imp.import_mode in [IM.CSF_AND_BIOMET, IM.IAS, IM.EDDYPRO_FO_AND_BIOMET]
    return cfg_imp.input_files, cfg_imp.import_mode, cfg_meta.site_name, cfg_exp.ias.out_fname_ver_suffix, has_meteo


def try_auto_detect_input_files(*args, **kwargs):
    try:
        return detect_input_files(*args, **kwargs)
    except AutoImportException as e:
        ff_logger.error(e)
        raise
