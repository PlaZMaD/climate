import contextlib
import logging
from typing import Callable


@contextlib.contextmanager
def catch(on_exception: Callable = None, err_types=Exception):
    if not err_types:
        yield
        return
    
    try:
        yield
    except err_types as e:
        if on_exception:
            on_exception(e)


def fix_strs_case(strs: list[str], correct_case: list[str]):
    correct_l_to_correct = {c.lower(): c for c in correct_case}
    if len(correct_l_to_correct) != len(correct_case):
        raise Exception('Possibly correct_case contains duplicates with different cases')
    
    missing = [c for c in strs if c.lower() in correct_l_to_correct]
    new_strs = [correct_l_to_correct.get(c.lower(), c) for c in strs]
    renames = [(s, n) for s, n in zip(strs, new_strs) if s != n]
    return new_strs, renames, missing


@contextlib.contextmanager
def switch_log_level(level, logger_name=None):
    logger = logging.getLogger(logger_name)
    old_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(old_level)


''' was used to save-load time convert functions, but better to avoid
def func_to_str(fn: Callable) -> str:
    return inspect.getsource(fn).strip()


def str_to_func(code: str) -> Callable:
    """
    WARNNG: unsafe, str may contain undesirable code
    code: must contain all imports too
    """
    ns = {}
    exec("import pandas as pd", globals(), ns)
    exec(code, globals(), ns)

    # def src_func(*args, **kwargs):
    #     # import pandas as pd
    #
    #     ns = {'pd': pd}
    #     result = ns['my_datetime_converter'](df)
    #     return exec(code, {'args': args, 'kwargs': kwargs})

    func = list(ns.values())[1]
    assert callable(func)
    return func
'''


def gen_enum_info(enum_class) -> str:
    return ", ".join(m.name for m in enum_class)


def is_protected_method(name):
    return name.startswith("_")


