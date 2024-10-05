import textwrap
import warnings
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import List
from warnings import warn

from IPython.core.display import Markdown
from IPython.display import display

from PIL import Image

import src.helpers.os_helpers  # noqa: F401
from src.helpers.py_helpers import catch
from src.ipynb_helpers import display_image_row
from src.helpers.io_helpers import tag_to_fname
from src.helpers.image_tools import crop_monocolor_borders, Direction, grid_images, remove_strip, \
    ungrid_image

PostProcSuffixes = SimpleNamespace(HMAPS='hmaps', COMPACT='c')
EddyPrefixes = SimpleNamespace(HEAT_MAP='FP', FLUX='Flux', DIURNAL='DC', DAILY_SUM='DSum', DAILY_SUMU='DSumU')


class EProcImgTagHandler:
    def __init__(self, main_path, eproc_options, img_ext='.png'):
        self.main_path = Path(main_path)

        is_ustar = eproc_options.options.is_to_apply_u_star_filtering
        self.nee_f_suffix = 'uStar_f' if is_ustar else 'f'

        self.loc_prefix = eproc_options.out_info.fnames_prefix
        self.img_ext = img_ext

    def tag_to_img_fname(self, tag, must_exist=True, warn_if_missing=True):
        fname = tag_to_fname(self.main_path, self.loc_prefix, tag, self.img_ext, must_exist)
        if warn_if_missing and not fname:
            warn(f"Expected image is missing: {tag}")

        return fname

    def tags_to_img_fnames(self, tags, exclude_missing=True, must_exist=True, warn_if_missing=True):
        res = {tag: self.tag_to_img_fname(tag, must_exist, warn_if_missing) for tag in tags}
        missing_image_tags = [k for k, v in res.items() if not v]

        if exclude_missing:
            for t in missing_image_tags:
                res.pop(t)
        return res

    @staticmethod
    def test_tag(tag, prefix, suffix):
        if prefix and not tag.startswith(prefix + '_'):
            return False
        if suffix and not tag.endswith('_' + suffix):
            return False
        return True

    def raw_tag(self, tag: str):
        if tag.endswith(self.nee_f_suffix):
            return self.remove_suffix(tag, self.nee_f_suffix)
        elif tag.endswith('_f'):
            return self.remove_suffix(tag, 'f')
        else:
            assert False, f'Cannot derive expected unprocessed image tag for {tag}'

    @staticmethod
    def remove_suffix(tag: str, expected_suffix):
        sf = '_' + expected_suffix
        assert tag.endswith(sf)
        return tag.rstrip(sf)

    def display_tag_info(self, extended_tags):
        img_names = [Path(path).name for path in Path(self.main_path).glob(self.loc_prefix + '_*' + self.img_ext)]
        possible_tags = [name.removeprefix(self.loc_prefix + '_').removesuffix(self.img_ext) for name in img_names]

        def detect_prefix(s, prefixes):
            s = tag.partition('_')[0]
            if s not in prefixes:
                warn('Unexpected file name start: ' + s)
            return s

        prefixes_list = list(vars(EddyPrefixes).values())
        final_print = '\nUnused and ' + '[used]' + ' tags in output_sequence: '
        last_prefix = ''
        for tag in sorted(possible_tags):
            prefix = detect_prefix(tag, prefixes_list)
            if last_prefix != prefix:
                final_print += '\n\n'
            final_print += f'[{tag}]' if tag in extended_tags else tag
            final_print += ' '
            last_prefix = prefix

        lines = textwrap.wrap(final_print + '\n', replace_whitespace=False,
                              break_long_words=False)

        class PyPrint:
            BOLD = '\033[1m'
            END = '\033[0m'

        for line in lines:
            repl = line.replace('[', PyPrint.BOLD).replace(']', PyPrint.END)
            print(repl)


