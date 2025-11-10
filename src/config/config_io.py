from copy import copy
from pathlib import Path
from typing import Self, Any, Annotated
from pydantic import BaseModel, ConfigDict, model_serializer, Field
from ruamel.yaml import CommentedSeq, CommentedMap, YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

from src.config.config_versions import update_config_version
from src.helpers.env_helpers import ENV
from src.helpers.io_helpers import find_unique_file

# TODO 1 +.toml vs ?.py (vs .yaml)?
# comments io support, import defaults, diff export, time conversion function vs safety 

METADATA_KEY = '_meta_description'
BASEMODEL_KEY = '_is_basemodel'
CONFIG_GLOB = '*config*.yaml'


def dict_to_yaml_with_comments(d: dict) -> CommentedMap:
    d = CommentedMap(d)
    if METADATA_KEY in d:
        meta = d[METADATA_KEY]
        del d[METADATA_KEY]
        for k, v in meta.items():
            if k == BASEMODEL_KEY:
                continue
            eol = []  # or smth else
            if 'desc' in v:
                eol += [v['desc']]
            comment = ' # '.join(eol)
            d.yaml_add_eol_comment(key=k, comment=comment)
    return d


def config_to_yaml(x, path, basedepth):
    """ Nested metadata processing and improves yaml items wrapping """
    
    if isinstance(x, dict):
        res = dict_to_yaml_with_comments(x)
        is_basemodel = METADATA_KEY in x and BASEMODEL_KEY in x[METADATA_KEY]
        if is_basemodel:
            basedepth = 0
        
        v_types = {type(v) for v in res.values()}
        if basedepth > 0 and v_types <= {str, int, float} and len(path) > 1:
            res.fa.set_flow_style()
        else:
            for k, v in res.items():
                res[k] = config_to_yaml(v, path + [str(k)], basedepth + 1)
        return res
    
    if isinstance(x, list):
        types = {type(v) for v in x}
        if types <= {str, int, float}:  # and len(x) <= max_len
            res = CommentedSeq(x)
            res.fa.set_flow_style()
        else:
            res = [config_to_yaml(i, path + [str(x)], basedepth + 1) for i in x]
        return res

    if isinstance(x, str):
        return SingleQuotedScalarString(x)
    
    return x


def copy_comments(from_el, to_el):
    """ Nested comments transfer """
        
    if isinstance(to_el, CommentedMap):
        to_el.ca.items.update(from_el.ca.items)

        v_types = {type(v) for v in to_el.values()}
        if v_types <= {str, int, float}:
            pass
        else:            
            for k in to_el.keys():
                if k in from_el.keys():
                    _, to_el[k] = copy_comments(from_el[k], to_el[k])
        return from_el, to_el
    
    return from_el, to_el


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
        config_meta[BASEMODEL_KEY] = True
        if len(config_meta) > 0:
            res[METADATA_KEY] = config_meta
        return res


class FFBaseModel(AnnotatedBaseModel):
    # pydantic basemodel options
    model_config = ConfigDict(validate_assignment=True, revalidate_instances="always", use_attribute_docstrings=True)


def preprocess_yaml_text(text: str) -> str:
    fixed_text = text.replace('\t', '    ')
    if fixed_text != text:
        print('Tabs were replaced with spaces in the yaml file.')
    return fixed_text


class BaseConfig(FFBaseModel):
    from_file: Annotated[bool, Field(exclude=True)] = None
    default_fpath: Annotated[Path, Field(exclude=True)] = None
    
    @classmethod
    def get_yaml_io(cls) -> YAML:
        yaml_io = YAML()
        yaml_io.preserve_quotes = True
        yaml_io.default_flow_style = False
        yaml_io.indent(mapping=4, sequence=4, offset=4)
        return yaml_io
    
    @classmethod
    def load_dict_from_yaml(cls, fpath: Path) -> dict:
        yaml_text = fpath.read_text(encoding='utf8')
        yaml_text = preprocess_yaml_text(yaml_text)
        
        yaml_io = cls.get_yaml_io()
        yaml_dict = yaml_io.load(yaml_text)
        return yaml_dict
    
    @classmethod
    def save_to_yaml(cls, config: BaseModel, fpath: Path, add_comments: bool):
        save_dict = config.model_dump(mode='json')                
        cfg_dict = config_to_yaml(save_dict, path=[], basedepth=0)
        
        if add_comments:
            default_cfg_dict = cls.load_dict_from_yaml(config.default_fpath)
            assert cls.model_validate(default_cfg_dict)
            _, cfg_dict = copy_comments(default_cfg_dict, cfg_dict)
        
        with open(fpath, "w") as fl:
            yaml_io = cls.get_yaml_io()            
            yaml_io.dump(cfg_dict, fl)
    
    @classmethod
    def save(cls: Self, config, fpath: str | Path, add_comments: bool):
        # TODO 1 hardcoded temp fix, restore auto options in some better way
        cfg_auto = copy(config)
        cfg_auto.data_import.input_files = 'auto'
        cfg_auto.data_import.import_mode = 'AUTO'
        cfg_auto.metadata.site_name = 'auto'
        cfg_auto.data_export.ias.out_fname_ver_suffix = 'auto'
        cfg_auto.reddyproc.site_id = ''
        cfg_auto.reddyproc.input_file = ''
        
        cls.save_to_yaml(cfg_auto, Path(fpath), add_comments)
        if ENV.LOCAL and add_comments:
            cls.save_to_yaml(cfg_auto, Path(fpath).with_stem(fpath.stem + '_short'), add_comments=False)
    
    @classmethod
    def load_or_init(cls, load_path: str | Path | None, default_fpath: Path, init_debug: bool, init_version: str) -> Self:
        """ load_path: None to force construct a dummy for consequent ipynb fill """
        if load_path == 'auto':
            load_path = find_unique_file(Path('.'), CONFIG_GLOB)
        
        if load_path:
            cfg_dict = cls.load_dict_from_yaml(Path(load_path))
            cfg_dict = update_config_version(cfg_dict, init_version)
            
            cfg_model = cls.model_validate(cfg_dict)            
            
            cfg_model.from_file = True
        else:
            '''
            if ENV.LOCAL:
                logging.warning('\n Debug mode enabled in local ENV. \n')
                init_debug = True
            '''
            
            cfg_model = cls.model_construct(debug=init_debug, version=init_version)
            cfg_model.from_file = False
        
        assert default_fpath.exists()
        cfg_model.default_fpath = default_fpath
        
        return cfg_model
