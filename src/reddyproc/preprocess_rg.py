from types import SimpleNamespace
import pandas as pd
import datetime
from pysolar import solar
from pysolar import radiation


# TODO move call earlier to REP file preparation, but will requre user to set lat long away from here
def prepare_rg(rep_options: SimpleNamespace):
    if not rep_options.ustar_use_theor_rg:
        return

    col_names = pd.read_csv(rep_options.input_file, header=None, nrows=2, sep=' ')
    col_names.columns = col_names.iloc[0]
    col_names = col_names.loc[1:1]
    if 'Rg_t' in col_names:
        return

    data = pd.read_csv(rep_options.input_file, header=0, names=col_names.columns, skiprows=1, sep=' ')

    datetimes = pd.to_datetime({'year': data['Year'], 'month': 1, 'day': 1}, utc=True) - pd.to_timedelta(1, unit='d') + \
                       pd.to_timedelta(data['DoY'], unit='d') + pd.to_timedelta(data['Hour'] - rep_options.timezone, unit='h')
    altitude_degs = solar.get_altitude_fast(rep_options.latitude, rep_options.longitude, datetimes)
    altitude_degs[altitude_degs < 0] = 0.001

    col_names['Rg_t'] = ['Wm-2']
    data['Rg_t'] = radiation.get_radiation_direct(datetimes, altitude_degs)

    col_names.to_csv(rep_options.input_file, sep=' ', header=True, index=False)
    data.to_csv(rep_options.input_file, sep=' ', index=False,  header=False, mode='a')