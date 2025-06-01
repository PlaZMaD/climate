import contextlib


@contextlib.contextmanager
def catch(on_exception=None, err_types=Exception):
    if not err_types:
        yield
        return

    try:
        yield
    except err_types as e:
        if on_exception:
            on_exception(e)


def invert_dict(dict):
    return {v: k for k, v in dict.items()}