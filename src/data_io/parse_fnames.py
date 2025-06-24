import logging
import re


def try_parse_ias_fname(fname: str):
	examples = 'tv_fy4_2023_v01.xlsx -> tv_fy4'
	match1 = re.match(r"(.*)_\d{2,4}_(v\d{1,3})", fname)

	if match1:
		ias_output_prefix = match1.group(1)
		ias_output_version = match1.group(2)
	else:
		logging.warning(f'Cannot parse ias file name {fname} for site id and version, using defaults.\n'
		                "Try to rename ias input file to match 'siteid_YYYY_vNN.ext' pattern, \n"
		                f"for example, {examples}.")
		ias_output_prefix = 'unknown_site'
		ias_output_version = 'vNN'
	return ias_output_prefix, ias_output_version


def try_parse_eddypro_fname(fname: str):
	examples = 'Iga_FO_23.csv -> Iga, eddy_pro SSB 2023.csv -> SSB'
	match1 = re.match(r"(.*)_FO_.*\d{2,4}", fname, flags=re.IGNORECASE)
	match2 = re.match(r"eddy.?pro_(.*)_\d{2,4}", fname, flags=re.IGNORECASE)

	match = match1 if match1 else match2
	if match:
		ias_output_prefix = match.group(1)
	else:
		logging.warning(f'Cannot parse ias file name {fname} for site id and version, using defaults.\n'
		                "Try to rename eddypro input file to match 'siteid_FO_YYYY.ext' or 'eddy_pro_siteid_YYYY' patterns, \n"
		                f"for example, {examples}.")
		ias_output_prefix = 'unknown_site'

	logging.warning('No version is expected in eddypro file name, specify manually in ias_output_version .')
	ias_output_version = 'vNN'

	return ias_output_prefix, ias_output_version
