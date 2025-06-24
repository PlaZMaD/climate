import zipfile
from pathlib import Path
from typing import Union
from zipfile import ZipFile

from src.helpers.py_helpers import ensure_list
# TODO 3 type hints: A | B instead of Union - smth is wrong in pycharm 2024.1 and py 3-11

def ensure_path(arg: Union[Path, str]) -> Path:
	return arg if isinstance(arg, Path) else Path(arg)


def tag_to_fpath(folder: Path, prefix, tag, ext, must_exist):
	# meaning of tag here is unique file name ending
	# Test_site_2024_Hd_f.png -> tag is Hd_f

	fpath = folder / (prefix + '_' + tag + ext)
	if must_exist and not fpath.exists():
		return None
	else:
		return fpath


def replace_fname_end(fpath: Path, tag: str, new_tag: str):
	return fpath.parent / fpath.name.replace(tag + '.', new_tag + '.')


def ensure_empty_dir(folder: Union[str, Path]):
	folder = ensure_path(folder)

	folder.mkdir(parents=True, exist_ok=True)
	for path in folder.iterdir():
		if path.is_file():
			path.unlink()


def create_archive(arc_path: Union[Path, str], folders: Union[list[Union[Path, str]], Union[Path, str]],
                   top_folder: Union[Path, str], include_fmasks, exclude_files: list[Union[Path, str]]):

	folders = ensure_list(folders, transform_func=ensure_path)
	exclude_files = ensure_list(exclude_files, transform_func=ensure_path)

	files = []
	for folder in folders:
		for mask in include_fmasks:
			files += list(folder.glob(mask))
	files = set(files) - set(exclude_files)

	with ZipFile(arc_path, 'w', zipfile.ZIP_DEFLATED) as zf:
		for file in files:
			relative_path = file.relative_to(top_folder)
			zf.write(file, relative_path)
