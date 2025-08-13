import os
import sys
from pathlib import Path

from IPython import get_ipython


class _Env:
    def __init__(self):
        # TODO QE 3 add support local ipynb or skip? (COLAB | LOCAL, IPYNB | PY)
        try:
            import google.colab
        except ImportError:
            self.COLAB = False
        else:
            self.COLAB = True

        self.LOCAL = not self.COLAB
        self.IPYNB: bool = get_ipython()


ENV = _Env()


def ipython_only(func):
    def wrapper(*args, **kwargs):
        if ENV.IPYNB:
            return func(*args, **kwargs)
        else:
            print(f"IPython env not detected. {func.__name__} is skipped by design.")
            return None

    return wrapper


def colab_only(func):
    def wrapper(*args, **kwargs):
        if ENV.COLAB:
            return func(*args, **kwargs)
        else:
            print(f"Colab env not detected. {func.__name__} is skipped by design.")
            return None

    return wrapper


def setup_r_env():
    if ENV.LOCAL:
        # only for conda rpy2: (bundled with embedded R which should go without default R_HOME):
        # env_folder = Path(sys.executable).parent
        # r_folder = env_folder / 'Lib/R'
        # assert r_folder.exists()
        # os.environ['R_HOME'] = str(r_folder)

        # only if system R used on W10 (not conda bundled)
        # remove from Rcmd_environ to user PATH to remove rpy2 import warning
        # bin1_path = "%RTOOLS44_HOME%/x86_64-w64-mingw32.static.posix/bin;"
        # bin2_path = "%RTOOLS44_HOME%/usr/bin;"
        # assert bin1_path in os.environ['PATH'] ?
        # assert bin2_path in os.environ['PATH'] ?

        # for pip rpy2 on W10, just set R_HOME correctly
        pass
    else:
        # something different, but it works
        # print(f"Google colab auto sets R_HOME to: {os.environ['R_HOME']}")
        pass
