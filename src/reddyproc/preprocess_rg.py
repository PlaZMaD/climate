from types import SimpleNamespace

import pandas as pd
from pysolar import radiation
from pysolar import solar


# TODO 2 move call earlier to REP file preparation to remove double read of file,
#  but will requre user to set lat long earlier in the config
def prepare_rg(rep_options: SimpleNamespace):
    # generate theoretical solar radiation using specifically pysolar

    if not rep_options.ustar_rg_source == "Rg_th_Py":
        return
    rg_col = rep_options.ustar_rg_source

    csv_header = pd.read_csv(rep_options.input_file, header=None, nrows=2, sep=' ')
    csv_header.columns = csv_header.iloc[0]
    csv_header = csv_header.loc[1:1]

    data = pd.read_csv(rep_options.input_file, header=0, names=csv_header.columns, skiprows=1, sep=' ')

    datetimes = pd.to_datetime({'year': data['Year'], 'month': 1, 'day': 1}, utc=True) - pd.to_timedelta(1, unit='d') + \
                       pd.to_timedelta(data['DoY'], unit='d') + pd.to_timedelta(data['Hour'] - rep_options.timezone, unit='h')
    altitude_degs = solar.get_altitude_fast(rep_options.latitude, rep_options.longitude, datetimes)
    altitude_degs[altitude_degs < 0] = 0.001

    csv_header[rg_col] = ['Wm-2']
    data[rg_col] = radiation.get_radiation_direct(datetimes, altitude_degs)

    csv_header.to_csv(rep_options.input_file, sep=' ', header=True, index=False)
    data.to_csv(rep_options.input_file, sep=' ', index=False,  header=False, mode='a')