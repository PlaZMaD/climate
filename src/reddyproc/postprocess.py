import zipfile
from pathlib import Path
from typing import List
from zipfile import ZipFile


def create_archive(dir, arc_fname, include_fmasks, exclude_files: List[Path]):
    # move out of draw_graphs later

    folder = Path(dir)
    files = [path for mask in include_fmasks for path in list(folder.glob(mask))]
    files = set(files) - set(exclude_files)

    arc_path = folder / arc_fname
    with ZipFile(arc_path, 'w', zipfile.ZIP_DEFLATED) as myzip:
        for file in files:
            myzip.write(file, file.name)

    return arc_path
