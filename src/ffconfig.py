from pathlib import Path

from pydantic import BaseModel, PositiveInt
from typing import Callable, Any

from src.data_io.data_import_modes import ImportMode, InputFileType


class CleanBaseModel(BaseModel):
    def __dir__(self):
        # hide [model_computed_fields, model_config, model_extra] from debugger
        return [k for k in super().__dir__() if not k.startswith('model_')]


class InputFileConfig(CleanBaseModel):
    # генерируем новые временные метки в случае ошибок
    repair_time: bool = True
    # заменяем -9999  на np.nan
    missing_data_codes: str | list[str] = ['-9999']
    time_col: str = 'datetime'

    # full auto mode may be difficult due to human date and time col names in all the cases (but heuristic?)
    time_converter: Callable[[Any], Any] = None


class FFConfig(CleanBaseModel):
    input_files: str | list[str] | dict[str | Path, InputFileType] = 'auto'
    # flexible, but too complicated to edit for user?
    # files: dict[str, InputFileConfig]

    eddypro_fo: InputFileConfig = InputFileConfig()
    eddypro_biomet: InputFileConfig = InputFileConfig()
    # ias: InputFileConfig
    # csf: InputFileConfig

    site_name: str = 'auto'
    ias_output_version: str = 'auto'

    has_meteo: bool | None = None

    # options not for ipynb:

    # if True will load just a small chunk of data
    debug: bool = False
    import_mode: ImportMode = ImportMode.AUTO
