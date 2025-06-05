import zipfile
from pathlib import Path
from typing import List, Union
from zipfile import ZipFile


def tag_to_fname(dir: Path, prefix, tag, ext, must_exist):
    # meaning of tag here is unique file name ending
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


def create_archive(arc_path, folders: Union[List[str], str], top_folder, include_fmasks, exclude_files: List[Path]):
    if type(folders) is str:
        folders = [folders]

    folders = [Path(dir) for dir in folders]
    files = []
    for folder in folders:
        for mask in include_fmasks:
            files += list(folder.glob(mask))
    files = set(files) - set(exclude_files)

    with ZipFile(arc_path, 'w', zipfile.ZIP_DEFLATED) as myzip:
        for file in files:
            relative_path = file.relative_to(top_folder)
            myzip.write(file, relative_path)
