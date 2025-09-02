"""
All values which are used in ipynb must be set '= None' here
or detecting which values were used and changed (fallbacks, autos) starts to be extra complex
"""
import contextlib
import logging
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Annotated, Self


from src.data_io.data_import_modes import ImportMode, InputFileType
from src.helpers.config_io import TrackedBaseModel, ConfigStoreMode, ConfigModel
from src.helpers.env_helpers import ENV
from src.helpers.py_helpers import gen_enum_info
from src.helpers.io_helpers import find_unique_file

DEFAULT_CONFIG = 'misc/default_config.yaml'


class TrackedConfig(ConfigModel):   
    @classmethod
    def save(cls: Self, config, fpath: str | Path, mode: ConfigStoreMode):
        starting_config = deepcopy(config)

        def prep_save(model):
            model._enable_tracking = False
            model.restore_starting_values()
        starting_config.sub_models_apply(prep_save)
        prep_save(starting_config)
        
        '''
        if self._load_path:
            logging.info(f'Config was loaded from {self._load_path}, saving skipped.')
            return
        '''

        '''
        # save-load of function, avoid if possible
        if config.eddypro_fo.time_converter:
            if not config.eddypro_fo.time_converter_str:
                config.eddypro_fo.time_converter_str = func_to_str(config.eddypro_fo.time_converter)
            config.eddypro_fo.time_converter = None

        if config.eddypro_biomet.time_converter:
            if not config.eddypro_biomet.time_converter_str:
                config.eddypro_biomet.time_converter_str = func_to_str(config.eddypro_biomet.time_converter)
            config.eddypro_biomet.time_converter = None
        '''
        
        starting_config.store_mode = mode
        cls.save_to_yaml(starting_config, Path(fpath))

    @classmethod
    def load_or_init(cls, load_path: str | Path | None, repo_dir: Path, init_debug: bool, init_version: str, debug_skip_validate=True) -> Self:
        if load_path == 'auto':
            load_path = find_unique_file(Path('.'), '*config*.yaml')

        if not cls._default_model_values:
            FFConfig.load_defaults(repo_dir / DEFAULT_CONFIG)

        if load_path:
            config = cls.load_from_yaml(Path(load_path), validate=debug_skip_validate)            
            _load_path = str(load_path)
        else:
            # config_values = {v for k, v in config.model_dump().items() if not isinstance(v, dict)}
            # assert set(AUTO_PLACEHOLDERS) & config_values == set()
            
            if ENV.LOCAL: 
                init_debug = True
            
            config = cls.model_construct(debug=init_debug, version=init_version)
            _load_path = None

        '''
        # save-load of function, avoid if possible
        if config.eddypro_fo.time_converter_str:
            config.eddypro_fo.time_converter = str_to_func(config.eddypro_fo.time_converter_str)
        if config.eddypro_biomet.time_converter_str:
            config.eddypro_biomet.time_converter = str_to_func(config.eddypro_biomet.time_converter_str)
        '''
        def prep_load(model: cls):
            model._load_path = _load_path
            model._enable_tracking = True
        config.sub_models_apply(prep_load)
        prep_load(config)
        return config


class InputFileConfig(TrackedBaseModel):
    # генерируем новые временные метки в случае ошибок
    repair_time: bool = None
    # заменяем -9999  на np.nan
    missing_data_codes: str | list[str] = None

    # full auto mode may be difficult due to human date and time col names in all the cases (but heuristic?)
    # time_converter: Callable[[Any], Any]
    # TODO 3 str is used to support config save load, but it won't be safe in server mode (UI or Colab ok)
    # time_converter_str: str


class MergedDateTimeFileConfig(InputFileConfig):
    datetime_col: str = None
    try_datetime_formats: str | list[str] = None


class SeparateDateTimeFileConfig(InputFileConfig):
    time_col: str = None
    try_time_formats: str | list[str] = None
    date_col: str = None
    try_date_formats: str | list[str] = None


class RepConfig(TrackedBaseModel):
    is_to_apply_u_star_filtering: bool = None
    ustar_threshold_fallback: float = None
    ustar_rg_source: Annotated[str, 'Rg_th_Py, Rg_th_REP, Rg, ""'] = None
    is_bootstrap_u_star: bool = None
    # TODO 2 add enums?
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


class FiltersConfig(TrackedBaseModel):
    # TODO 1 library which supports all none by default instead of pydantic?
    # TODO 1 auto = initial; changed or not? make this config-wide approach
    meteo: dict = None
    min_max: dict = None
    window: dict = None
    quantile: dict = None
    madhampel: dict = None
    winter_date_ranges: list[tuple[str, str]] = None
    man_ranges: list[tuple[str, str]] = None


# TODO 1 yaml should have comments, will loading them from default config work? in annotation? auto gen from source? toml lib?
# all settings by default, partial mode optional (or commented out?) if not default, comment?
class FFConfig(TrackedConfig):
    # super().version: str
    # super().store_mode: ConfigStoreMode
    debug: bool = None

    # TODO 3 all auto should be in default as non-auto (not to trigger auto on save) and None must be allowed type, not clean
    input_files: str | list[str] | dict[str | Path, InputFileType] = None
    # flexible, but too complicated to edit for user?
    # files: dict[str, InputFileConfig]

    eddypro_fo: SeparateDateTimeFileConfig = SeparateDateTimeFileConfig.model_construct()
    eddypro_biomet: MergedDateTimeFileConfig = MergedDateTimeFileConfig.model_construct()
    # ias: InputFileConfig
    # csf: InputFileConfig
    import_mode: Annotated[ImportMode | None, gen_enum_info(ImportMode)] = None
    # if True will load just a small chunk of data
    time_col: str = None

    # TODO 1 move to ig
    has_meteo: bool = None

    site_name: str = None
    ias_output_version: str = None

    qc: dict = None
    # TODO 1 all nested options will not be tracked or protected, nested starts to be too complex 
    filters: FiltersConfig = FiltersConfig.model_construct()

    calc_nee: bool = None
    calc_with_strg: bool = None
    reddyproc: RepConfig = RepConfig.model_construct()


class RepOutInfo(TrackedBaseModel):
    start_year: int
    end_year: int
    fnames_prefix: str


class FFGlobals(TrackedBaseModel):
    # not yet clear if to include in user config or not
    out_dir: Path
    repo_dir: Path

    points_per_day: int = None

    rep_arc_exclude_files: list[Path] = None
    rep_out_info: RepOutInfo = None
    rep_level3_fpath: Path = None
