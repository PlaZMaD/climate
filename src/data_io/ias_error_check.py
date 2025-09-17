# -*- coding: utf-8 -*-
# pyinstaller.exe --onefile --hidden-import openpyxl.cell._writer --windowed --add-data "locale;locale" --add-data "regulation.ico;."
# <a href="https://www.flaticon.com/free-icons/rules" title="rules icons">Rules icons created by Flat Icons - Flaticon</a>
import gettext
import logging
import re
import sys
from copy import deepcopy as copy
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime

from src.data_io.table_loader import load_table_logged


# np.set_printoptions(threshold=sys.maxsize)


def set_lang(language):
    # TODO E 3 replaced to Path, verify bundle still works
    # get the bundle dir if bundled or simply the __file__ dir if not bundled
    bundle_dir = getattr(sys, '_MEIPASS', Path(__file__).parent.parent.parent.absolute())

    locales_dir = bundle_dir / 'locale'
    assert locales_dir.exists()

    lang = gettext.translation('messages', locales_dir, fallback=True, languages=[language])
    lang.install()


# TODO 3 E fixes done: 'FO3_SSITC_ TEST' -> 'FO3_SSITC_TEST', need to update IAS check tool
# 'SPEC_NIR_ OUT' 'SPEC_PRI_REF_ IN', 'SPEC_RED_ OUT', 'SPEC_PRI_ REF_OUT', 'SPEC_RED_ IN'
known_columns = ['ALB', 'APAR', 'CH4', 'CO2', 'CO2C13', 'D_SNOW', 'DBH', 'EVI', 'FC', 'FC_CMB', 'FC_SSITC_TEST', 'FCH4',
                 'FCH4_CMB', 'FCH4_PI', 'FETCH_70', 'FETCH_80', 'FETCH_90', 'FETCH_FILTER', 'FETCH_MAX', 'FH2O', 'FN2O',
                 'FN2O_CMB', 'FNO', 'FNO_CMB', 'FNO2', 'FNO2_CMB', 'FO3', 'FO3_SSITC_TEST', 'G', 'GPP_PI', 'H', 'H_PI',
                 'H_SSITC_TEST', 'H2O', 'LE', 'LE_PI', 'LE_SSITC_TEST', 'LEAF_WET', 'LW_IN', 'LW_OUT', 'MCRI',
                 'MO_LENGTH', 'MTCI', 'N2O', 'NDVI', 'NEE_PI', 'NETRAD', 'NIRV', 'NO', 'NO2', 'O3', 'P', 'P_RAIN',
                 'P_SNOW', 'PA', 'PBLH', 'PPFD_BC_IN', 'PPFD_DIF', 'PPFD_DIR', 'PPFD_IN', 'PPFD_OUT', 'PRI', 'R_UVA',
                 'R_UVB', 'RECO_PI', 'REDCl', 'REP', 'RH', 'RUNOFF', 'SAP_DT', 'SAP_FLOW', 'SB', 'SC', 'SCH4', 'SG',
                 'SH', 'SLE', 'SPEC_NIR_IN', 'SPEC_NIR_OUT', 'SPEC_PRI_REF_IN', 'SPEC_PRI_REF_OUT',
                 'SPEC_PRI_TGT_IN', 'SPEC_PRI_TGT_OUT', 'SPEC_RED_IN', 'SPEC_RED_OUT', 'SR', 'STEMFLOW', 'SW_BC_IN',
                 'SW_DIF', 'SW_IN', 'SW_OUT', 'SWC', 'T_BOLE', 'T_CANOPY', 'T_DP', 'T_SONIC', 'T_SONIC_SIGMA', 'TA',
                 'TAU', 'TAU_SSITC_TEST', 'TCARI', 'THROUGHFALL', 'TS', 'U_SIGMA', 'USTAR', 'V_SIGMA', 'VPD_PI',
                 'W_SIGMA', 'WD', 'WD_SIGMA', 'WS', 'WS_MAX', 'WTD', 'ZL', 'CO2_STR', 'CH4_RSSI',
                 'FCH4_SSITC_TEST',
                 # TODO QE 3 ias check tool requires one specific name too, must be updated
                 # TODO 1: QV: specification contains error V: use specification, H20_STR = no import rename for now; 
                 # E: intentional (need to rename, to common name)
                 'H20_STR', 'H2O_STR'
                 ]


