import src.helpers.os_helpers  # noqa: F401

from src.ias.error_check import check_file_proto
from src.ias.file_loader import load_ias


def test_ias_to_csv():
    ias_input = "tv_fy4_2023_v01.csv"
    # check_file_proto(ias_input)
    load_ias(ias_input, "test.csv", verify_fpath="eddy_pro result_SSB 2023.csv")

    assert False
