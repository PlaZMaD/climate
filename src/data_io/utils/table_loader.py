"""
This file is an attempt to handle table load as an abstract initial part of data processing,
and to separate operations like time series repair or merge years from specific file format (if this is possible at all)
"""

from pathlib import Path
import pandas as pd
import numpy as np
from gettext import gettext as _

from src.helpers.pd_helpers import find_changed_el
from src.ff_logger import ff_logger


# TODO 2 csv: non-comma and other separators: strategy?
# TODO 1 csv: file recognised as single column - must fail


def guess_inconsistent_csv_table_start(fpath: Path, lookup_rows=10, **pd_io_kwargs):
    """ a workaround for some (incorrect) csv with multiple header columns with different width """
    
    rows = [pd.read_csv(fpath, skiprows=i, nrows=1, header=None, **pd_io_kwargs) for i in range(lookup_rows)]
    row_l = np.array([len(row.columns) for row in rows])
    equal_rows_start_at = find_changed_el(row_l, from_end=True) + 1
    
    if equal_rows_start_at == lookup_rows:
        raise Exception(f'Cannot guess start of csv table in {fpath}')
    
    return equal_rows_start_at


def load_csv(fpath: Path, max_header_rows=4, **pd_read_kwargs):
    '''
    # does not work reliably even with 10 numeric lines
    import chardet
    if 'encoding' not in pd_read_kwargs:
        fpath.readlines...
        with open(fpath, "r+b") as fb:
            first_lines = [next(fb) for _ in range(max_header_rows)]
            <delete numeric lines ?>
            enc = chardet.detect(b'\n'.join(first_lines))
            pd_read_kwargs['encoding'] = enc
    '''
    
    fallback_io_kwargs = {'encoding': 'utf8', 'encoding_errors': 'backslashreplace'}
    
    try:
        df = pd.read_csv(fpath, **pd_read_kwargs)
    except FileNotFoundError:
        raise
    except Exception as e:
        # TODO 2 change any to UnicodeDecodeError, <header err name>?
        ff_logger.debug(f'When reading {fpath}: {e}, attempting other import mode.')
        
        if pd_read_kwargs['skiprows'] is None:
            pd_read_kwargs['skiprows'] = guess_inconsistent_csv_table_start(fpath, **fallback_io_kwargs)
        
        df = pd.read_csv(fpath, **fallback_io_kwargs, **pd_read_kwargs)
    
    # TODO 2 Excel sometimes saves empty columns into csv: ,,,,,,,; remove them verbose/silent
    return df


def load_xls(fpath, **pd_read_kwargs):
    # TODO 3 https://stackoverflow.com/questions/50695778/how-to-increase-process-speed-using-read-excel-in-pandas
    data = pd.read_excel(fpath, **pd_read_kwargs)
    if isinstance(data, dict):
        if len(data.values()) > 1:
            ff_logger.error(_("Several lists in data file!"))
            assert False
        else:
            data = next(iter(data.values()))
    return data


def load_table_from_file(fpath, skiprows=None, nrows=None, header_row=0) -> pd.DataFrame:
    """	nrows: read only first n rows """
    # probably extract to load table? can all repairs be generalised operations on tables?
    
    pd_read_kwargs = {'nrows': nrows, 'header': header_row, 'skiprows': skiprows}
    
    suffix = Path(fpath).suffix.lower()
    if suffix == '.csv':
        df = load_csv(fpath, **pd_read_kwargs)
    elif suffix in ['.xls', '.xlsx']:
        df = load_xls(fpath, **pd_read_kwargs)
    else:
        raise Exception(f"Unknown file type {suffix}. Select CSV, XLS or XLSX file.")
    return df


# TODO 2 header_row=None (case of load to auto guess table type)
def load_table_logged(fpath, skiprows=None, nrows=None, header_row=0) -> pd.DataFrame:  
    # TODO 2 possibly this fixed csv (or other) bugs, merge into table loader routine?
    # TODO 2 Excel 2016 saved files seems were impossible to open without specyfying engine, why ?    
    '''
    for key, item in df_dict.items():
        item = item.dropna(how='all', axis=1)
        if (item.loc[0, :].isnull()).sum() > 2:
            print(f"skipping line 1, 3")
            l_config['skiprows'] = [0, 2]  # .append(i)
            continue

        item = item.replace('NAN', np.nan)
        item = item.dropna(how='all', axis=1)
        cond_1 = np.isreal(item.loc[1, :].to_numpy()) == False#(item.loc[1, :].astype(str).str.isnumeric() == False)#(item.loc[0, item.columns != d_config['time']].astype(str).str.isnumeric() == False)
        cond_2 = (item.loc[1, :].isna())#(item.loc[0, item.columns != d_config['time']].isna())


        if (cond_1.sum() > 1 and cond_2.sum() !=len(item.columns) - 1) or (cond_1.sum()==0 and cond_2.sum()==0): #cond_1.sum() > 1 and cond_2.sum() != len(item.columns) - 1: #any(item.loc[0, item.columns != d_config['time']].astype(str).str.isnumeric() == False) and not all(item.loc[0, item.columns != d_config['time']].isna()):
            l_config['skiprows'].append(1)#[1]#lambda x: x == 1
            print(f"skipping line #{1}")
            # else:
            #     pass
            #     # l_config['skiprows'] = None
    '''
    
    # with log_exception(...) instead
    try:
        data = load_table_from_file(fpath, skiprows, nrows, header_row)
    except Exception as e:
        ff_logger.exception(e)
        # raise SystemExit vs
        raise
    
    # TODO 1 move to csf
    ff_logger.info(f'File {fpath} loaded.')
    
    # TODO 3 df.index.freq and df.name: unconventional attrs required for script, probably subclass to solve this    
    
    return data