def get_freq(df, time):
    try_max = 100
    try_ind = 0
    t_shift = 5
    start = 1
    deltas = df[time] - df[time].shift(1)
    while try_ind < try_max:
        del_arr = deltas.iloc[start + try_ind * t_shift: start + try_ind * t_shift + t_shift].values
        if not np.all(del_arr == del_arr[0]) and del_arr[0] is not None:
            try_ind = try_ind + 1
            continue
        else:
            return del_arr[0]


def column_checker(col_list):
    error_flag = 0

    # Проверка на наличие временнЫх колонок
    minimum_setup = {'TIMESTAMP_START', 'TIMESTAMP_END'}
    if not set(col_list[:2]) <= minimum_setup:  # TODO QE 3 or != ?
        logging.error(
            _("DateTime columns ['TIMESTAMP_START', 'TIMESTAMP_END'] should go first. Check columns order and names."))
        error_flag = 1
    try:
        dtime_pos = col_list.index('DTime')
        if dtime_pos != 2:
            logging.error(_('Wrong DTime column position, should go 3!'))
            error_flag = 1
    except ValueError:
        logging.info(_("No DTime column in the data"))

    # Проверка на наличие дублирующихся названий
    seen = set()
    dupes = []
    for col in col_list:
        if col in seen:
            dupes.append(col)
        else:
            seen.add(col)
    if len(dupes) > 0:
        logging.error(_("There are columns with the same names: {}").format(dupes))
        error_flag = 1

    # Сортировка по индексам
    full_col_list = copy(col_list)
    full_col_list = [f for f in full_col_list if f not in ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']]

    re_check = [re.fullmatch(r".*_[0-9]_[0-9]_[0-9]", f) for f in full_col_list]
    re_check = [f.string for f in re_check if f is not None]

    no_index_cols = [f for f in full_col_list if f not in re_check]
    if len(no_index_cols) > 0:
        error_flag = 1
        logging.error(
            _("Columns naming problem, columns {} do not have correct suffix structure.").format(no_index_cols))

    unique_cols = list(set([f[:-6] for f in re_check]))
    for col in unique_cols:

        if col not in known_columns:
            logging.warning(
                _("The column {} is not in the known columns list, please double-check the name!").format(col))

        col_with_inds = [f for f in re_check if re.fullmatch(f"{col}_[0-9]_[0-9]_[0-9]", f)]
        if len(col_with_inds) == 1:
            if col_with_inds[0][-5:] != '1_1_1':
                logging.error(_("Suffix problem for {}, 1_1_1 should be used in case of a single variable.").format(
                    col_with_inds))
                error_flag = 1
        else:
            index_structure = np.array([f[-5:].split('_') for f in col_with_inds]).astype(int)
            for suf in range(3):
                ind_line = index_structure[:, suf]
                if ind_line.min() != 1:
                    logging.error(_('Check suffix for {}, not starting from 1').format(col))
                    error_flag = 1

                prev = 1
                sorted_inds = np.sort(ind_line)
                for i in sorted_inds:
                    if i - prev > 1:
                        logging.error(
                            _('Check suffix for {} with #{} index "{}", incrementing by > 1').format(col, suf + 1, i))
                        error_flag = 1
                    prev = i
    linked_cols = {}
    linked_cols['FCH4'] = ['P', 'RH', 'SCH4', 'USTAR', 'CH4_RSSI']
    linked_cols['FC'] = ['FC_SSITC_TEST', 'P', 'RH', 'SC', 'SW_IN', 'TA', 'USTAR', 'CO2_STR']
    linked_cols['FH2O'] = ['G', 'LE_SSITC_TEST', 'NETRAD', 'P', 'RH', 'SLE', 'SW_IN', 'H2O_STR']
    linked_cols['FN2O'] = ['P', 'RH', 'USTAR']
    linked_cols['FNO2'] = ['P', 'RH', 'USTAR']
    linked_cols['FO3'] = ['FO3_SSITC_TEST', 'P', 'RH', 'USTAR']
    linked_cols['H'] = ['G', 'H_SSITC_TEST', 'NETRAD', 'P', 'RH', 'SH', 'SW_IN']
    linked_cols['LE'] = ['LE_SSITC_TEST', 'G', 'NETRAD', 'P', 'SLE', 'SW_IN', 'H2O_STR']
    linked_cols['TAU'] = ['TAU_SSITC_TEST']

    for col, linked_list in linked_cols.items():
        if col in unique_cols:
            diff = list(set(linked_list) - set(unique_cols))
            if len(diff) > 0:
                logging.warning(_("Check linked vars for {}, missing cols: {}").format(col, diff))

    return error_flag


def check_time(data, time_in, check_year=True):
    data_in = data.copy()
    data_in['default_index'] = data.index + 2
    data_in.index = data_in[time_in]
    outflag = 0

    logging.info(_("Checking time column for {}").format(time_in))
    correct_column_type = is_datetime(data_in[time_in])
    if not correct_column_type:
        logging.info(_("{} is not of correct type.").format(time_in))
        outflag = 1

    missed_values = data_in[time_in].isna()
    if missed_values.any():
        logging.error(_("Can't read timestamp. Please check entries near lines \n {}").format(
            data_in.loc[missed_values, 'default_index'].to_numpy()))
        outflag = 1

    data_in_dup = data_in.drop(data_in[missed_values].index, axis=0)

    if check_year and (
            not (data_in_dup[time_in].dt.year.to_numpy()[0] == data_in_dup[time_in].dt.year.to_numpy()[:-1]).all()):
        years = data_in_dup[time_in].dt.year.unique()
        examples = [int(data_in_dup.query(f'{time_in}.dt.year=={f}')['default_index'].to_numpy()[0]) for f in years]
        logging.error(
            _("There should be only one year presented in file, got {}, i.e. lines {}!").format(years, examples))
        outflag = 1

    if data_in_dup.index.duplicated(keep='first').any():
        logging.error(_("Duplicated timestamps! check lines:{}").format(
            data_in_dup.loc[data_in_dup.index.duplicated(), 'default_index'].to_numpy()))
        outflag = 1

    return outflag


def final_time_check(data, time_in):
    data_in = data.copy()
    data_in['default_index'] = data.index + 2
    data_in.index = data_in[time_in]
    outflag = 0

    data_freq = pd.to_timedelta(get_freq(data_in, time_in))

    year = data_in.index.year.to_numpy()[0]
    if "TIMESTAMP_START" in time_in:
        start = f"{year}.01.01 00:00"
        end = f"{year}.12.31 23:30"
    else:
        if "TIMESTAMP_END" in time_in:
            start = f"{year}.01.01 00:30"
            end = f"{year + 1}.01.01 00:00"
        else:
            logging.error(_("Strange time column name!"))
            return 1
    correct_index = pd.date_range(start=pd.to_datetime(start, format="%Y.%m.%d %H:%M"),
                                  end=pd.to_datetime(end, format="%Y.%m.%d %H:%M"),
                                  freq=pd.to_timedelta(data_freq))
    extra_index = data_in.index.difference(correct_index)
    missing_index = correct_index.difference(data_in.index)
    if len(missing_index) > 0:
        outflag = 1
        logging.error(_("Missing values: {}").format(missing_index.astype(str)))
    if len(extra_index) > 0:
        outflag = 1
        logging.error(_("Extra values: {}, lines: {}").format(extra_index.astype(str),
                                                              data_in.loc[extra_index, 'default_index'].to_numpy()))

    logging.info("\n")

    return outflag


def load_ias(fpath: Path):
    # TODO 2 try to merge into src.data_io.table_loader -> load_table_from_file
    # there is something wrong with csv files
    # may be wrong - file is shared, so will require more shared file
    ext_l = fpath.suffix.lower()

    if '.csv' in ext_l:
        ftype = 'csv'
    elif ext_l in ['.xls', '.xlsx']:
        ftype = 'excel'
    else:
        raise Exception('Unknown extension.')

    load_func = None
    l_config = {}

    if ftype == 'csv':
        load_func = pd.read_csv
        # l_config['sep'] = sep

    elif ftype == 'excel':
        load_func = pd.read_excel
        l_config['sheet_name'] = None

    else:
        logging.error(_("Select CSV, XLS or XLSX file."))
        return 2

    try:
        data = load_func(fpath, **l_config)
    except Exception as e:
        logging.error(e)
        raise

    if ftype == 'excel':
        if isinstance(data, dict):
            if len(data.values()) > 1:
                logging.error(_("Several lists in data file!"))
                assert False
            else:
                data = next(iter(data.values()))
        logging.info(f"File {fpath} loaded.\n")

    return data


def check_ias_file(fpath):
    # TODO 3 possibly extract later to abstract time series converter/repairer routines which are format independent? E: ok
    # eddypro may have similar flaws

    # data = load_ias(fpath)
    data = load_table_logged(fpath)

    total_errors = 0
    columns = list(copy(data.columns))
    if len(columns) < 3:
        logging.error(
            _("Not enough columns, please check your file. If you are using csv - make sure that it uses comma as a separator."))
        return 0

    check_column = column_checker(columns)
    total_errors = total_errors + check_column

    time_checks = []
    final_time_checks = []

    for col in ['TIMESTAMP_START', 'TIMESTAMP_END']:
        if col not in columns:
            time_checks.append(1)
            logging.error(_('No column {} in the file!').format(col))
            continue

        data[f'{col}_datetime'] = pd.to_datetime(data[col].fillna(0).astype(int), format="%Y%m%d%H%M", errors='coerce')
        time_checks.append(check_time(data, f"{col}_datetime"))
        if not time_checks[-1]:
            final_time_checks.append(final_time_check(data, f"{col}_datetime"))
        else:
            final_time_checks.append(1)
            logging.warning(
                _("No  final timestamp checks for {}, please fix all errors to complete this step.").format(col))

    total_errors = total_errors + np.sum(time_checks) + np.sum(final_time_checks)
    col_errors = 0

    for col in columns:
        if col in ['TIMESTAMP_START', 'TIMESTAMP_END'] or col not in data.columns:
            continue

        na_test = data[col].isna().all()
        if na_test:
            col_errors = col_errors + 1
            logging.error(_("The column {} is empty.").format(col))
            continue

        all_std_na = data[col].eq(-9999).all()
        if all_std_na:
            col_errors = col_errors + 1
            logging.error(_("The column {} has only -9999 values.").format(col))
            continue

        inf_vals = data.loc[np.logical_or(data[col] == np.inf, data[col] == -np.inf)].index.to_numpy()
        if len(inf_vals) > 0:
            logging.error(_("INF val in {} at the position {}").format(col, inf_vals))
            col_errors = col_errors + 1

        # check_col = pd.to_numeric(data[col].fillna(-9999), errors='coerce')
        check_col = pd.to_numeric(data[col], errors='coerce')

        inf_vals = check_col.loc[np.logical_or(check_col == np.inf, check_col == -np.inf)].index.to_numpy()
        if len(inf_vals) > 0:
            logging.error(_("INF val in {} at the position {}").format(col, inf_vals))
            col_errors = col_errors + 1

        wrong_vals = check_col.loc[check_col.isna()].index + 2
        if len(wrong_vals) > 0:
            col_errors = col_errors + 1
            logging.error(_("Non numerical values in {} at lines {}").format(col, wrong_vals.to_numpy()))

    total_errors = total_errors + col_errors
    logging.info(_("{} errors in total, check logs!").format(total_errors))

    return total_errors


class ErrorFlagHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.had_error = False

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.had_error = True


def draft_check_ias(fpath):
    # TODO E 3 synchronise sometimes to IAS tool repo (via duplicate file)

    # TODO 2 move to the script start?
    # will it be translation method for all the tools?
    # afaik это основной метод мультилокальности в питоне, но переделывать под него все потребует усилий.
    set_lang('ru')

    logging.info("Checking IAS file...")

    logger = logging.getLogger()
    stream_formatter = logging.Formatter(
        "%(module)s: %(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(stream_handler)
    # logger.critical("Process init")

    formatter = logging.Formatter(
        "[%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    errors = check_ias_file(fpath)

    if errors > 0:
        msg = f"Input file {fpath} cannot be used yet. Please fix errors."
        logging.error(msg)

        # TODO 2 colab crashes on this, what is proper silent abort? search 1 more use case
        # raise SystemExit(msg)

        raise Exception(msg)
