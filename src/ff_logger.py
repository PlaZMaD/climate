import logging
import sys
from pathlib import Path

'''
def debug_stdout_to_log(debug_log_fpath):
    # stdout->log was required for something, possibly legacy
    # duplicates all prints to file

    class Logger(object):
        def __init__(self):
            self.terminal = sys.stdout
            self.log = open(debug_log_fpath, "w")

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)

        def flush(self):
            # this flush method is needed for python 3 compatibility.
            # this handles the flush command by doing nothing.
            # you might want to specify some extra behavior here.
            pass

    sys.stdout = Logger()
'''

# TODO 3 refactor: ff_logger
ff_log = logging.getLogger('FF')


def init_logging(level=logging.INFO, fpath: Path = None, to_stdout=True):
    # seems intended way was to send logs both to log file and stdout?
    
    class FFFormatter(logging.Formatter):
        def format(self, record):
            if record.levelno > logging.INFO:
                return f"[{record.levelname}] {record.getMessage()}"
            return record.getMessage()

    if fpath:
        logging.basicConfig(filename=fpath, filemode="w", force=True)
        if to_stdout:
            # If stream is not specified, sys. stderr is used
            log_handler = logging.StreamHandler(sys.stdout)
            log_handler.setFormatter(FFFormatter(datefmt="%H:%M:%S"))
            logging.getLogger().addHandler(log_handler)
    else:
        # when no file is specified, writes to stderr
        logging.basicConfig(force=True)

    # logging.basicConfig(level = INFO, ...) spams library INFO messages to logs; 
    # possibly using only ff_log is better 
    # reducing plotly log spam
    # logging.getLogger('kaleido').setLevel(logging.WARNING)
    # logging.getLogger('choreographer').setLevel(logging.WARNING)
    # logging.getLogger('rpy2').setLevel(logging.WARNING)
    # logging.getLogger('rpy2').addFilter(lambda r: 'PATH' not in r.getMessage())

    logging.getLogger('bglabutils').setLevel(level=level)
    
    ff_log.setLevel(level=level)

