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
    """Same as intersect sets, but keeps order; Consider pandas.Index instead of list if you here"""    
    return [el for el in items if el in valid_items]


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


'''
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
'''


def format_dict(items: dict, separator: str = ' -> ', item_separator: str = ', ') -> str:
    str_items = [f'{k}{separator}{v}' for k, v in items.items()]
    return item_separator.join(str_items)
