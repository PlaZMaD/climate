from pathlib import Path
from typing import Optional, Type, Any, Tuple
from copy import deepcopy

from pydantic import BaseModel, ConfigDict, create_model
from pydantic.fields import FieldInfo
from ruamel.yaml import YAML, CommentedSeq


def partial_model(model: Type[BaseModel]):
    def make_field_optional(field: FieldInfo, default: Any = None) -> Tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new
    return create_model(
        f'Partial{model.__name__}',
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.__fields__.items()
        }
    )


class ValidatedBaseModel(BaseModel):
    def __dir__(self):
        # hide [model_computed_fields, model_config, model_extra] from debugger
        return [k for k in super().__dir__() if not k.startswith('model_')]

    model_config = ConfigDict(validate_assignment=True)


def load_basemodel(fpath, load_model_class: type[ValidatedBaseModel]):
    with open(fpath, 'r') as fl:
        yaml = YAML().load(fl)
    return load_model_class.model_validate(yaml)


def inline_short_lists(data, max_len=2):
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = inline_short_lists(v, max_len)
    elif isinstance(data, list):
        if len(data) <= max_len and all(not isinstance(i, (dict, list)) for i in data):
            seq = CommentedSeq(data)
            seq.fa.set_flow_style()
            return seq
        return [inline_short_lists(i, max_len) for i in data]
    return data


def save_basemodel(fpath: Path, config: ValidatedBaseModel) -> None:
    config_json = config.model_dump(mode='json')

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=4, sequence=4, offset=4)

    config_yaml = inline_short_lists(config_json, max_len=2)

    with open(fpath, "w") as fl:
        yaml.dump(config_yaml, fl)

