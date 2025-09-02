from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer
from ruamel.yaml import YAML, CommentedSeq, CommentedMap

METADATA_KEY = 'meta_description'


class ValidatedBaseModel(BaseModel):
    # def __dir__(self):
    #     # hide [model_computed_fields, model_config, model_extra] from debugger
    #     return [k for k in super().__dir__() if not k.startswith('model_')]

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


def load_basemodel(fpath, load_model_class: type[ValidatedBaseModel]):
    with open(fpath, 'r') as fl:
        yaml = YAML().load(fl)
    return load_model_class.model_validate(yaml)


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
        if types <= {str, int, float}: # and len(x) <= max_len
            res = CommentedSeq(x)
            res.fa.set_flow_style()
        else:
            res = [config_to_yaml(i, path + [str(x)], max_len) for i in x]
    else:
        res = x

    return res


def save_basemodel(fpath: Path, config: ValidatedBaseModel) -> None:
    config_dict = config.model_dump(mode='json')

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=4, sequence=4, offset=4)

    config_yaml = config_to_yaml(config_dict, path=[])

    with open(fpath, "w") as fl:
        yaml.dump(config_yaml, fl)
    pass
