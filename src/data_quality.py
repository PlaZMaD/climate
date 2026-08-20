from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
from plotly import graph_objects as go, express as px

from src.ff_logger import ff_logger
from src.helpers.env_helpers import ENV


class StatsMode(Enum):
    ALL = 'ALL'
    OUTSIDE_2S = 'OUTSIDE_2S'
    SYMMETRIC_2S = 'SYMMETRIC_2S'


# demo data will be binned to this precision
DEMO_SAVE_BINS = 100
# if new data range is larger than the previous, add some extra and then clip
MAX_EXTRA_BINS = 200


def _grow_bins(hist_edges, hist_counts, new_min, new_max, max_extra_bins=MAX_EXTRA_BINS):
    hist_edges = np.asarray(hist_edges, dtype=float)
    hist_counts = np.asarray(hist_counts, dtype=float)
    size = hist_edges[1] - hist_edges[0]
    start, end = hist_edges[0], hist_edges[-1]
    
    add_left = max(0, int(np.ceil((start - new_min) / size))) if new_min < start else 0
    add_right = max(0, int(np.ceil((new_max - end) / size))) if new_max > end else 0
    
    add_left_c = min(add_left, max_extra_bins)
    add_right_c = min(add_right, max_extra_bins)
    clipped = (add_left_c != add_left) or (add_right_c != add_right)
    
    if add_left_c == 0 and add_right_c == 0:
        return hist_edges, hist_counts, clipped
    
    new_start = start - add_left_c * size
    new_n = len(hist_counts) + add_left_c + add_right_c
    new_counts = np.zeros(new_n, dtype=float)
    new_counts[add_left_c:add_left_c + len(hist_counts)] = hist_counts
    new_edges = new_start + size * np.arange(new_n + 1)
    
    return new_edges, new_counts, clipped


def hist_overlay(baseline_edges, baseline_counts, cur_series, col_name, plot_size, opacity=0.5):
    """
    edges_orig, counts_orig: saved demo data histogram
    series_cur: live series to compare against the demo

    Baseline bins are reused or extended about 3x when possible. 
    If new series value range is too large, they are clipped to side bins.
    """
    cur_series = cur_series.dropna().to_numpy(dtype=float)
    if len(cur_series) == 0:
        ff_logger.warning(f'No data in {col_name} to compare against demo data.')
        return
    
    cur_min, cur_max = cur_series.min(), cur_series.max()
    plot_min = min(baseline_edges[0], cur_min)
    plot_max = max(baseline_edges[-1], cur_max)
    if plot_min == cur_min and plot_max == cur_max:
        plot_edges = baseline_edges
        plot_baseline_counts = baseline_counts
        cur_data_clipped = False
    else:    
        plot_edges, plot_baseline_counts, cur_data_clipped = _grow_bins(baseline_edges, baseline_counts, 
                                                                        plot_min, plot_max)
        if cur_data_clipped:
            ff_logger.warning(
                f"[{col_name}] current data range [{cur_min:.4g}, {cur_max:.4g}] exceeds baseline "
                f"range [{baseline_edges[0]:.4g}, {baseline_edges[-1]:.4g}] even after expanding. \n"
                f"Out-of-range values will be clipped into the edge bins."
            )
    
    counts_cur, _ = np.histogram(np.clip(cur_series, plot_edges[0], plot_edges[-1]), bins=plot_edges)
    plot_range = plot_edges[1] - plot_edges[0]
    centers = (plot_edges[:-1] + plot_edges[1:]) / 2
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=centers, y=plot_baseline_counts.astype(int), name='demo', width=plot_range,
                         marker_color=px.colors.qualitative.Plotly[1 % len(px.colors.qualitative.Plotly)],
                         opacity=opacity, showlegend=True))
    fig.add_trace(go.Bar(x=centers, y=counts_cur, name='current', width=plot_range,
                         marker_color=px.colors.qualitative.Plotly[2 % len(px.colors.qualitative.Plotly)],
                         opacity=opacity, showlegend=True))
    
    clip_warning = '' if not cur_data_clipped else ' clipped'
    fig.update_layout(barmode='overlay', title=col_name + clip_warning,
                      xaxis_title="", yaxis_title="", legend_title="",
                      height=plot_size[1], width=plot_size[0], dragmode='pan')
    fig.show(config={'scrollZoom': False, 'toImageButtonOptions': {'filename': col_name}})


