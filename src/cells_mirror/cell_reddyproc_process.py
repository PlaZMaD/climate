from src.ipynb_globals import *
from types import SimpleNamespace
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
import src.ipynb_globals as ig
from src.helpers.io_helpers import ensure_empty_dir
from src.reddyproc.preprocess_rg import prepare_rg

ig.eddyproc = SimpleNamespace()
ig.eddyproc.options = SimpleNamespace(
    site_id=ias_output_prefix,

    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # "Rg_th_Py", "Rg_th_REP" - estimate by theoretical algs,
    # "Rg" - by real data, "" - ignore Rg and filter both days and nights
    ustar_rg_source="Rg",
    is_bootstrap_u_star=False,
    # u_star_seasoning: one of "WithinYear", "Continuous", "User"
    u_star_seasoning="Continuous",

    is_to_apply_partitioning=True,
    # partitioning_methods: one or both of "Reichstein05", "Lasslop10"
    partitioning_methods=["Reichstein05", "Lasslop10"],

    latitude=64.2,
    longitude=100,
    timezone=+7,

    # "Tsoil"
    temperature_data_variable="Tair",

    # do not change
    u_star_method="RTw",
    is_to_apply_gap_filling=True,
    input_file=f"output/{reddyproc_filename}",
    output_dir="output/reddyproc",
    log_fname_end='_log.txt'
)

prepare_rg(ig.eddyproc.options)
ensure_empty_dir(ig.eddyproc.options.output_dir)
ig.eddyproc.out_info, ig.eddyproc.options = reddyproc_and_postprocess(ig.eddyproc.options)
