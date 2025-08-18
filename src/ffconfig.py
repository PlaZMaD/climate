import logging
from pathlib import Path
from typing import Callable, Any

from src.data_io.data_import_modes import ImportMode, InputFileType
from src.helpers.config_io import ValidatedBaseModel, save_basemodel, load_basemodel, partial_model
from src.helpers.py_helpers import func_to_str, str_to_func


class InputFileConfig(ValidatedBaseModel):
    # генерируем новые временные метки в случае ошибок
    repair_time: bool = True
    # заменяем -9999  на np.nan
    missing_data_codes: str | list[str] = ['-9999']

    # full auto mode may be difficult due to human date and time col names in all the cases (but heuristic?)
    time_converter: Callable[[Any], Any] | None
    # TODO 3 str is used to support config save load, but it won't be safe in server mode (UI or Colab ok)
    time_converter_str: str


class RepConfig(ValidatedBaseModel):
    site_id: str

    is_to_apply_u_star_filtering: bool
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback: float
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # 'Rg_th_Py', 'Rg_th_REP' - estimate by theoretical algs,
    # 'Rg' - by real data, '' - ignore Rg and filter both days and nights
    ustar_rg_source: str
    is_bootstrap_u_star: bool
    # u_star_seasoning: one of 'WithinYear', 'Continuous', 'User'
    u_star_seasoning: str

    is_to_apply_partitioning: bool

    # partitioning_methods: one or both of 'Reichstein05', 'Lasslop10'
    partitioning_methods: list[str]

    latitude: float
    longitude: float
    timezone: float

    # 'Tsoil'
    temperature_data_variable: str

    # do not change
    u_star_method: str
    is_to_apply_gap_filling: bool
    input_file: str
    output_dir: str
    log_fname_end: str = '_log.txt'


class FiltersConfig(ValidatedBaseModel):
    meteo: dict = {}
    quantile: dict = {}
    madhampel: dict = {}
    window: dict = {}
    min_max: dict = {}
    man_ranges: list[tuple[str, str]] = {}


@partial_model
class FFConfig(ValidatedBaseModel):
    # TODO 3 auto read (from env?) in FluxFilter.py
    version: str

    input_files: str | list[str] | dict[str | Path, InputFileType] = 'auto'
    # flexible, but too complicated to edit for user?
    # files: dict[str, InputFileConfig]

    eddypro_fo: InputFileConfig
    eddypro_biomet: InputFileConfig
    # ias: InputFileConfig
    # csf: InputFileConfig

    site_name: str = 'auto'
    ias_output_version: str = 'auto'

    has_meteo: bool
    qc: dict = {}
    filters: FiltersConfig

    calc_nee: bool
    calc_with_strg: bool
    reddyproc: RepConfig

    # options not for ipynb:

    # if True will load just a small chunk of data
    time_col: str = 'datetime'
    debug: bool = False
    import_mode: ImportMode = ImportMode.AUTO


class RepOutInfo(ValidatedBaseModel):
    start_year: int
    end_year: int
    fnames_prefix: str


@partial_model
class FFGlobals(ValidatedBaseModel):
    # not yet clear if to include in user config or not
    out_dir: Path

    points_per_day: int

    rep_arc_exclude_files: list[Path]
    rep_out_info: RepOutInfo
    rep_level3_fpath: Path


def save_config(config: FFConfig, fpath: Path):
    # TODO 3 switch to auto type conversion if required?
    if config.eddypro_fo.time_converter:
        if not config.eddypro_fo.time_converter_str:
            config.eddypro_fo.time_converter_str = func_to_str(config.eddypro_fo.time_converter)
        else:
            logging.warning('Time conversion function for eddypro cannot be saved if it was loaded. '
                            'If necessary, remove it from config or recreate config.')
        config.eddypro_fo.time_converter = None

    if config.eddypro_biomet.time_converter:
        if not config.eddypro_biomet.time_converter_str:
            config.eddypro_biomet.time_converter_str = func_to_str(config.eddypro_biomet.time_converter)
        else:
            logging.warning('Time conversion function for biomet cannot be saved if it was loaded. '
                            'If necessary, remove it from config or recreate config.')
        config.eddypro_biomet.time_converter = None

    save_basemodel(fpath, config)


def load_config(fpath: Path) -> FFConfig:
    config = load_basemodel(fpath, FFConfig)

    if config.eddypro_fo.time_converter_str:
        config.eddypro_fo.time_converter = str_to_func(config.eddypro_fo.time_converter_str)
    if config.eddypro_biomet.time_converter_str:
        config.eddypro_biomet.time_converter = str_to_func(config.eddypro_biomet.time_converter_str)

    return config
