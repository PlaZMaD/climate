import os
import shutil
import sys
from pathlib import Path

from IPython import get_ipython


# DONE log remove if logger worked


class EnvDetect:
    def __init__(self):
        # TODO QE 4 is also support of local ipynb any useful? (COLAB | LOCAL, IPYNB | PY)
        try:
            import google.colab
        except ImportError:
            self.COLAB = False
        else:
            self.COLAB = True
        
        self.LOCAL = not self.COLAB
        self.IPYNB: bool = get_ipython()


ENV = EnvDetect()


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


def setup_r_env(repo_dir: Path):
    if ENV.LOCAL:
        # only for conda rpy2: (bundled with embedded R which should go without default R_HOME):
        # env_dir = Path(sys.executable).parent
        # r_dir = env_dir / 'Lib/R'
        # assert r_dir.exists()
        # os.environ['R_HOME'] = str(r_dir)
        # os.environ['RPY2_CFFI_MODE'] = "ABI"
        
        # rpy2 malfunctions with R4.6.0
        if not shutil.which("R.dll"):
            print(f"rpy2 did not place R.dll in the path, adding it manually")
            r_home = Path(os.environ['R_HOME']) 
            r_bin = r_home / 'bin' / 'x64'
            os.environ["PATH"] = str(r_bin) + os.pathsep + os.environ["PATH"]
            assert shutil.which("R.dll")
            
            # os.add_dll_directory(str(r_bin))
        
        # "make not found" means Rtools not installed, RTools45:
        # https://cran.r-project.org/bin/windows/Rtools/rtools45/rtools.html
        # https://cran.r-project.org/bin/windows/Rtools/rtools45/files/rtools45-6768-6492.exe
                
        # only if system R used on W10 (not conda bundled)
        # remove from Rcmd_environ to user PATH to remove rpy2 import warning
        
        # for pip rpy2 on W10, just set R_HOME correctly
        pass
    else:
        # something different, but it works
        # print(f"Google colab auto sets R_HOME to: {os.environ['R_HOME']}")
    
        # load rpy2 specifically after adding R.dll to the path, or error will happen:
        # package ‘stats’ in options("defaultPackages") was not found 
        from rpy2 import robjects
        
        install_reddyproc_path = repo_dir / 'src/reddyproc/install_reddyproc.r'
        robjects.r.source(str(install_reddyproc_path))
        
        pass
