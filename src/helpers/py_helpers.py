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


def invert_dict(d: dict):
    vals = d.values()
    vals_set = set(vals)
    if len(vals) != len(vals_set):
        raise Exception('Cannot invert dictionary with duplicate values')

    return {v: k for k, v in d.items()}


def replace_in_dict_by_values(d: dict, replacements: dict):
    assert set(replacements.values()) <= set(d.values())

    rd = invert_dict(d)
    rv = invert_dict(replacements)
    for k, v in rv.items():
        rd[k] = v
    return invert_dict(rd)


def fix_strs_case(strs: list[str], correct_case: list[str]):
    correct_l_to_correct = {c.lower(): c for c in correct_case}
    if len(correct_l_to_correct) != len(correct_case):
        raise Exception('Possibly correct_case contains duplicates with different cases')

    missing = [c for c in strs if c.lower() in correct_l_to_correct]
    new_strs = [correct_l_to_correct.get(c.lower(), c) for c in strs]
    renames = [(s, n) for s, n in zip(strs, new_strs) if s != n]
    return new_strs, renames, missing


def sort_fixed(items: list[str], fix_underscore: bool):
    # sort: ['NETRAD_1_1_1', 'PA_1_1_1', 'PPFD_IN_1_1_1', 'P_1_1_1']
    # fix_underscore = True: ['NETRAD_1_1_1', 'P_1_1_1', 'PA_1_1_1', 'PPFD_IN_1_1_1']
    def key(s):
        return s.replace('_', ' ') if fix_underscore else s

    return sorted(items, key=key)


def ensure_list(items, transform_func=None) -> list:
    if isinstance(items, list):
        ret = items
    else:
        ret = [items]

    if transform_func:
        return [transform_func(el) for el in ret]
    else:
        return ret


def intersect_list(items: list, valid_items: list) -> list:
    """Same as intersect sets, but keeps order"""
    return [el for el in items if el in valid_items]


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


def dict_remove_matches(inplace: dict, match: dict, keep_keys: list[str]):
    for k in match:
        if k not in inplace:
            continue
        if k in keep_keys:
            continue
            
        if inplace[k] == match[k]:
            del inplace[k]


def dict_replace(inplace: dict, replace: dict, skip_keys: list[str]):
    for k in inplace:
        if k not in replace:
            continue
        if k in skip_keys:
            continue
            
        if inplace[k] != replace[k]:
            inplace[k] = replace[k]


def is_protected_method(name):
    return name.startswith("_")


def format_dict(items: dict, separator: str = '->') -> str:
    str_items = [f'{k} {separator} {v}' for k, v in items.items()]
    return ', '.join(str_items)
