""" Reminder: this is dev-only duplicate of specific ipynb cell, it is out of sync frequently """
from pathlib import Path

from src.ipynb_globals import *
from src.colab_routines import colab_add_download_button
from src.helpers.io_helpers import create_archive
from src.reddyproc.postprocess_graphs import RepImgTagHandler, RepOutputGen, RepOutputHandler

rep_out_dir = Path(config.reddyproc.output_dir)
tag_handler = RepImgTagHandler(main_path=rep_out_dir, rep_cfg=config.reddyproc, rep_out_info=gl.rep_out_info,
                               img_ext='.png')
rog = RepOutputGen(tag_handler)

output_sequence: tuple[str | list[str], ...] = (
    "## Тепловые карты",
    rog.hmap_compare_row('NEE_*'),
    rog.hmap_compare_row('LE_f'),
    rog.hmap_compare_row('H_f'),
    "## Суточный ход",
    rog.diurnal_cycle_row('NEE_*'),
    rog.diurnal_cycle_row('LE_f'),
    rog.diurnal_cycle_row('H_f'),
    "## 30-минутные потоки и суточные средние",
    rog.flux_compare_row('NEE_*'),
    rog.flux_compare_row('LE_f'),
    rog.flux_compare_row('H_f')
)

roh = RepOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=gl.rep_out_info)
roh.prepare_images_safe()
gl.rep_arc_exclude_files = roh.img_proc.raw_img_duplicates

rep_arc_path = rep_out_dir / (gl.rep_out_info.fnames_prefix + '.zip')
create_archive(arc_path=rep_arc_path, dirs=rep_out_dir, top_dir=rep_out_dir,
               include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=roh.img_proc.raw_img_duplicates)

colab_add_download_button(rep_arc_path, 'Download eddyproc outputs')

roh.display_images_safe()

tag_handler.display_tag_info(roh.extended_tags())
