from src.ipynb_globals import *
from types import SimpleNamespace
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
import src.ipynb_globals as ig
from src.helpers.io_helpers import ensure_empty_dir

ig.eddyproc = SimpleNamespace()
ig.eddyproc.options = SimpleNamespace(
    site_id=ias_output_prefix,

    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # default REP detects nights by Rg; when Rg is missing, this is experimental fallback to apply uStar over all data
    ustar_allowed_on_days=True,

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

    # other values may not work
    u_star_method="RTw",
    is_bootstrap_u_star=False,
    is_to_apply_gap_filling=True,
    input_file=f"output/{reddyproc_filename}",
    output_dir="output/reddyproc",
    log_fname_end='_log.txt'
)

ensure_empty_dir(ig.eddyproc.options.output_dir)
ig.eddyproc.out_info, ig.eddyproc.options = reddyproc_and_postprocess(ig.eddyproc.options)
