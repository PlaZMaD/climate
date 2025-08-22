from copy import deepcopy as copy

import numpy as np
import pandas as pd
import plotly_resampler
from plotly import graph_objects as go, express as px
from plotly.subplots import make_subplots

from bglabutils import basic as bg


def colapse_filters(data, filters_db_in):
    out_filter = {}
    for feature, filters in filters_db_in.items():
        if len(filters) > 0:
            out_filter[feature] = data[filters[0]].astype(int) if len(filters) == 1 else np.logical_and.reduce(
                (data[filters].astype(int)), axis=1).astype(int)
    return out_filter


def get_column_filter(data, filters_db_in, column_name):
    if column_name not in filters_db_in.keys():
        return np.array([1] * len(data.index))
    if len(filters_db_in[column_name]) > 0:
        return colapse_filters(data, filters_db_in)[column_name]
    else:
        return np.array([1] * len(data.index))


def basic_plot(data, col2plot, ias_output_prefix, filters_db=None, min_days=8, window_days=10, steps_per_day=2 * 24, use_resample=False):
    multiplot = isinstance(col2plot, list)

    window_days = window_days  # дней в окне
    min_days = window_days // 2 - 1
    pl_data = data.copy()

    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    color_data = 'darkorange'
    color_line = 'darkslateblue'

    add_color_data = copy(px.colors.qualitative.Pastel1)
    add_color_line = copy(px.colors.qualitative.Prism)

    add_color_data.insert(0, color_data)
    add_color_line.insert(0, color_line)

    fig = go.Figure(layout=layout)
    if multiplot:
        fig = make_subplots(rows=len(col2plot), cols=1, shared_xaxes=True, figure=fig,
                            subplot_titles=[i.upper() for i in col2plot])
    else:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, figure=fig, row_heights=[.8, .2],
                            subplot_titles=[col2plot.upper(), 'Residuals'])

    fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey', minor_ticks='inside',
                     minor_tickcolor='Grey')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey')
    # fig.update_layout(
    #     title = col2plot,
    #     xaxis_tickformat = '%H:%M %d %B <br>%Y'
    # )
    if not multiplot:
        cols = [col2plot]
    else:
        cols = col2plot

    fig.update_layout(
        # title = " ".join(cols),
        xaxis_tickformat='%H:%M %d %B <br>%Y'
    )
    for row, col2plot in enumerate(cols):
        if filters_db is not None:
            filters = get_column_filter(pl_data, filters_db, col2plot)
            pl_data.loc[~filters.astype(bool), col2plot] = np.nan

        if steps_per_day % 2 == 0:
            closed = 'left'
        else:
            closed = 'both'
        rolling_mean = bg.calc_rolling(pl_data[col2plot], step=steps_per_day, rolling_window=window_days,
                                       min_periods=min_days)

        fig.add_trace(go.Scattergl(
            x=pl_data.index, y=pl_data[col2plot], mode='markers', name=col2plot,
            marker_color=add_color_data[row]
        ), row=row + 1, col=1)
        fig.add_trace(go.Scattergl(
            x=rolling_mean.index, y=rolling_mean, mode='lines', name=f'{col2plot} mean {window_days} days',
            opacity=.7, line_color=add_color_line[row]
        ), row=row + 1, col=1)
        if not multiplot:
            fig.add_trace(go.Scattergl(
                x=rolling_mean.index, y=rolling_mean - pl_data[col2plot], mode='lines', name=f'residuals'
            ), row=2, col=1)

    if use_resample:
        fig = plotly_resampler.FigureResampler(fig, default_n_shown_samples=5000)

    fig_name = f"_{int(np.median(pl_data.index.year))}"
    if "ias_output_prefix " in locals() or "ias_output_prefix" in globals():
        fig_name = fig_name + "_" + ias_output_prefix
    fig_config = {'toImageButtonOptions': {'filename': '_'.join(cols) + fig_name, }}
    fig.show(config=fig_config)