class EddyImgPostProcess:
    def __init__(self, total_years, tag_handler):
        self.total_years = total_years
        self.tag_handler = tag_handler
        self.raw_img_duplicates: List[Path] = []

    def ungrid_heatmap(self, img):
        tile_count = self.total_years + 1
        row_count = (tile_count - 1) // 3 + 1
        tiles_2d = ungrid_image(img, nx=3, ny=row_count)
        assert len(tiles_2d) == row_count and len(tiles_2d[0]) == 3

        tiles_ordered = [elem for row in tiles_2d for elem in row]
        legend_tile = tiles_ordered[tile_count - 1]

        year_tiles_stacked_vertically = grid_images(tiles_ordered[0: tile_count - 1], max_horiz=1)
        # just a copy of same legend
        legend_tiles_stacked_vertically = grid_images([legend_tile] * (tile_count - 1), max_horiz=1)
        return year_tiles_stacked_vertically, legend_tiles_stacked_vertically

    @staticmethod
    def compact_title_row(img, row_count):
        rows = ungrid_image(img, ny=row_count, flatten=True)
        title = remove_strip(rows[0], Direction.HORIZONTAL, 0.5)
        c_title = crop_monocolor_borders(title, sides='TB')
        fixed = grid_images([c_title] + rows[1: row_count], 1)
        return fixed

    def load_heatmap(self, path):
        img = Image.open(path)

        # in case of multiple years, they are columns
        maps, legends = self.ungrid_heatmap(img)
        cmap = crop_monocolor_borders(maps, sides='LR')
        clegend = crop_monocolor_borders(legends, sides='LR')
        return cmap, clegend

    def get_legend_scale(self, legend_col):
        legend = ungrid_image(legend_col, ny=self.total_years, flatten=True)[0]
        scale = ungrid_image(legend, ny=3, flatten=True)[1]
        return scale

    def process_heatmaps(self, target_tag):
        raw_tag_f = self.tag_handler.remove_suffix(target_tag, PostProcSuffixes.HMAPS)
        raw_tag = self.tag_handler.raw_tag(raw_tag_f)

        tps = self.tag_handler.tags_to_img_fnames([raw_tag, raw_tag_f], must_exist=True)
        if len(tps) != 2:
            return
        else:
            path, path_f = tps.values()

        maps, legends = self.load_heatmap(path)
        maps_f, legends_f = self.load_heatmap(path_f)

        if self.get_legend_scale(legends) != self.get_legend_scale(legends_f):
            print(f'\n\n Legends of heatmaps do not match, check original output of EProc for {target_tag} \n')
        merged = grid_images([maps, maps_f, legends_f], 3)

        merged.save(self.tag_handler.tag_to_img_fname(target_tag, must_exist=False))
        self.raw_img_duplicates += [path, path_f]

    def process_flux(self, target_tag):
        raw_tag = self.tag_handler.remove_suffix(target_tag, PostProcSuffixes.COMPACT)

        path = self.tag_handler.tag_to_img_fname(raw_tag, must_exist=True)
        if not path:
            return
        img = Image.open(path)

        fixed = self.compact_title_row(img, self.total_years + 1)

        fixed.save(self.tag_handler.tag_to_img_fname(target_tag, must_exist=False))
        self.raw_img_duplicates += [path]

    def process_diurnal_cycle(self, target_tag):
        raw_tag = self.tag_handler.remove_suffix(target_tag, PostProcSuffixes.COMPACT)

        path = self.tag_handler.tag_to_img_fname(raw_tag, must_exist=True)
        if not path:
            return
        img = Image.open(path)

        fixed = self.compact_title_row(img, 5)

        fixed.save(self.tag_handler.tag_to_img_fname(target_tag, must_exist=False))
        self.raw_img_duplicates += [path]


class EProcOutputGen:
    # output is declared as auto generated on each run list of image tags
    # tags mean unique suffixes of image file names,
    # i.e. for 'tv_fy4_22-14_21-24_FP_Rg_f.png' tag is 'FP_Rg_f'
    # this allows both default auto-detected order of cell output by this class
    # or custom order if to declare output list manually in the notebook cell
    # auto generation is nessesary because order depends on reddyproc options

    def __init__(self, tag_handler: EProcImgTagHandler):
        self.tag_handler = tag_handler

    def col_name_and_suffix(self, col_name):
        # * in col_name means 'uStar_f' or 'f'
        cn, sf = col_name.split('_')
        if sf == '*':
            sf = self.tag_handler.nee_f_suffix
        return cn, sf

    def hmap_compare_row(self, col_name) -> List[str]:
        cn, sf = self.col_name_and_suffix(col_name)
        fp, hm = EddyPrefixes.HEAT_MAP, PostProcSuffixes.HMAPS
        return [f'{fp}_{cn}_{sf}_{hm}']

    def diurnal_cycle_row(self, col_name) -> List[str]:
        # for example, 'DC_NEE_uStar_f_compact'
        cn, sf = self.col_name_and_suffix(col_name)
        dc, ct = EddyPrefixes.DIURNAL, PostProcSuffixes.COMPACT
        return [f'{dc}_{cn}_{sf}_{ct}']

    def flux_compare_row(self, col_name) -> List[str]:
        # for example, ['Flux_NEE_compact', 'Flux_NEE_uStar_f_compact'],
        cn, sf = self.col_name_and_suffix(col_name)
        fl, ct = EddyPrefixes.FLUX, PostProcSuffixes.COMPACT
        return [f'{fl}_{cn}_{ct}', f'{fl}_{cn}_{sf}_{ct}']


class EProcOutputHandler:
    def __init__(self, output_sequence, tag_handler, out_info):
        self.output_sequence = output_sequence
        self.tag_handler = tag_handler

        total_years = out_info.end_year - out_info.start_year + 1
        assert total_years > 0
        self.img_proc = EddyImgPostProcess(total_years, tag_handler)

    def extended_tags(self):
        # flatten, exclude markdown text
        rows = [row for row in self.output_sequence if type(row) is list]
        return [tag for row in rows for tag in row]

    def prepare_images(self):
        ct = self.tag_handler.test_tag

        for tag in self.extended_tags():
            if ct(tag, EddyPrefixes.HEAT_MAP, PostProcSuffixes.HMAPS):
                self.img_proc.process_heatmaps(tag)
            elif ct(tag, EddyPrefixes.FLUX, PostProcSuffixes.COMPACT):
                self.img_proc.process_flux(tag)
            elif ct(tag, EddyPrefixes.DIURNAL, PostProcSuffixes.COMPACT):
                self.img_proc.process_diurnal_cycle(tag)
            else:
                check = [ct(tag, prefix=prefix, suffix=None) for prefix in list(vars(EddyPrefixes).values())]
                if len(check) != 1:
                    warn(f'Unrecognized tag: {tag}')

    def on_missing_file(self, e):
        print(str(e))

    def prepare_images_safe(self):
        with catch(self.on_missing_file, FileNotFoundError):
            self.prepare_images()

    def display_images(self):
        for output_step in self.output_sequence:
            if type(output_step) is str:
                title_text = output_step
                display(Markdown(title_text))
            elif type(output_step) is list:
                paths = self.tag_handler.tags_to_img_fnames(output_step)
                display_image_row(list(paths.values()))
            else:
                raise Exception("Wrong ig.output_sequence contents")

    def display_images_safe(self):
        with catch(self.on_missing_file, FileNotFoundError):
            self.display_images()