import logging
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any, Annotated, ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_serializer
from ruamel.yaml import YAML, CommentedSeq, CommentedMap

from src.helpers.py_helpers import dict_remove_matches, dict_replace, gen_enum_info, is_protected_method
from src.data_io.data_import_modes import ImportMode

AUTO_PLACEHOLDERS = ['auto', ImportMode.AUTO]
METADATA_KEY = '_meta_description'
DYNAMIC_VALUES_KEY = 'dynamic_values'


# TODO 1 +.toml vs ?.py (vs .yaml)?
# comments io support, import defaults, diff export, time conversion function vs safety 


class ConfigStoreMode(Enum):
    ALL_OPTIONS = 'ALL_OPTIONS'
    ONLY_CHANGES = 'ONLY_CHANGES'


def dict_to_yaml_with_comments(d: dict) -> CommentedMap:
    d = CommentedMap(d)
    if METADATA_KEY in d:
        meta = d[METADATA_KEY]
        del d[METADATA_KEY]
        for k, v in meta.items():
            eol = []
            if DYNAMIC_VALUES_KEY in v:
                eol += ['dynamic: ' + str(v[DYNAMIC_VALUES_KEY])]

            if 'desc' in v:
                eol += [v['desc']]

            d.yaml_add_eol_comment(comment=' # '.join(eol), key=k)
    return d


def config_to_yaml(x, path, max_len=5):
    """ Nested metadata processing and improves yaml items wrapping """

    if isinstance(x, dict):
        res = dict_to_yaml_with_comments(x)

        v_types = {type(v) for v in res.values()}
        if v_types <= {str, int, float} and len(path) > 1:
            res.fa.set_flow_style()
        else:
            for k, v in res.items():
                res[k] = config_to_yaml(v, path + [str(k)], max_len)
    elif isinstance(x, list):
        types = {type(v) for v in x}
        if types <= {str, int, float}:  # and len(x) <= max_len
            res = CommentedSeq(x)
            res.fa.set_flow_style()
        else:
            res = [config_to_yaml(i, path + [str(x)], max_len) for i in x]
    else:
        res = x

    return res


class TrackedBaseModel(BaseModel):
    """ 
    tracks first value and if first not equal to consequent, adds to _starting_values
    not solid, but close to only option when config is set and used in multiple places 
    """
    
    # def __dir__(self):
    #     # hide [model_computed_fields, model_config, model_extra] from debugger
    #     return [k for k in super().__dir__() if not k.startswith('model_')]

    # pydantic basemodel options
    model_config = ConfigDict(validate_assignment=True, revalidate_instances="always")  # , arbitrary_types_allowed=True

    _load_path: str = None
    _starting_values: dict = {}
    _enable_tracking: bool = False

    def model_post_init(self, __context: Any) -> None:
        # Annotated[*, ["info"]] -> Annotated[*, {'desc': "info"}]
        for k, v in self.model_fields.items():
            if v.metadata and isinstance(v.metadata, list):
                self.model_fields[k].metadata = {'desc': v.metadata[0]}

    def __setattr__(self, name, new_value):        
        if is_protected_method(name) or not self._enable_tracking or isinstance(new_value, TrackedBaseModel):
            return super().__setattr__(name, new_value)

        cur_value = getattr(self, name)
        cur_is_auto = str(cur_value).lower() == 'auto'

        if self._load_path and not cur_is_auto and cur_value != new_value:
            logging.warning(f"Option for **{name}** in ipynb does not match option in configuration file: \n"
                            f"ipynb (skipped): {new_value} \n"
                            f"config (used): {cur_value}")
            return

        if cur_value is not None and cur_value != new_value:
            self._starting_values |= {name: cur_value}

        super().__setattr__(name, new_value)
        
    def restore_starting_values(self):
        if len(self._starting_values) > 0:
            logging.debug(f'Summary on config values changed dynamically: {self._starting_values}')

        for k, v in self._starting_values.items():
            prev = vars(self)[k]
            if isinstance(prev, Enum):
                prev = prev.value

            # TODO 1 model_fields should not be acessed from the instance?
            if not self.model_fields[k].metadata:
                self.model_fields[k].metadata = {}
            self.model_fields[k].metadata |= {DYNAMIC_VALUES_KEY: prev}
            vars(self)[k] = v

    @model_serializer(mode="wrap")
    def include_field_meta(self, nxt):
        """ required to generate yaml comments from annotations """
        res = nxt(self)

        assert METADATA_KEY not in self
        config_meta = {k: v.metadata for k, v in self.model_fields.items() if v.metadata}
        if len(config_meta) > 0:
            res[METADATA_KEY] = config_meta
        return res


class ConfigModel(TrackedBaseModel):
    # TODO 3 auto read (from env?) in FluxFilter.py
    version: str = None

    store_mode: Annotated[ConfigStoreMode, gen_enum_info(ConfigStoreMode)] = ConfigStoreMode.ALL_OPTIONS
    _default_model_values: ClassVar[dict] = None
    _sub_model_names: ClassVar[list] = None

    def get_sub_models(self):
        return [var for var in vars(self) if isinstance(var, TrackedBaseModel)]

    def sub_models_apply(self, func): 
        for model in self.get_sub_models():
            func(model)    

    @classmethod
    def load_defaults(cls, default_fpath):
        """ required to support store_mode=ONLY_CHANGES used on export (remove defaults) and import (add defaults) """
        with open(default_fpath, 'r') as f:
            default_yaml = YAML().load(f)
        cls._default_model_values = default_yaml
        default_instance = cls.model_validate(cls._default_model_values) 
        
        cls._sub_model_names = [k for k,v in cls.model_fields.items() if issubclass(v.annotation, BaseModel)]

    @classmethod
    def load_from_yaml(cls, fpath: Path, validate: bool):
        with open(fpath, 'r') as fl:
            loaded_yaml = YAML().load(fl)

        if 'store_mode' in loaded_yaml and loaded_yaml['store_mode'] == ConfigStoreMode.ONLY_CHANGES.value:            
            # TODO 1 version and store_mode should be managed separately? check analysis answer          
            full_yaml = deepcopy(cls._default_model_values)
            for model_name in cls._sub_model_names:
                if model_name in loaded_yaml:
                    dict_replace(full_yaml[model_name], loaded_yaml[model_name], skip_keys=[])
            dict_replace(full_yaml, loaded_yaml, skip_keys=cls._sub_model_names)

            # TODO 1 no need for nested?
            # TODO_test = cls._default_model_values.model_copy(update=loaded_yaml, deep=True)
            # assert cls.model_validate(loaded_yaml) == TODO_test
        else:
            full_yaml = loaded_yaml

        return cls.model_validate(full_yaml) if validate else cls.model_construct(**full_yaml)

    @classmethod
    def save_to_yaml(cls, config, fpath: Path):
        save_dict = config.model_dump(mode='json')
        
        if config.store_mode == ConfigStoreMode.ONLY_CHANGES:
            for model_name in cls._sub_model_names:
                dict_remove_matches(save_dict[model_name], cls._default_model_values[model_name], keep_keys=[])
            dict_remove_matches(save_dict, cls._default_model_values, keep_keys=cls._sub_model_names + ['version'])            

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(mapping=4, sequence=4, offset=4)

        config_yaml = config_to_yaml(save_dict, path=[])

        with open(fpath, "w") as fl:
            yaml.dump(config_yaml, fl)
