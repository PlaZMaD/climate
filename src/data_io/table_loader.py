import logging
from pathlib import Path

import pandas as pd


def load_csv(fpath, **pd_read_kwargs):
	try:
		return pd.read_csv(fpath, **pd_read_kwargs)
	except Exception as e:
		logging.error(f'Error when reading {fpath}: {e}, attempting error correction.')
		with open(fpath, encoding='utf8', errors='backslashreplace') as f:
			return pd.read_csv(f, **pd_read_kwargs)


def load_xls(fpath, **pd_read_kwargs):
	data = pd.read_excel(fpath, **pd_read_kwargs)
	if isinstance(data, dict):
		if len(data.values()) > 1:
			logging.error(("Several lists in data file!"))
			assert False
		else:
			data = next(iter(data.values()))
	return data


def load_table_from_file(fpath, nrows=None, header_row=None, no_header=False) -> pd.DataFrame:
	"""	:param nrows: read only first n rows """
	# probably extract to load table? can all repairs be generalised operations on tables?

	pd_read_kwargs = {'nrows': nrows}
	if no_header:
		pd_read_kwargs |= {'header': None}

	suffix = Path(fpath).suffix.lower()
	if suffix == '.csv':
		df = load_csv(fpath, **pd_read_kwargs)
	elif suffix in ['.xls', '.xlsx']:
		df = load_xls(fpath, **pd_read_kwargs)
	else:
		raise Exception(_(f"Unknown file type {suffix}. Select CSV, XLS or XLSX file."))
	return df


def load_table_logged(fpath):
	# with log_exception(...) instead
	try:
		data = load_table_from_file(fpath)
	except Exception as e:
		logging.exception(e)
		raise

	logging.info(f'File {fpath} loaded.\n')
	return data
