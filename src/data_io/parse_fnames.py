import re

from src.ff_logger import ff_logger
from src.helpers.py_collections import format_dict


def preprocess_fname(fname: str) -> str:
    return fname.replace(' ', '_')


def try_parse_ias_fname(fname: str):
    examples = {'tv_fy4_2023_v01.xlsx': 'tv_fy4'}
    txt_examples = format_dict(examples)
    # [try_parse_ias_fname(k) for k,v in examples.items()]
    
    fname = preprocess_fname(fname)
    match1 = re.match(r"(.*)_\d{2,4}_(v[\dN]{1,3})", fname, re.IGNORECASE)
    
    if match1:
        site_name = match1.group(1)
        ias_out_version = match1.group(2)
    else:
        msg = (f'Cannot parse ias file name {fname} for site id and version, using defaults. \n'
               f"\t Try to rename file to match 'siteid_YYYY_vNN.ext' pattern, \n"
               f'\t for example, {txt_examples}.')
        ff_logger.warning(msg)
        site_name = None
        ias_out_version = None
    return site_name, ias_out_version


def try_parse_csf_fname(fname: str):
    # TODO 2 QOA import: add patterns
    examples = {'Psn_CSF_2024_test.csv': 'Psn'}
    txt_examples = format_dict(examples)
    # [try_parse_ias_fname(k) for k,v in examples.items()]
    
    fname = preprocess_fname(fname)
    match1 = re.match(r"(.*)_CSF_\d{2,4}_.*", fname, re.IGNORECASE)
    
    if match1:
        site_name = match1.group(1)
    else:
        ff_logger.info(f'Cannot parse csf file name {fname} for site name, using defaults.\n'
                       "   Try to rename csf input file to match 'siteid_CSF_YYYY.ext' pattern, \n"
                       f"  for example, {txt_examples}.")
        site_name = 'unknown_site'
    
    ias_out_version = None
    
    return site_name, ias_out_version


def try_parse_eddypro_fname(fname: str):
    examples = {'Iga_FO_23.csv': 'Iga', 'eddy_pro SSB 2023.csv': 'SSB'}
    txt_examples = format_dict(examples)
    # [try_parse_eddypro_fname(k) for k,v in examples.items()]
    
    fname = preprocess_fname(fname)
    match1 = re.match(r"(.*)_FO_.*\d{2,4}", fname, flags=re.IGNORECASE)
    match2 = re.match(r"eddy.?pro_(.*)_\d{2,4}", fname, flags=re.IGNORECASE)
    
    match = match1 if match1 else match2
    if match:
        site_name = match.group(1)
    else:
        msg = (f'Cannot parse eddypro file name {fname} for site id, using default. \n'
               f"\t Try to rename file to match 'siteid_FO_YYYY.ext' or 'eddy_pro_siteid_YYYY' patterns, \n"
               f'\t for example, {txt_examples}.')
        ff_logger.info(msg)
        site_name = None
    
    ff_logger.info('No version is expected in the eddypro file name, specify manually in ias_out_version .')
    ias_out_version = None
    
    return site_name, ias_out_version
