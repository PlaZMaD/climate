from pathlib import Path
from typing import List, Union
from warnings import warn


def tag_to_fname(dir: Path, prefix, tag, ext, must_exist):
    # meaning of tags here is unique file name endings
    # Test_site_2024_Hd_f.png -> tag is Hd_f

    fname = dir / (prefix + '_' + tag + ext)
    if must_exist and not fname.exists():
        return None
    else:
        return fname


def replace_fname_end(path: Path, tag: str, new_tag: str):
    return path.parent / path.name.replace(tag + '.', new_tag + '.')


def ensure_empty_dir(folder: Union[str, Path]):
    if type(folder) is str:
        folder = Path(folder)

    folder.mkdir(parents=True, exist_ok=True)
    for path in folder.iterdir():
        if path.is_file():
            path.unlink()
