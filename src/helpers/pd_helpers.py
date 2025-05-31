import pandas as pd


def equal_series(s1, s2, allow_nans=True):
	return (s1 == s2) | (s1.isna() & s2.isna() & allow_nans)


def df_intersect_cols(df1: pd.DataFrame, df2: pd.DataFrame, invert=False):
	# column-wise intersection

	same_cols = [col for col in df1.columns if col in df2.columns and equal_series(df1[col], df2[col]).all()]
	return df1(same_cols)


def df_get_unique_cols(df1: pd.DataFrame, df2: pd.DataFrame):
	# removes same cols in both dfs

	same_cols = [col for col in df1.columns if col in df2.columns and equal_series(df1[col], df2[col]).all()]

	df1_unique = df1.drop(same_cols, axis='columns', errors='ignore')
	df2_unique = df2.drop(same_cols, axis='columns', errors='ignore')
	return df1_unique, df2_unique
