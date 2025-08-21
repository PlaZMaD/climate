import logging
from pathlib import Path
import pandas as pd


def export_rep_level3(fpath: Path, df: pd.DataFrame, time_col: str, output_template, config, points_per_day):
    df['Year'] = df[time_col].dt.year
    df['DoY'] = df[time_col].dt.dayofyear
    df['Hour'] = df[time_col].dt.hour + df[time_col].dt.minute / 60

    df['NEE'] = df['nee'].fillna(-9999)
    df['LE'] = df['le'].fillna(-9999)
    df['H'] = df['h'].fillna(-9999)
    if 'swin_1_1_1' in df.columns:
        df['Rg'] = df['swin_1_1_1'].fillna(-9999)
    else:
        print("WARNING! No swin_1_1_1!")

    # TODO 1 QOA does switching name 'vpd' <-> 'vpd_1_1_1' have any purpose? (Q about import, not on export)
    # introduces nasty complications, requires fix on ias export?
    # E: export goal was to match rep

    # TODO 2 if biomet, 'air_temperature' contains derivation from 'ta_1_1_1'
    # E: because they are different, 'air_temperature' is worse backup plan if 'ta_1_1_1' is missing
    # TODO 1 check other cols from description

    if config.has_meteo:
        df['Tair'] = df['ta_1_1_1'].fillna(-9999)
        df['rH'] = df['rh_1_1_1'].fillna(-9999)
        df['VPD'] = df['vpd_1_1_1'].fillna(-9999)
    else:
        df['Tair'] = (df['air_temperature'] - 273.15).fillna(-9999)
        df['rH'] = df['rh'].fillna(-9999)
        df['VPD'] = df['vpd'].fillna(-9999)

    if 'ts_1_1_1' in df.columns:
        df['Tsoil'] = df['ts_1_1_1'].fillna(-9999)

    df['Ustar'] = df['u_star'].fillna(-9999)

    if 'ch4_flux' in df.columns:
        df['CH4flux'] = df['ch4_flux'].fillna(-9999)

    i = 0
    while df.iloc[i]['Hour'] != 0.5:
        i += 1
    df = df.iloc[i:]

    if len(df.index) < 90 * points_per_day:
        print("WARNING!  < 90 days in reddyproc file!")

    pd.DataFrame({
        key: item for key, item in output_template.items() if key in df.columns
    }).to_csv(fpath, index=False, sep=' ')
    df.to_csv(fpath, index=False, header=False,
              columns=[i for i in output_template.keys() if i in df.columns], mode='a', sep=' ')
    del df
    logging.info(f"REddyProc file saved to {fpath}")