def plot_nice_year_hist_plotly(df, to_plot, time_col, filters_db):
    pl_data = df.copy()  # [to_plot]
    # point
    if filters_db is not None:
        print()
        filters = get_column_filter(df, filters_db, to_plot)
        pl_data['filter'] = filters
        pl_data.loc[~filters.astype(bool), to_plot] = np.nan
    # print(pl_data.loc[pd.to_datetime('26 June 2016 1:30'), ['nee', 'nee_nightFilter', 'swin_1_1_1', 'filter']].to_string())
    fig = go.Figure()
    fig.update_layout(title=f'{to_plot}')
    fig.add_trace(go.Heatmap(
        x=pl_data[time_col].dt.date,
        y=pl_data[time_col].dt.hour + 0.5 * (pl_data[time_col].dt.minute // 30),
        z=pl_data[to_plot]
    ))
    fig_config = {'toImageButtonOptions': {'filename': f'{to_plot}_{int(np.median(pl_data.index.year))}', }}

    fig.show(config=fig_config)


def make_filtered_plot(data_pl, col, col2plot, ias_output_prefix, filters_db):
    data = data_pl.copy()
    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    add_color_dot = copy(px.colors.qualitative.Dark24)
    fig = go.Figure(layout=layout)
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey', minor_ticks='inside',
                     minor_tickcolor='Grey')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey')

    data['full_filter'] = get_column_filter(data, filters_db, col)
    data['full_filter'] = data['full_filter'].astype(int)
    pl_data = data.query(f"full_filter==0")
    color_ind = 0
    fig.add_trace(go.Scattergl(
        x=data.query("full_filter==1").index, y=data.query("full_filter==1")[col],
        mode='markers', name="Good data", marker_color=add_color_dot[color_ind]
    ))
    color_ind += 1

    if len(filters_db[col]) > 0:
        for filter_name in filters_db[col]:
            fig.add_trace(go.Scattergl(
                x=pl_data.query(f"{filter_name}==0").index, y=pl_data.query(f"{filter_name}==0")[col],
                mode='markers', name=filter_name, marker_color=add_color_dot[color_ind]
            ))
            color_ind += 1
            pl_data = pl_data.query(f"{filter_name}==1")

    fig.update_layout(
        title=f'{col2plot}',
        xaxis_tickformat='%H:%M %d %B <br>%Y'
    )
    fileName = "basic"
    if "ias_output_prefix " in locals() or "ias_output_prefix" in globals():
        fileName = ias_output_prefix
    fileName += f'_{int(np.median(data.index.year))}_{col}'
    fig_config = {'toImageButtonOptions': {'filename': fileName, }}
    fig.show(config=fig_config)


def plot_albedo(plot_data, filters_db):
    pl_data: pd.DataFrame = plot_data.copy()

    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # TODO 3 may be change cols to pl_data[alb_col]
    # may solve: usage search + navigation, typing hint, case inconsistensy
    # consider units conversions on import when same name
    # consider difference between _1_1_1 instrument code and actual data col

    # TODO QOA 1 ALB_1_1_1 will be used now (check load renames), ok?
    #  V: ALB_1_1_1 have lower priority than calc from ias was not approved by

    # basic.py: def add_albedo(dataT, out_sw, in_sw)

    can_calc = {'swin_1_1_1', 'swout_1_1_1'} <= set(pl_data.columns)
    can_use = 'alb_1_1_1' in pl_data.columns

    if can_calc:
        pl_data['albedo'] = pl_data['swout_1_1_1'].div(pl_data['swin_1_1_1'])
        if can_use:
            print("alb_1_1_1 is available, but will be calculated instead")
    elif can_use:
        # TODO 1 QOA should not be here, nor conversion is correct here, must be on import?
        pl_data['albedo'] = pl_data['alb_1_1_1'] / 100.0
    else:
        print("No swin_1_1_1/sout_1_1_1, nor alb_1_1_1")
        return 0

    pl_data.loc[pl_data['swin_1_1_1'] <= 20., 'albedo'] = np.nan
    pl_data.loc[pl_data['swout_1_1_1'] <= 0, 'albedo'] = np.nan

    pl_ind = pl_data[pl_data['albedo'] < pl_data['albedo'].quantile(0.95)].index
    fig = go.Figure(layout=layout)
    fig.add_trace(go.Scattergl(x=pl_data.loc[pl_ind].index, y=pl_data.loc[pl_ind, 'albedo'], name="Albedo"))
    fig.update_layout(title='Albedo')
    fig_config = {'toImageButtonOptions': {'filename': 'albedo', }}
    fig.show(config=fig_config)
