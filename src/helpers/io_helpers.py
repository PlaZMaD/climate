import re
import zipfile
from pathlib import Path
from zipfile import ZipFile

from src.helpers.py_helpers import ensure_list


# Naming reminder: fpath (= file), dpath (= dir or folder)

def find_unique_file(dpath: Path, mask: str) -> Path | None:
    fpaths = list(dpath.glob(mask))
    if len(fpaths) > 1:
        raise Exception(f'Excepted none or one, but multiple files matching {mask} found: {fpaths}')
    if len(fpaths) == 1:
        return fpaths[0]
    else:
        return None


def ensure_path(arg: Path | str) -> Path:
    return arg if isinstance(arg, Path) else Path(arg)


def tag_to_fpath(parent_dir: Path, prefix, tag, ext, must_exist):
    # meaning of tag here is unique file name ending
    # Test_site_2024_Hd_f.png -> tag is Hd_f
    
    fpath = parent_dir / (prefix + '_' + tag + ext)
    if must_exist and not fpath.exists():
        return None
    else:
        return fpath


def replace_fname_end(fpath: Path, tag: str, new_tag: str):
    return fpath.parent / fpath.name.replace(tag + '.', new_tag + '.')


def ensure_empty_dir(dpath: str | Path):
    dpath = Path(dpath)
    
    dpath.mkdir(parents=True, exist_ok=True)
    for path in dpath.iterdir():
        if path.is_file():
            path.unlink()


def create_archive(arc_path: Path | str, dirs: list[Path | str] | Path | str,
                   top_dir: Path | str, include_fmasks, exclude_files: list[Path | str]):
    dirs = ensure_list(dirs, transform_func=ensure_path)
    exclude_files = ensure_list(exclude_files, transform_func=ensure_path)
    
    files = []
    for dpath in dirs:
        for mask in include_fmasks:
            files += list(dpath.glob(mask))
    files = set(files) - set(exclude_files)
    
    with ZipFile(arc_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            relative_path = file.relative_to(top_dir)
            zf.write(file, relative_path)


def find_in_files(root_dir: Path | str, fname_regex='.*', find_regex: str = None):
    # fname_regex multiple extensions example '.*\.(py|R|r)$'
    # to exclude, add at the start: ^(?!.*ias_error_check)
    root_dir = Path(root_dir)
    
    all_fpaths = list(root_dir.glob('**/*'))
    fpaths = [f for f in all_fpaths if re.match(pattern=fname_regex, string=str(f))]
    files_with_matches = [f for f in fpaths if open(f, 'r').read().find(find_regex) != -1]
    return files_with_matches
