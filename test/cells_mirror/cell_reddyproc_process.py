""" Reminder: this is dev-only duplicate of specific ipynb cell, it is out of sync frequently """
from src.helpers.env_helpers import setup_r_env
from test.ipynb_globals import *
from src.ipynb_routines import ipython_enable_word_wrap

# TODO 1 ias: (meeting) split ias check on 1) strict check (instrument) 2) (all -9999 allowed in ipynb)
# TODO 2 ias: test if TIMESTAMP_END is used, add message?

config_reddyproc = RepConfig(    
    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # "Rg_th_Py", "Rg_th_REP" - estimate by theoretical algs,
    # "Rg" - by real data, "" - ignore Rg and filter both days and nights
    # TODO 2 test when fallback activated + (multuyear or bootstrap): if all ok?
    ustar_rg_source="Rg",
    is_bootstrap_u_star=False,
    # u_star_seasoning: one of "WithinYear", "Continuous", "User"
    u_star_seasoning="Continuous",
    
    # TODO 2 rep: (meeting) apply theoretical Rg to REP partitioning
    is_to_apply_partitioning=True,
    
    # partitioning_methods: one or both of "Reichstein05", "Lasslop10"
    partitioning_methods=["Reichstein05", "Lasslop10"],
    
    latitude=56.5,
    longitude=32.6,
    timezone=+3.0,
    
    # "Tsoil"
    temperature_data_variable="Tair",
    
    # do not change
    # TODO 1 ias: (meeting) ias output level2 must be not filtered; 
    site_id=config.metadata.site_name,
    u_star_method="RTw",
    is_to_apply_gap_filling=True,
    input_file=str(gl.rep_level3_fpath),
    output_dir=str(gl.out_dir / 'reddyproc'),
)

if not config.from_file:
    config.reddyproc = config_reddyproc

config.reddyproc.input_file = config_reddyproc.input_file
config.reddyproc.output_dir = config_reddyproc.output_dir
config.reddyproc.site_id = config_reddyproc.site_id

prepare_rg(config.reddyproc)
ensure_empty_dir(config.reddyproc.output_dir)
gl.rep_out_info, config.reddyproc = reddyproc_and_postprocess(config.reddyproc, gl.repo_dir)
