from contextlib import contextmanager
from copy import copy
from pathlib import Path
from typing import TextIO

import rpy2.robjects as ro
from rpy2 import rinterface_lib as rl
from rpy2.rinterface_lib.sexp import NULLType
from rpy2.robjects import conversion, default_converter

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


def r_converter():
    none_converter = conversion.Converter("None converter")
    none_converter.py2rpy.register(type(None), lambda _: ro.r("NULL"))
    none_converter.rpy2py.register(NULLType, lambda _: None)
    return conversion.localconverter(default_converter + none_converter)


def reddyproc_and_postprocess(rep_cfg: RepConfig, repo_dir: Path):
    cfg_vars = copy(vars(rep_cfg))
    cfg_vars['partitioning_methods'] = ro.StrVector(rep_cfg.partitioning_methods)
    with r_converter():
        rep_options = ro.ListVector(cfg_vars)
    
    err_prefix = 'error'
    draft_log_name = Path(rep_cfg.output_dir) / (err_prefix + rep_cfg.log_fname_end)
    
    with open(draft_log_name, 'w') as f, capture_r_output(f):
        warpper_fpath = repo_dir / 'src/reddyproc/reddyproc_wrapper.r'
        ro.r(f'repo_dir <- "{repo_dir}"')
        ro.r.source(str(warpper_fpath))
        func_run_web_tool = ro.globalenv['reddyproc_and_postprocess']
        
        r_res = func_run_web_tool(user_options=rep_options)
        roi = RepOutInfo(
            start_year=int(r_res.rx2['info'].rx2['Y.START'][0]),
            end_year=int(r_res.rx2['info'].rx2['Y.END'][0]),
            fnames_prefix=r_res.rx2['out_prefix'][0]
        )
    
    changed_config = r_res.rx2['changed_config']
    if changed_config:
        changed_ustar = changed_config.rx2['isToApplyUStarFiltering'][0]
        if changed_ustar != rep_cfg.is_to_apply_u_star_filtering:
            ff_logger.warning('REddyProc fallback on isToApplyUStarFiltering is detected and propagated.')
            rep_cfg.is_to_apply_u_star_filtering = changed_ustar
    
    new_path = draft_log_name.parent / draft_log_name.name.replace(err_prefix, roi.fnames_prefix)
    draft_log_name.rename(new_path)
    
    return roi, rep_cfg
