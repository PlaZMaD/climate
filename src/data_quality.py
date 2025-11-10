from pathlib import Path
import numpy as np
import pandas as pd

from src.ff_logger import ff_logger


def compare_stats(df: pd.DataFrame, qc_file: Path):
    df_stats = df.describe(percentiles=[0.95]).loc[['mean', 'std']]
    
    # df_stats.to_excel(qc_file)
    # df_stats.loc['mean','tau'] = 5
    df_exp_stats = pd.read_excel(qc_file, index_col=0)
    df_merge = df_exp_stats.rename(index={'mean': 'ref_mean', 'std': 'ref_std'}).loc[['ref_mean', 'ref_std']]
    
    df = pd.concat([df_merge, df_stats], axis=0)
    
    mean_diff = np.abs(df.loc['ref_mean'] - df.loc['mean'])
    mask_outside_2s = mean_diff > df.loc['ref_std'] * 2
    mask_outside_both_2s = mean_diff > np.maximum(df.loc['std'], df.loc['ref_std']) * 2
    
    ff_logger.info('Values with means outside of 2 sigmas of the reference station: \n' +
          df.loc[:, mask_outside_2s].to_string())    
    ff_logger.info('Values with means outside of 2 sigmas of both reference and current station: \n' +
                   df.loc[:, mask_outside_both_2s].to_string())
    pass
    

def try_compare_stats(df: pd.DataFrame, qc_file: Path):
    try:
        compare_stats(df, qc_file)
    except:
        print('Cannot compare statistics')
