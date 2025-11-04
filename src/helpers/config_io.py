import logging
from copy import copy
from pathlib import Path
from typing import Self, Any, Annotated
from pydantic import BaseModel, ConfigDict, model_serializer, Field
from ruamel.yaml import CommentedSeq, CommentedMap, YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

from src.helpers.env_helpers import ENV
from src.helpers.io_helpers import find_unique_file

# TODO 1 +.toml vs ?.py (vs .yaml)?
# comments io support, import defaults, diff export, time conversion function vs safety 

METADATA_KEY = '_meta_description'


def dict_to_yaml_with_comments(d: dict) -> CommentedMap:
    d = CommentedMap(d)
    if METADATA_KEY in d:
        meta = d[METADATA_KEY]
        del d[METADATA_KEY]
        for k, v in meta.items():
            eol = []  # or smth else
            if 'desc' in v:
                eol += [v['desc']]
            comment = ' # '.join(eol)
            d.yaml_add_eol_comment(key=k, comment=comment)
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
        return res
    
    if isinstance(x, list):
        types = {type(v) for v in x}
        if types <= {str, int, float}:  # and len(x) <= max_len
            res = CommentedSeq(x)
            res.fa.set_flow_style()
        else:
            res = [config_to_yaml(i, path + [str(x)], max_len) for i in x]
        return res

    if isinstance(x, str):
        return SingleQuotedScalarString(x)
    
    return x


def copy_comments(src_x, tgt_x):
    """ Nested comments transfer """
        
    if isinstance(tgt_x, CommentedMap):
        tgt_x.ca.items.update(src_x.ca.items)

        v_types = {type(v) for v in tgt_x.values()}
        if v_types <= {str, int, float}:
            pass
        else:            
            for k in tgt_x.keys():
                if k in src_x.keys():
                    _, tgt_x[k] = copy_comments(src_x[k], tgt_x[k])
        return src_x, tgt_x
    
    return src_x, tgt_x


class AnnotatedBaseModel(BaseModel):
    def model_post_init(self, __context: Any) -> None:
        # Annotated[*, ["info"]] -> Annotated[*, {'desc': "info"}]
        for k, v in self.model_fields.items():
            if v.metadata and isinstance(v.metadata, list):
                self.model_fields[k].metadata = {'desc': v.metadata[0]}
    
    @model_serializer(mode="wrap")
    def include_field_meta(self, nxt):
        """ required to generate yaml comments from annotations """
        res = nxt(self)
        
        assert METADATA_KEY not in self
        config_meta = {k: v.metadata for k, v in self.model_fields.items() if v.metadata}
        if len(config_meta) > 0:
            res[METADATA_KEY] = config_meta
        return res


class FFBaseModel(AnnotatedBaseModel):
    # pydantic basemodel options
    model_config = ConfigDict(validate_assignment=True, revalidate_instances="always", use_attribute_docstrings=True)


class BaseConfig(FFBaseModel):
    # TODO 1 bool vs Annotated[bool, Field(exclude=True)] = None
    from_file: Annotated[bool, Field(exclude=True)] = None
    default_path: Annotated[Path, Field(exclude=True)] = None
    
    @classmethod
    def get_yaml(cls) -> YAML:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        yaml.indent(mapping=4, sequence=4, offset=4)
        return yaml
    
    @classmethod
    def load_from_yaml(cls, fpath: Path, return_model=True):
        with open(fpath, 'r') as fl:
            yaml = cls.get_yaml()
            loaded_yaml = yaml.load(fl)
        
        model = cls.model_validate(loaded_yaml)
        if return_model:
            return model
        else:
            return loaded_yaml
    
    @classmethod
    def save_to_yaml(cls, config: BaseModel, fpath: Path):
        save_dict = config.model_dump(mode='json')                
        config_yaml = config_to_yaml(save_dict, path=[])
        
        default_config = cls.load_from_yaml(config.default_path, return_model=False)
        _, config_yaml = copy_comments(default_config, config_yaml)
        
        with open(fpath, "w") as fl:
            yaml = cls.get_yaml()            
            yaml.dump(config_yaml, fl)
    
    @classmethod
    def save(cls: Self, config, fpath: str | Path):
        # TODO 1 hardcoded temp fix, restore auto options in some better way
        config_auto = copy(config)
        config_auto.input_files = 'auto'
        config_auto.import_mode = 'AUTO'
        config_auto.site_name = 'auto'
        config_auto.ias_out_version = 'auto'
        config_auto.reddyproc.site_id = ''
        config_auto.reddyproc.input_file = ''
        
        cls.save_to_yaml(config_auto, Path(fpath))
    
    @classmethod
    def load_or_init(cls, load_path: str | Path | None, default_path: Path, init_debug: bool, init_version: str) -> Self:
        if load_path == 'auto':
            load_path = find_unique_file(Path('.'), '*config*.yaml')
        
        if load_path:
            config = cls.load_from_yaml(Path(load_path))
            if config.version != init_version:
                raise NotImplementedError(f'Current config version: {init_version} does not match loaded version: {config.version}. \n'
                                          'Backwards compatibility is planned to be implemented soon. \n'
                                          'For now, please update config fields manually to match default exported config.')
            config.from_file = True
        else:
            '''
            if ENV.LOCAL:
                logging.warning('\n Debug mode enabled in local ENV. \n')
                init_debug = True
            '''
            
            config = cls.model_construct(debug=init_debug, version=init_version)
            config.from_file = False
        
        assert default_path.exists()
        config.default_path = default_path
        
        return config
