from contextlib import contextmanager
from io import TextIOWrapper
from pathlib import Path
from types import SimpleNamespace
from warnings import warn

import rpy2.robjects as ro
from rpy2 import rinterface_lib as rl


@contextmanager
def capture_r_output(file: TextIOWrapper):
    # proper file name is not known yet, but expected to be finalized under yield

    rc = rl.callbacks
    cb_bkp = rc.consolewrite_print, rc.consolewrite_warnerror, rc.showmessage
    std_print = rc.consolewrite_print

    rc.consolewrite_print = lambda msg: (file.write(msg), std_print(msg))
    rc.consolewrite_warnerror = lambda msg: (file.write(msg), std_print(msg))
    rc.showmessage = lambda msg: (file.write(msg), std_print(msg))

    try:
        yield
    finally:
        (rc.consolewrite_print, rc.consolewrite_warnerror, rc.showmessage) = cb_bkp


def reddyproc_and_postprocess(options):
    py_options_fix = options
    py_options_fix.partitioning_methods = ro.StrVector(options.partitioning_methods)
    r_options = ro.ListVector(vars(py_options_fix))

    err_prefix = 'error'
    draft_log_name = Path(options.output_dir) / (err_prefix + options.log_fname_end)

    with open(draft_log_name, 'w') as f, capture_r_output(f):
        ro.r.source('src/reddyproc/reddyproc_wrapper.r')
        func_run_web_tool = ro.globalenv['reddyproc_and_postprocess']

        r_res = func_run_web_tool(user_options=r_options)
        res = SimpleNamespace(
            start_year=int(r_res.rx2['info'].rx2['Y.START'][0]),
            end_year=int(r_res.rx2['info'].rx2['Y.END'][0]),
            fnames_prefix=r_res.rx2['out_prefix'][0]
        )

    changed_config = r_res.rx2['changed_config']
    if changed_config:
        changed_ustar = changed_config.rx2['isToApplyUStarFiltering'][0]
        if changed_ustar != options.is_to_apply_u_star_filtering:
            warn('REddyProc fallback on isToApplyUStarFiltering is detected and propagated.')
            options.is_to_apply_u_star_filtering = changed_ustar

    new_path = draft_log_name.parent / draft_log_name.name.replace(err_prefix, res.fnames_prefix)
    draft_log_name.rename(new_path)

    return res
