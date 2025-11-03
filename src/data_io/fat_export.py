import numpy as np
import pandas as pd

from bglabutils import basic as bg
from src.config.ff_config import FFConfig, FFGlobals
from src.ff_logger import ff_logger


def export_fat(df: pd.DataFrame, fat_output_template, time_col, gl: FFGlobals, config: FFConfig):
    df['DoY'] = np.round(
        df[time_col].dt.dayofyear + df[time_col].dt.hour / 24. + df[time_col].dt.minute / 24. / 60.,
        decimals=3)
    df[r'u*'] = df['u_star'].fillna(-99999)
    df['H'] = df['h'].fillna(-99999)
    df['lE'] = df['le'].fillna(-99999)
    df['NEE'] = df['nee'].fillna(-99999)
    if 'ppfd_1_1_1' in df.columns:
        df['PPFD'] = df['ppfd_1_1_1'].fillna(-99999)
        df['PPFD_gapfilling'] = df['ppfd_1_1_1'].interpolate(limit=3).fillna(
            bg.calc_rolling(df['ppfd_1_1_1'], rolling_window=10, step=gl.points_per_day, min_periods=4)
        ).fillna(-99999)
    else:
        ff_logger.info(f"FAT file will have no PPFD")
        fat_output_template.pop('PPFD')
    
    if not config._has_meteo:
        df['ta_1_1_1'] = df['air_temperature'] - 273.15
    
    df['Ta'] = df['ta_1_1_1'].fillna(-99999)
    df['VPD'] = df['vpd_1_1_1'].fillna(-99999)
    
    df['period'] = df.index.month % 12 // 3 + 1
    
    df['Ta_gapfilling'] = df['ta_1_1_1'].interpolate(limit=3).fillna(
        bg.calc_rolling(df['ta_1_1_1'], rolling_window=10, step=gl.points_per_day, min_periods=4)
    ).fillna(-99999)
    df['VPD_gapfilling'] = df['vpd_1_1_1'].interpolate(limit=3).fillna(
        bg.calc_rolling(df['vpd_1_1_1'], rolling_window=10, step=gl.points_per_day, min_periods=4)
    ).fillna(-99999)
    
    for year in df.index.year.unique():
        fat_filename = f"FAT_{config.site_name}_{year}.csv"
        fat_fpath = gl.out_dir / fat_filename
        pd.DataFrame(fat_output_template).to_csv(fat_fpath, index=False)
        save_data = df.loc[df[time_col].dt.year == year]
        if len(save_data.index) >= 5:
            save_data.to_csv(fat_fpath, index=False, header=False,
                             columns=[i for i in fat_output_template.keys()], mode='a')  # , sep=' ')
        else:
            fat_fpath.unlink(missing_ok=True)
            
            print(f"not enough data for {year}")
            ff_logger.info(f"{year} not saved, not enough data!")
    
        ff_logger.info(f"FAT file saved to {fat_fpath}")
