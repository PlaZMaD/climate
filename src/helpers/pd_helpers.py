import pandas as pd


def equal_series(s1, s2, compare_na=True):
	return (s1 == s2) | (s1.isna() & s2.isna() & compare_na)


def df_intersect_cols(df1: pd.DataFrame, df2: pd.DataFrame, compare_na=True):
	# returns exacly same cols in both dfs, na == na

	same_name_cols = df1.columns.intersection(df2.columns)
	equal_cols = [col for col in same_name_cols if equal_series(df1[col], df2[col], compare_na).all()]
	return df1[equal_cols]


def df_get_unique_cols(df1: pd.DataFrame, df2: pd.DataFrame, compare_na=True):
	# removes same cols in both dfs, na == na

	equal_cols = df_intersect_cols(df1, df2, compare_na)

	df1_unique = df1.drop(equal_cols, axis='columns', errors='ignore')
	df2_unique = df2.drop(equal_cols, axis='columns', errors='ignore')
	return df1_unique, df2_unique


def df_repair_cols_case(df: pd.DataFrame, correct_case, ignore_missing=True):
	correct_l_to_correct = {c.lower(): c for c in correct_case}

	new_cols = pd.Index([correct_l_to_correct.get(c.lower(), c) for c in df.columns])
	same_cols = new_cols.intersection(df.columns)
	renamed_from = list(df.columns.drop(same_cols))
	renamed_to = list(new_cols.drop(same_cols))

	df.columns = new_cols
	if len(renamed_from) > 0:
		print(f'Unexpected columns case fixed: {renamed_from} -> {renamed_to}')

	missing = set(df.columns) - set(correct_case)
	if len(missing) > 0:
		msg = f'Unknown correct case for columns: {missing}'
		if ignore_missing:
			print(msg)
		else:
			raise Exception(msg)

	return df


def df_verify_cols(df: pd.DataFrame, must_cols, optional_cols, allow_unknown=True):
	if must_cols:
		missing = set(must_cols) - set(df.columns)
		if len(missing) > 0:
			msg = f'Missing expected columns: {missing}'
			return False, msg

	if not allow_unknown:
		unknown_cols = set(df.columns) - set(must_cols) - set(optional_cols)
		if len(unknown_cols) > 0:
			msg = f'Unrecognised columns: {unknown_cols}'
			return False, msg
	return True, ''
