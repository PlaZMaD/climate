# Reminder: this is duplicate of specific cell used for test purposes, it is outdated or ahead frequently

from src.ipynb_globals import *
from types import SimpleNamespace
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
import src.ipynb_globals as ig
from src.helpers.io_helpers import ensure_empty_dir
from src.reddyproc.preprocess_rg import prepare_rg

ig.rep = SimpleNamespace()
ig.rep.options = SimpleNamespace(
    site_id=ias_output_prefix,

    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # "Rg_th_Py", "Rg_th_REP" - estimate by theoretical algs,
    # "Rg" - by real data, "" - ignore Rg and filter both days and nights
    # TODO 2 when fallback activated + (multuyear or bootstrap): test if all ok?
    ustar_rg_source="Rg",
    is_bootstrap_u_star=False,
    # u_star_seasoning: one of "WithinYear", "Continuous", "User"
    u_star_seasoning="Continuous",

    is_to_apply_partitioning=True,

    # partitioning_methods: one or both of "Reichstein05", "Lasslop10"
    partitioning_methods=["Reichstein05", "Lasslop10"],

    latitude=56.5,
    longitude=32.6,
    timezone=+3.0,

    # "Tsoil"
    temperature_data_variable="Tair",

    # do not change
    u_star_method="RTw",
    is_to_apply_gap_filling=True,
    input_file=str(rep_input_fpath),
    output_dir=str(out_dir / 'reddyproc'),
    log_fname_end='_log.txt'
)

prepare_rg(ig.rep.options)
ensure_empty_dir(ig.rep.options.output_dir)
ig.rep.out_info, ig.rep.options = reddyproc_and_postprocess(ig.rep.options)
