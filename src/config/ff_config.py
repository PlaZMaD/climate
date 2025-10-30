from pathlib import Path
from typing import Annotated

from src.config.config_types import ImportMode, InputFileType
from src.config.config_io import FFBaseModel, BaseConfig
from src.helpers.py_helpers import gen_enum_info


# DEFAULT_CONFIG = 'misc/default_config.yaml'
# TODO 1 strings in arrays as strings, not values: missing_data_codes: [-9999, NAN]
# TODO 2 config file link in the introduction - how to deal with updates?


class InputFileConfig(FFBaseModel):
    """ generate new timestamps in case of errors """
    repair_time: bool = None
    """ can replace -9999 to np.nan """
    # TODO 1 config: some options can be None on load, but better not during run; how to deal with it fluently?
    missing_data_codes: list[str | int] = None
    skip_validation: bool = None
    
    # full auto mode may be difficult due to human date and time col names in all the cases (but heuristic?)
    # time_converter: Callable[[Any], Any]
    # TODO 3 func <-> str is used to support config save load, but it won't be safe in server mode (UI or Colab ok)
    # time_converter_str: str


class MergedDateTimeFileConfig(InputFileConfig):
    datetime_col: str = None
    try_datetime_formats: str | list[str] = None


class SeparateDateTimeFileConfig(InputFileConfig):
    time_col: str = None
    try_time_formats: str | list[str] = None
    date_col: str = None
    try_date_formats: str | list[str] = None


class RepConfig(FFBaseModel):
    is_to_apply_u_star_filtering: bool = None
    ustar_threshold_fallback: float = None
    ustar_rg_source: Annotated[str, 'Rg_th_Py, Rg_th_REP, Rg, ""'] = None
    is_bootstrap_u_star: bool = None
    # TODO 3 add enums?
    u_star_seasoning: Annotated[str, 'WithinYear, Continuous, User'] = None
    
    is_to_apply_partitioning: bool = None
    
    partitioning_methods: Annotated[list[str], 'Reichstein05, Lasslop10'] = None
    
    latitude: float = None
    longitude: float = None
    timezone: float = None
    
    temperature_data_variable: str = None
    
    site_id: str = None
    u_star_method: str = None
    is_to_apply_gap_filling: bool = None
    input_file: str = None
    output_dir: str = None
    log_fname_end: str = '_log.txt'


class FiltersConfig(FFBaseModel):
    # TODO 1 auto = initial; changed or not? make this config-wide approach
    meteo: dict = None
    min_max: dict = None
    window: dict = None
    quantile: dict = None
    madhampel: dict = None
    winter_date_ranges: list[list[str]] = None
    man_ranges: list[list[str]] = None


# TODO 1 V: yaml should have comments, will loading them from default config work? in annotation? auto gen from source? toml lib?
# all settings by default, partial mode optional (or commented out?) if not default, comment?
class FFConfig(BaseConfig):
    version: str = None
    """  True: fast load, just 3 months of data """
    debug: bool = None
    
    # TODO 3 all auto should be in default as non-auto (not to trigger auto on save) and None must be allowed type, not clean
    input_files: str | list[str] | dict[str | Path, InputFileType] = None
    # flexible, but too complicated to edit for user?
    # files: dict[str, InputFileConfig]
    
    eddypro_fo: SeparateDateTimeFileConfig = SeparateDateTimeFileConfig.model_construct()
    eddypro_biomet: MergedDateTimeFileConfig = MergedDateTimeFileConfig.model_construct()
    ias: MergedDateTimeFileConfig = MergedDateTimeFileConfig.model_construct()
    csf: MergedDateTimeFileConfig = MergedDateTimeFileConfig.model_construct()
    
    import_mode: Annotated[ImportMode | None, gen_enum_info(ImportMode)] = None
    time_col: str = None
    
    # TODO 1 move to ig?
    has_meteo: bool = None
    
    site_name: str = None
 
    ias_out_fname_ver_suffix: str = None
    ias_export_intervals: str = None
    
    qc: dict = None
    filters: FiltersConfig = FiltersConfig.model_construct()
    
    calc_nee: bool = None
    calc_with_strg: bool = None
    reddyproc: RepConfig = RepConfig.model_construct()


class RepOutInfo(FFBaseModel):
    start_year: int
    end_year: int
    fnames_prefix: str


class FFGlobals(FFBaseModel):
    # not yet clear if to include in user config or not
    # TODO 2 refactor: to output_dir
    out_dir: Path
    input_dir: Path
    repo_dir: Path
    
    points_per_day: int = None
    
    rep_arc_exclude_files: list[Path] = None
    rep_out_info: RepOutInfo = None
    rep_level3_fpath: Path = None
