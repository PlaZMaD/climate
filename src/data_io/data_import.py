from pathlib import Path

from src.helpers.io_helpers import ensure_path
from src.helpers.py_helpers import ensure_list, format_dict
from src.ff_logger import ff_log
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

SUPPORTED_FILE_EXTS_LOWER = ['.csv', '.xlsx', '.xls']


# info on all imports:

# - full output, csf, ias = always 30 min
#   biomet - must be resampled, can not match at all

# TODO 1 test if only WARNING for unknowns
# - OA, V: ff_log.critical() for unknown cols, don't error
#   V: but in IAS, require by specification (due to check instrument)

# V: newly generated cols can be considered same as if imported for simplicity

# - mid-script biomet is replaced with "meteo params" or just col set OA & V:ok
# - OA: 2-4 levels = biomet, eddy (are dupes are possible which damage that way to define specification?)


# TODO 3 consider a table with all simple col ops instead of just untransparent import and export transforms
# problem: Excel vs VCS, use yaml table? csv? ...?
# handling unit/str conversions between import and export if name is same?
# ias check, ias export, ias import, initial script renames, renames during script run (required for export)
# E: unclear if table will help, people may damage it on edits (may be mega-config?)


# FluxFiler.py:
# O: check cell description for logic
# have_* flags:
# were not originally a way to store info which col is generated
# TODO 3 dictionary + optional transform lambda instead? useful to view cols flow,
# flags seems not nessesary or at some places var instead of const fits too, like p_rain = rain
# E: ok, requires prev section edits too, but low benefit

# TODO 1 0.9.4 problem: vpd imported from FO, but ignored?
# TODO 1 QOA ['vpd'] in FO (Pa?) have other units from ['vpd_1_1_1'] in biomet (kPa), but script L2-L4 specs is FO name with biomet units? ias hPa 6-140 ?
# E: 'VPD' could be bad ? should 'VPD_PI_1_1_1'  be imported from IAS? (no VPD)
# DONE OA, V: ias: import VPD_PI and convert (via generalised rename lambda function though)


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
        ff_log.warning(f'Cannot detect file type {fpath}, row guesses are: \n'
                       f'{guesses} \n'
                       f'Consider specifying file types manually according to import cell description.')
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
            ff_log.warning(skip_msg)
        return option
    
    if new_option_call:
        assert new_option is None
        new_option = new_option_call()
    
    if ok_msg:
        ff_log.info(ok_msg)
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
            # possible_input_modes += [ImportMode.CSF]
            ff_log.warning('Found CSF, but biomet is missing. Biomet data is required to use CSF import mode.')
        else:
            possible_input_modes += [ImportMode.CSF_AND_BIOMET]
    
    if len(possible_input_modes) == 0:
        raise AutoImportException(
            f'No import modes possible, ensure input files are in the script folder and review log.')
    elif len(possible_input_modes) == 1:
        mode = possible_input_modes[0]
    else:
        raise AutoImportException(f'Multiple input modes possible: {possible_input_modes}, cannot auto pick.\n'
                                  "Remove some files or specify manually config.input_files = {...} .")
    
    return mode


def detect_auto_fname_options(input_file_types: dict[Path, InputFileType], import_mode: ImportMode):
    IM, IFT = ImportMode, InputFileType
    parse_fname_source = {
        IM.EDDYPRO_FO: IFT.EDDYPRO_FO,
        IM.EDDYPRO_FO_AND_BIOMET: IFT.EDDYPRO_FO,
        IM.IAS: IFT.IAS,
        # IM.CSF: IFT.CSF,
        IM.CSF_AND_BIOMET: IFT.CSF
    }[import_mode]
    parser = {
        IFT.EDDYPRO_FO: try_parse_eddypro_fname,
        IFT.IAS: try_parse_ias_fname,
        IFT.CSF: try_parse_csf_fname
    }[parse_fname_source]
    
    paths = [k for k, v in input_file_types.items() if v == parse_fname_source]
    
    if len(paths) > 1:
        paths_info = ensure_list(paths, str)
        ff_log.warning(f'Multiple file names can be used to auto detect site: {paths_info}, \n'
                       'Using the first one or specify auto options.')
    
    if len(paths) >= 1:
        ias_site_name_auto, ias_out_version_auto = parser(paths[0].name)
    else:
        ias_site_name_auto, ias_out_version_auto = None, None
    
    if ias_site_name_auto is None:
        ias_site_name_auto = 'unknown_site'
    if ias_out_version_auto is None:
        ias_out_version_auto = 'vNN'
    
    return ias_site_name_auto, ias_out_version_auto


def auto_detect_input_files(config: FFConfig):
    # noinspection PyPep8Naming
    IM = ImportMode
    
    if config.input_files == 'auto':
        # ff_log.info("Detecting input files due to config['path'] = 'auto' ")
        input_files_auto = detect_known_files()
        input_files_info = format_dict(input_files_auto, separator=': ')
        config.input_files = change_if_auto(config.input_files, input_files_auto,
                                            ok_msg=f'Detected input files: {input_files_info}')
    elif type(config.input_files) in [list, str]:
        user_fpaths = ensure_list(config.input_files, transform_func=ensure_path)
        config.input_files = detect_known_files(from_list=user_fpaths)
    elif type(config.input_files) is dict:
        config.input_files = {Path(fpath): ftype for fpath, ftype in config.input_files.items()}
    else:
        raise ValueError(f'{config.input_files=}')
    
    config.import_mode = detect_input_mode(config.input_files)
    ff_log.info(f'Import mode: {config.import_mode}')
    
    # TODO 1 update cells desc to match exact config naming after updating config options
    auto_site_name, auto_ias_ver = detect_auto_fname_options(config.input_files, config.import_mode)
    
    config.site_name = change_if_auto(config.site_name, auto_site_name,
                                      ok_msg=f'Auto picked site name: {auto_site_name}')
    config.ias_out_version = change_if_auto(config.ias_out_version, auto_ias_ver,
                                            ok_msg=f'Auto picked ias version: {auto_ias_ver}')
    
    # TODO 2 _has_meteo vs has_meteo, duplicates in import toutines 
    config._has_meteo = config.import_mode in [IM.CSF_AND_BIOMET, IM.IAS, IM.EDDYPRO_FO_AND_BIOMET]
    return config.input_files, config.import_mode, config.site_name, config.ias_out_version, config._has_meteo


# TODO 1 config.input_files = ... will not reset on cell re-run, this damages re-run BADLY, fix
def try_auto_detect_input_files(*args, **kwargs):
    try:
        return auto_detect_input_files(*args, **kwargs)
    except AutoImportException as e:
        ff_log.error(e)
        raise


def import_data(config: FFConfig):
    if config.import_mode in [ImportMode.EDDYPRO_FO, ImportMode.EDDYPRO_FO_AND_BIOMET]:
        res = load_eddypro(config)
    elif config.import_mode == ImportMode.IAS:
        res = import_ias(config)
    # elif config.import_mode in [ImportMode.CSF, ImportMode.CSF_AND_BIOMET]:
    elif config.import_mode in [ImportMode.CSF_AND_BIOMET]:
        res = import_csf(config)
    else:
        raise Exception(f"Please double check value of config['mode'], {config['mode']} is probably typo")
    
    paths = format_dict(config.input_files, separator=': ')
    # DONE logs:  fix log
    ff_log.info(f'Data imported from files: {paths} \n')
    
    # TODO 2 import: if to use fo and biomet from different years, this will fail on rep export; ensure this is detected earlier
    # assert res[0][config.time_col].isna().sum() == 0
    
    return res
