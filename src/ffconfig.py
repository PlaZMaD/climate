import logging
from enum import Enum
from pathlib import Path
from typing import Annotated

from src.data_io.data_import_modes import ImportMode, InputFileType
from src.helpers.config_io import ValidatedBaseModel, ConfigStoreMode, ConfigModel
from src.helpers.py_helpers import gen_enum_info, ensure_list, is_protected_method

AUTO_VALUES = ['auto', ImportMode.AUTO]
DEFAULT_CONFIG = 'misc/default_config.yaml'


class TrackedConfig(ConfigModel):
    _load_path: str = None
    _auto_values: dict = {}

    def __setattr__(self, name, new_value):
        if is_protected_method(name):
            super().__setattr__(name, new_value)
        
        cur_value = getattr(self, name)

        if self._load_path and cur_value not in AUTO_VALUES and cur_value != new_value:
            logging.warning(f"Option for **{name}** in ipynb does not match option in configuration file: \n"
                            f"ipynb (skipped): {new_value} \n"
                            f"config (used): {cur_value}")
            return

        if cur_value != new_value and cur_value in AUTO_VALUES:
            self._auto_values |= {name: cur_value}

        super().__setattr__(name, new_value)

    def restore_auto_values(self):
        if len(self._auto_values) > 0:
            logging.debug(f'Auto values summary: {self._auto_values}')
        for k, v in self._auto_values.items():
            prev = vars(self)[k]
            if isinstance(prev, Enum):
                prev = prev.value

            if not self.model_fields[k].metadata:
                self.model_fields[k].metadata = {}
            self.model_fields[k].metadata |= {'dynamic value': prev}
            vars(self)[k] = v

    def save(self, fpath: str | Path, mode: ConfigStoreMode):
        self.restore_auto_values()
        self.store_mode = mode

        if self._load_path:
            logging.info(f'Config was loaded from {self._load_path}, saving skipped.')
            return

        '''
        # save-load of function, avoid if possible (switch to auto type conversion if required?)
        if config.eddypro_fo.time_converter:
            if not config.eddypro_fo.time_converter_str:
                config.eddypro_fo.time_converter_str = func_to_str(config.eddypro_fo.time_converter)
            config.eddypro_fo.time_converter = None
    
        if config.eddypro_biomet.time_converter:
            if not config.eddypro_biomet.time_converter_str:
                config.eddypro_biomet.time_converter_str = func_to_str(config.eddypro_biomet.time_converter)
            config.eddypro_biomet.time_converter = None
        '''

        super().save_to_yaml(Path(fpath))

    @classmethod
    def load(cls, fpath: str | Path | None, repo_dir: Path):
        if fpath == 'auto':
            matches = list(Path(repo_dir).glob('*.yaml'))
            if len(matches) > 1:
                msg_matches = ensure_list(matches, transform_func=str)
                raise Exception(f'Found more than 2 configs: {msg_matches} '
                                'remove excessive or specify config name to load instead of auto.')
            elif len(matches) == 1:
                fpath = matches[0]
            elif len(matches) == 0:
                fpath = None

        if fpath:
            config: cls = cls.load_from_yaml(Path(fpath), default_fpath=repo_dir / DEFAULT_CONFIG)
            config._load_path = str(fpath)
        else:
            config: cls = cls.load_from_yaml(fpath=None, default_fpath=repo_dir / DEFAULT_CONFIG)
            config._load_path = None

        '''
        # save-load of function, avoid if possible (switch to auto type conversion if required?)
        if config.eddypro_fo.time_converter_str:
            config.eddypro_fo.time_converter = str_to_func(config.eddypro_fo.time_converter_str)
        if config.eddypro_biomet.time_converter_str:
            config.eddypro_biomet.time_converter = str_to_func(config.eddypro_biomet.time_converter_str)
        '''

        return config


class InputFileConfig(ValidatedBaseModel):
    # генерируем новые временные метки в случае ошибок
    repair_time: bool = True
    # заменяем -9999  на np.nan
    missing_data_codes: str | list[str] = ['-9999']

    # full auto mode may be difficult due to human date and time col names in all the cases (but heuristic?)
    # time_converter: Callable[[Any], Any] | None = None
    # TODO 3 str is used to support config save load, but it won't be safe in server mode (UI or Colab ok)
    # time_converter_str: str | None = None

    time_col: str | None = None
    try_time_formats: str | list[str] | None = None
    date_col: str | None = None
    try_date_formats: str | list[str] | None = None
    datetime_col: str | None = None
    try_datetime_formats: str | list[str] | None = None


class RepConfig(ValidatedBaseModel):
    site_id: str = None

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

    u_star_method: str = 'RTw'
    is_to_apply_gap_filling: bool = True
    input_file: str = None
    output_dir: str = None
    log_fname_end: str = '_log.txt'


class FiltersConfig(ValidatedBaseModel):
    meteo: dict = {}
    quantile: dict = {}
    madhampel: dict = {}
    window: dict = {}
    min_max: dict = {}
    man_ranges: list[tuple[str, str]] = []


# TODO 1 yaml should have comments, will loading them from default config work? in annotation? auto gen from source? toml lib?
# all settings by default, partial mode optional (or commented out?) if not default, comment?
class FFConfig(TrackedConfig):
    # TODO 3 auto read (from env?) in FluxFilter.py
    version: str

    input_files: str | list[str] | dict[str | Path, InputFileType] = 'auto'
    # flexible, but too complicated to edit for user?
    # files: dict[str, InputFileConfig]

    eddypro_fo: InputFileConfig = InputFileConfig()
    eddypro_biomet: InputFileConfig = InputFileConfig()
    # ias: InputFileConfig
    # csf: InputFileConfig

    site_name: str = 'auto'
    ias_output_version: str = 'auto'

    has_meteo: bool = None
    qc: dict = {}
    filters: FiltersConfig = FiltersConfig()

    calc_nee: bool = None
    calc_with_strg: bool = None
    reddyproc: RepConfig = RepConfig()

    # options not for ipynb:

    # if True will load just a small chunk of data
    time_col: str = 'datetime'
    debug: bool = False

    import_mode: Annotated[ImportMode, gen_enum_info(ImportMode)] = ImportMode.AUTO


class RepOutInfo(ValidatedBaseModel):
    start_year: int
    end_year: int
    fnames_prefix: str


class FFGlobals(ValidatedBaseModel):
    # not yet clear if to include in user config or not
    out_dir: Path
    repo_dir: Path

    points_per_day: int = None

    rep_arc_exclude_files: list[Path] = None
    rep_out_info: RepOutInfo = None
    rep_level3_fpath: Path = None
