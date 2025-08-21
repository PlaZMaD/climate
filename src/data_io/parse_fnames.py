import logging
import re


def examples_to_text(examples: dict):
    res = ''
    for k, v in examples.items():
        res += k + ' -> ' + v
    return res


def preprocess_fname(fname: str) -> str:
    return fname.replace(' ', '_')


def try_parse_ias_fname(fname: str):
    examples = {'tv_fy4_2023_v01.xlsx': 'tv_fy4'}
    txt_examples = examples_to_text(examples)
    # [try_parse_ias_fname(k) for k,v in examples.items()]

    fname = preprocess_fname(fname)
    match1 = re.match(r"(.*)_\d{2,4}_(v[\dN]{1,3})", fname)

    if match1:
        ias_output_prefix = match1.group(1)
        ias_output_version = match1.group(2)
    else:
        logging.warning(f'Cannot parse ias file name {fname} for site id and version, using defaults.\n'
                        "   Try to rename ias input file to match 'siteid_YYYY_vNN.ext' pattern, \n"
                        f"  for example, {txt_examples}.")
        ias_output_prefix = 'unknown_site'
        ias_output_version = 'vNN'
    return ias_output_prefix, ias_output_version


def try_parse_csf_fname(fname: str):
    # TODO 2 any csf patterns?
    '''
    examples = {'tv_fy4_2023_v01.xlsx': 'tv_fy4'}
    txt_examples = examples_to_text(examples)
    # [try_parse_ias_fname(k) for k,v in examples.items()]

    fname = preprocess_fname(fname)
    match1 = re.match(r"(.*)_\d{2,4}_(v[\dN]{1,3})", fname)

    if match1:
        ias_output_prefix = match1.group(1)
        ias_output_version = match1.group(2)
    else:
        logging.warning(f'Cannot parse ias file name {fname} for site id and version, using defaults.\n'
                        "   Try to rename ias input file to match 'siteid_YYYY_vNN.ext' pattern, \n"
                        f"  for example, {txt_examples}.")
        ias_output_prefix = 'unknown_site'
        ias_output_version = 'vNN'
    '''
    logging.warning('No csf file name patterns yet, set config ias_output_prefix manually.')
    ias_output_prefix = 'unknown_site'
    ias_output_version = 'vNN'

    return ias_output_prefix, ias_output_version


def try_parse_eddypro_fname(fname: str):
    examples = {'Iga_FO_23.csv': 'Iga', 'eddy_pro SSB 2023.csv': 'SSB'}
    txt_examples = examples_to_text(examples)
    # [try_parse_eddypro_fname(k) for k,v in examples.items()]

    fname = preprocess_fname(fname)
    match1 = re.match(r"(.*)_FO_.*\d{2,4}", fname, flags=re.IGNORECASE)
    match2 = re.match(r"eddy.?pro_(.*)_\d{2,4}", fname, flags=re.IGNORECASE)

    match = match1 if match1 else match2
    if match:
        ias_output_prefix = match.group(1)
    else:
        logging.warning(f'Cannot parse eddypro file name {fname} for site id, using default.\n'
                        "   Try to rename eddypro input file to match 'siteid_FO_YYYY.ext' or 'eddy_pro_siteid_YYYY' "
                        "patterns, \n"
                        f"  for example, {txt_examples}.")
        ias_output_prefix = 'unknown_site'

    logging.warning('No version is expected in eddypro file name, specify manually in ias_output_version .')
    ias_output_version = 'vNN'

    return ias_output_prefix, ias_output_version
