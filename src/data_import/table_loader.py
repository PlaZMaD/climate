import logging
from pathlib import Path

import pandas as pd


def load_csv(fpath, **pd_read_kwargs):
	return pd.read_csv(fpath, **pd_read_kwargs)


def load_xls(fpath, **pd_read_kwargs):
	data = pd.read_excel(fpath, **pd_read_kwargs)
	if isinstance(data, dict):
		if len(data.values()) > 1:
			logging.error(_("Several lists in data file!"))
			assert False
		else:
			data = next(iter(data.values()))
	return data


def load_table_from_file(fpath, nrows=None, header = 'infer') -> pd.DataFrame:
	# probably extract to load table? can all repairs be generalised operations on tables?

	pd_read_kwargs = {'nrows': nrows, 'header': header}

	suffix = Path(fpath).suffix.lower()
	if suffix == '.csv':
		df = load_csv(fpath, **pd_read_kwargs)
	elif suffix in ['.xls', '.xlsx']:
		df = load_xls(fpath, **pd_read_kwargs)
	else:
		raise Exception(_(f"Unknown file type {suffix}. Select CSV, XLS or XLSX file."))
	return df
