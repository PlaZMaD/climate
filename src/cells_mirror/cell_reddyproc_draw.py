from typing import List, Tuple, Union

import src.ipynb_globals as ig
from src.reddyproc.postprocess import create_archive
from src.reddyproc.postprocess_graphs import EProcOutputHandler, EProcImgTagHandler, EProcOutputGen
from src.colab_routines import colab_add_download_button, colab_no_scroll

tag_handler = EProcImgTagHandler(main_path='output/reddyproc', eproc_options=ig.eddyproc, img_ext='.png')
eog = EProcOutputGen(tag_handler)

output_sequence: Tuple[Union[List[str], str], ...] = (
    "## Тепловые карты",
    eog.hmap_compare_row('NEE_*'),
    eog.hmap_compare_row('LE_f'),
    eog.hmap_compare_row('H_f'),
    "## Суточный ход",
    eog.diurnal_cycle_row('NEE_*'),
    eog.diurnal_cycle_row('LE_f'),
    eog.diurnal_cycle_row('H_f'),
    "## 30-минутные потоки",
    eog.flux_compare_row('NEE_*'),
    eog.flux_compare_row('LE_f'),
    eog.flux_compare_row('H_f')
)

eio = EProcOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=ig.eddyproc.out_info)
eio.prepare_images_safe()

arc_path = create_archive(dir='output/reddyproc', arc_fname=ig.eddyproc.out_info.fnames_prefix + '.zip',
                          include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eio.img_proc.raw_img_duplicates)
colab_add_download_button(arc_path, 'Download outputs')

colab_no_scroll()
eio.display_images_safe()

tag_handler.display_tag_info(eio.extended_tags())
