from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any, Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, model_serializer
from ruamel.yaml import YAML, CommentedSeq, CommentedMap

from src.helpers.py_helpers import gen_enum_info, nested_dict_remove_same, nested_dict_replace

METADATA_KEY = 'meta_description'


class ConfigStoreMode(Enum):
    ALL_OPTIONS = 'ALL_OPTIONS'
    ONLY_CHANGES = 'ONLY_CHANGES'


def add_yaml_metadata(d: dict) -> CommentedMap:
    d = CommentedMap(d)
    if METADATA_KEY in d:
        meta = d[METADATA_KEY]
        d[METADATA_KEY] = None
        for k, v in meta.items():
            eol = []
            if 'dynamic value' in v:
                eol += ['last: ' + str(v['dynamic value'])]

            if 'desc' in v:
                eol += [v['desc']]

            d.yaml_add_eol_comment(comment=' # '.join(eol), key=k)
    return d


def config_to_yaml(x, path, max_len=5):
    """ Nested metadata processing and improves yaml items wrapping """

    if isinstance(x, dict):
        res = add_yaml_metadata(x)

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


class ValidatedBaseModel(BaseModel):
    # def __dir__(self):
    #     # hide [model_computed_fields, model_config, model_extra] from debugger
    #     return [k for k in super().__dir__() if not k.startswith('model_')]

    # pydantic basemodel options
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    def model_post_init(self, __context: Any) -> None:
        # Annotated[*, ["info"]] -> Annotated[*, {'desc': "info"}]
        for k, v in self.model_fields.items():
            if v.metadata and isinstance(v.metadata, list):
                self.model_fields[k].metadata = {'desc': v.metadata[0]}

    @model_serializer(mode="wrap")
    def include_field_meta(self, nxt):
        res = nxt(self)

        assert METADATA_KEY not in self
        config_meta = {k: v.metadata for k, v in self.model_fields.items() if v.metadata}
        if len(config_meta) > 0:
            res[METADATA_KEY] = config_meta
        return res


class ConfigModel(ValidatedBaseModel):
    store_mode: Annotated[ConfigStoreMode, gen_enum_info(ConfigStoreMode)] = ConfigStoreMode.ALL_OPTIONS
    _default_model_values: ClassVar[BaseModel]


    @classmethod
    def load_from_yaml(cls, fpath, default_fpath):
        """ default_fpath is required when store_mode=ONLY_CHANGES to set the missing values"""

        with open(default_fpath, 'r') as f:
            default_yaml = YAML().load(f)
        cls._default_model_values: ValidatedBaseModel = cls.model_validate(default_yaml)

        if not fpath:
            return deepcopy(cls._default_model_values)

        with open(fpath, 'r') as fl:
            loaded_yaml = YAML().load(fl)

        if 'store_mode' in loaded_yaml and loaded_yaml['store_mode'] == ConfigStoreMode.ONLY_CHANGES.value:
            nested_dict_replace(default_yaml, loaded_yaml)
            loaded_yaml = default_yaml

        return cls.model_validate(loaded_yaml)

    def save_to_yaml(self, fpath: Path) -> None:
        save_dict = self.model_dump(mode='json')

        if self.store_mode == ConfigStoreMode.ONLY_CHANGES:
            defaults_dict = self._default_model_values.model_dump(mode='json')
            nested_dict_remove_same(save_dict, defaults_dict)

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(mapping=4, sequence=4, offset=4)

        config_yaml = config_to_yaml(save_dict, path=[])

        with open(fpath, "w") as fl:
            yaml.dump(config_yaml, fl)
