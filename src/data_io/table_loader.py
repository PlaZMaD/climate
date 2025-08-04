import logging
from pathlib import Path

import pandas as pd


def guess_csv_table_start(fpath: Path, nrows=10, sep=','):
    equal_rows_start_at = 0

    # TODO 2 is enumerate fast?
    with open(fpath, "r") as fp:
        prev_ncols = -1
        for i, line in enumerate(fp):
            ncols = line.count(sep) + 1
            if prev_ncols != ncols:
                equal_rows_start_at = i
            prev_ncols = ncols
            if i == nrows:
                break

    if equal_rows_start_at == nrows:
        raise Exception(f'Cannot guess start of csv table in {fpath}')

    return equal_rows_start_at


def load_csv(fpath: Path, **pd_read_kwargs):
    try:
        return pd.read_csv(fpath, **pd_read_kwargs)
    except FileNotFoundError:
        raise
    except Exception as e:
        logging.error(f'Error when reading {fpath}: {e}, attempting error correction.')

        if 'skiprows':
            header_row_guess = guess_csv_table_start(fpath)
            pd_read_kwargs['skiprows'] = header_row_guess

        with open(fpath, encoding='utf8', errors='backslashreplace') as f:
            return pd.read_csv(f, **pd_read_kwargs)


def load_xls(fpath, **pd_read_kwargs):
    # TODO 3 https://stackoverflow.com/questions/50695778/how-to-increase-process-speed-using-read-excel-in-pandas
    data = pd.read_excel(fpath, **pd_read_kwargs)
    if isinstance(data, dict):
        if len(data.values()) > 1:
            logging.error(("Several lists in data file!"))
            assert False
        else:
            data = next(iter(data.values()))
    return data


def load_table_from_file(fpath, skiprows=None, nrows=None, header_row=None, no_header=False) -> pd.DataFrame:
    """	nrows: read only first n rows """
    # probably extract to load table? can all repairs be generalised operations on tables?

    pd_read_kwargs = {'nrows': nrows, 'header': header_row, 'skiprows': skiprows}
    if no_header:
        pd_read_kwargs |= {'header': None}

    suffix = Path(fpath).suffix.lower()
    if suffix == '.csv':
        df = load_csv(fpath, **pd_read_kwargs)
    elif suffix in ['.xls', '.xlsx']:
        df = load_xls(fpath, **pd_read_kwargs)
    else:
        raise Exception(f"Unknown file type {suffix}. Select CSV, XLS or XLSX file.")
    return df


def load_table_logged(fpath, skiprows=None, nrows=None, header_row=None, no_header=False):
    # with log_exception(...) instead
    try:
        data = load_table_from_file(fpath, skiprows, nrows, header_row, no_header)
    except Exception as e:
        logging.exception(e)
        raise

    logging.info(f'File {fpath} loaded.\n')
    return data
