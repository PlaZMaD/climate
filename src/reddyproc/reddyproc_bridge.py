from contextlib import contextmanager
from copy import copy
from pathlib import Path
from types import SimpleNamespace
from typing import TextIO

import pandas as pd
import rpy2.robjects as ro
from rpy2.rinterface import ListSexpVector
from rpy2 import rinterface_lib as rl
from rpy2.rinterface_lib.sexp import NULLType
from rpy2.robjects import conversion, default_converter
from rpy2.robjects import pandas2ri
from rpy2.robjects.vectors import FloatMatrix
# will not work under Colab
# from rpy2.rlike.container import NamedList

from src.ff_logger import ff_logger
from src.config.ff_config import RepConfig, RepOutInfo


@contextmanager
def capture_r_output(io_file: TextIO):
    # proper file name is not known yet, but expected to be finalized under yield
    
    rc = rl.callbacks
    cb_bkp = rc.consolewrite_print, rc.consolewrite_warnerror, rc.showmessage
    std_print = rc.consolewrite_print
    
    rc.consolewrite_print = lambda msg: (io_file.write(msg), std_print(msg))
    rc.consolewrite_warnerror = lambda msg: (io_file.write(msg), std_print(msg))
    rc.showmessage = lambda msg: (io_file.write(msg), std_print(msg))
    
    try:
        yield
    finally:
        (rc.consolewrite_print, rc.consolewrite_warnerror, rc.showmessage) = cb_bkp

'''
def rpy2_namedlist_to_py_simplenamespace(x: NamedList):
    dc = {str(k).replace('.', '_'): v for k, v in zip(x.names(), x)}
    return SimpleNamespace(**dc)
'''


def rpy2_listvector_to_py_simplenamespace(x: ro.ListVector):
    return SimpleNamespace(**{k: v for k, v in zip(x.names, x)})


def rpy2_floatvector_to_pd_dataframe(obj: FloatMatrix):
    # conversions don't work properly
    x = pandas2ri.rpy2py(obj)    
    # return pd.DataFrame(x, index=rownames, columns=list(obj.colnames))
    return pd.DataFrame(x, columns=list(obj.colnames))


def ff_rpy2_converter():
    cnv = conversion.Converter("FF helper converter")
    
    cnv.py2rpy.register(type(None), lambda _: ro.r("NULL"))
    
    cnv.rpy2py.register(NULLType, lambda _: None)
    # cnv.rpy2py.register(NamedList, rpy2_namedlist_to_py_simplenamespace)
    cnv.rpy2py.register(ro.StrVector, lambda x: x[0])    
    cnv.rpy2py.register(FloatMatrix, rpy2_floatvector_to_pd_dataframe)
    cnv.rpy2py.register(ro.ListVector, rpy2_listvector_to_py_simplenamespace)
    
    # order matters and brakes either lists, either dfs 
    # return conversion.localconverter(default_converter + cnv)
    return conversion.localconverter(pandas2ri.converter + default_converter + cnv)


def reddyproc_and_postprocess(rep_cfg: RepConfig, repo_dir: Path):
    cfg_vars = copy(vars(rep_cfg))
    cfg_vars['partitioning_methods'] = ro.StrVector(rep_cfg.partitioning_methods)
    with ff_rpy2_converter():
        rep_options = ro.ListVector(cfg_vars)
    
    err_prefix = 'error'
    draft_log_name = Path(rep_cfg.output_dir) / (err_prefix + rep_cfg.log_fname_end)
    
    with open(draft_log_name, 'w') as f, capture_r_output(f):
        warpper_fpath = repo_dir / 'src/reddyproc/reddyproc_wrapper.r'
        ro.r(f'repo_dir <- "{repo_dir}"')
        ro.r.source(str(warpper_fpath))
        func_run_web_tool = ro.globalenv['reddyproc_and_postprocess']
        
        rpy2_res = func_run_web_tool(user_options=rep_options)
        with ff_rpy2_converter():
            # works only partially, not in nested cases
            # manual extraction workaround: rpy2_res.rx2['bootstrap_values']
            py_res = conversion.rpy2py(rpy2_res)
            py_res.changed_config = conversion.rpy2py(py_res.changed_config)
            py_res.out_prefix = conversion.rpy2py(py_res.out_prefix)
            py_res.info = conversion.rpy2py(py_res.info)
            
        roi = RepOutInfo(
            # workaround due to . in name
            start_year=int(py_res.info.__dict__['Y.START'][0]),
            end_year=int(py_res.info.__dict__['Y.END'][0]),
            fnames_prefix=py_res.out_prefix,
        )
    
    changed_config = py_res.changed_config
    if changed_config:
        changed_ustar = changed_config.isToApplyUStarFiltering[0]
        if changed_ustar != rep_cfg.is_to_apply_u_star_filtering:
            ff_logger.warning('REddyProc fallback on isToApplyUStarFiltering is detected and propagated.')
            rep_cfg.is_to_apply_u_star_filtering = changed_ustar
    
    new_path = draft_log_name.parent / draft_log_name.name.replace(err_prefix, roi.fnames_prefix)
    draft_log_name.rename(new_path)
    
    return roi, rep_cfg