def df_to_hist_dict(df_full: pd.DataFrame, bins) -> dict:
    # compresses dataframe to per-column histograms (edges+counts), so they
    # can be persisted and later compared to another station's data without
    # needing the raw values again
    df = df_full.select_dtypes(include='number')
    
    imprint = {}
    for col in df.columns:
        s = df[col].dropna().to_numpy(dtype=float)
        counts, edges = np.histogram(s, bins=bins)
        
        if col in ['air_quality']:
            import matplotlib.pyplot as plt        
            centers = (edges[:-1] + edges[1:]) / 2
            plt.figure()
            plt.bar(centers, counts, width=np.diff(edges), align="edge", edgecolor="black")
            plt.title(col + '_numpy')
            plt.xlabel("Value")
            plt.ylabel("Count")
            plt.show()
        
        imprint[f"{col}__hist"] = counts
        imprint[f"{col}__edges"] = edges
    return imprint


def compare_stats(df_data: pd.DataFrame, show_hists: StatsMode, plot_size, 
                  demo_stats_file: Path, demo_hists_file: Path):
    df_stats = df_data.describe(percentiles=[0.95]).loc[['mean', 'std']]
    
    # df_stats.to_excel(qc_file)
    # df_stats.loc['mean','tau'] = 5
    df_exp_stats = pd.read_excel(demo_stats_file, index_col=0)
    df_merge = df_exp_stats.rename(index={'mean': 'ref_mean', 'std': 'ref_std'}).loc[['ref_mean', 'ref_std']]
    
    df = pd.concat([df_merge, df_stats], axis=0)
    df = df.loc[['ref_mean', 'mean', 'ref_std', 'std']]
    
    cannot_compare = ~df.loc['ref_std'].isna() & df.loc['std'].isna()
    ff_logger.info('Columns in the demo data, but not in processed: \n'
                   f'    {df.columns[cannot_compare].to_list()}')
    
    df.dropna(axis=1, inplace=True)
    mean_diff = np.abs(df.loc['ref_mean'] - df.loc['mean'])
    mask_outside_2s = mean_diff > df.loc['ref_std'] * 2
    mask_outside_both_2s = mean_diff > np.maximum(df.loc['std'], df.loc['ref_std']) * 2
    ff_logger.info('Values with means outside of 2 sigmas of the reference station: \n' +
                   df.loc[:, mask_outside_2s].to_string())
    
    ff_logger.info('Values with means outside of 2 sigmas of both reference and current station: \n' +
                   df.loc[:, mask_outside_both_2s].to_string())
      
    # demo_hist = df_to_hist_dict(df_data, bins=DEMO_SAVE_BINS)
    # np.savez_compressed(DEMO_DATA_HIST, **demo_hist)
    npz = np.load(demo_hists_file)
    
    if show_hists == StatsMode.ALL:
        cols_for_stats = df.columns
    elif show_hists == StatsMode.OUTSIDE_2S:
        cols_for_stats = df.loc[:, mask_outside_2s].columns
    elif show_hists == StatsMode.SYMMETRIC_2S:
        cols_for_stats = df.loc[:, mask_outside_both_2s].columns
    else:
        raise ValueError(f'Unknown comparsion mode: {show_hists}')
    
    for col in cols_for_stats:
        edges_orig = npz[f"{col}__edges"]
        counts_orig = npz[f"{col}__hist"]
        series_cur = df_data[col]
        hist_overlay(edges_orig, counts_orig, series_cur, col, plot_size)
    pass


def try_compare_stats(df: pd.DataFrame, show_hists: StatsMode, plot_size, 
                      demo_stats_file: Path, demo_hists_file: Path):
    try:
        compare_stats(df, show_hists, plot_size, 
                      demo_stats_file, demo_hists_file)
    except:
        print(f'Cannot compare statistics')
        if ENV.LOCAL:
            raise
