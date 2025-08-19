from pathlib import Path

from pydantic import BaseModel, ConfigDict
from ruamel.yaml import YAML, CommentedSeq, CommentedMap


class ValidatedBaseModel(BaseModel):
    def __dir__(self):
        # hide [model_computed_fields, model_config, model_extra] from debugger
        return [k for k in super().__dir__() if not k.startswith('model_')]

    model_config = ConfigDict(validate_assignment=True)


def load_basemodel(fpath, load_model_class: type[ValidatedBaseModel]):
    with open(fpath, 'r') as fl:
        yaml = YAML().load(fl)
    return load_model_class.model_validate(yaml)


def inline_short_lists(data, depth, max_len=5):
    if isinstance(data, dict):
        v_types = {type(v) for v in data.values()}
        if v_types <= {str, int, float} and depth > 1:
            map_ = CommentedMap(data)
            map_.fa.set_flow_style()
            return map_
        else:
            return {k: inline_short_lists(v, depth + 1, max_len) for k, v in data.items()}
    elif isinstance(data, list):
        types = {type(v) for v in data}
        if len(data) <= max_len and types <= {str, int, float}:
            seq = CommentedSeq(data)
            seq.fa.set_flow_style()
            return seq
        else:
            return [inline_short_lists(i, depth + 1, max_len) for i in data]
    else:
        return data


def save_basemodel(fpath: Path, config: ValidatedBaseModel) -> None:
    config_json = config.model_dump(mode='json')

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=4, sequence=4, offset=4)

    config_yaml = inline_short_lists(config_json, max_len=2, depth=0)

    with open(fpath, "w") as fl:
        yaml.dump(config_yaml, fl)
