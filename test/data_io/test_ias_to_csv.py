import src.helpers.os_helpers  # noqa: F401

from src.data_io.ias_io import import_iases


def test_ias_to_csv():
    ias_input = "tv_fy4_2023_v01.csv"
    # check_file_proto(ias_input)
    import_iases(ias_input, "test.csv", verify_fpath="eddy_pro result_SSB 2023.csv")
    
    assert False
