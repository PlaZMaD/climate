# Reminder: this is duplicate of specific cell used for test purposes, it is outdated or ahead frequently

from pathlib import Path

import src.ipynb_globals as ig
from src.colab_routines import colab_add_download_button
from src.helpers.io_helpers import create_archive
from src.reddyproc.postprocess_graphs import RepOutputHandler, RepImgTagHandler, RepOutputGen

rep_out_dir = Path(ig.rep.options.output_dir)
tag_handler = RepImgTagHandler(main_path=rep_out_dir, rep_options=ig.rep, img_ext='.png')
eog = RepOutputGen(tag_handler)

output_sequence: tuple[list[str] | str, ...] = (
    "## Тепловые карты",
    eog.hmap_compare_row('NEE_*'),
    eog.hmap_compare_row('LE_f'),
    eog.hmap_compare_row('H_f'),
    "## Суточный ход",
    eog.diurnal_cycle_row('NEE_*'),
    eog.diurnal_cycle_row('LE_f'),
    eog.diurnal_cycle_row('H_f'),
    "## 30-минутные потоки и суточные средние",
    eog.flux_compare_row('NEE_*'),
    eog.flux_compare_row('LE_f'),
    eog.flux_compare_row('H_f')
)

eio = RepOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=ig.rep.out_info)
eio.prepare_images_safe()
ig.arc_exclude_files = eio.img_proc.raw_img_duplicates

eproc_arc_path = rep_out_dir / (ig.rep.out_info.fnames_prefix + '.zip')
create_archive(arc_path=eproc_arc_path, folders=rep_out_dir, top_folder=rep_out_dir,
               include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eio.img_proc.raw_img_duplicates)

colab_add_download_button(eproc_arc_path, 'Download eddyproc outputs')

eio.display_images_safe()

tag_handler.display_tag_info(eio.extended_tags())
