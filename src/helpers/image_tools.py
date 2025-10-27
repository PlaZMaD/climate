import itertools
from enum import Enum, auto
from warnings import warn

import PIL
import numpy as np
from PIL import Image, ImageChops


class Direction(Enum):
    VERTICAL, HORIZONTAL = auto(), auto()


def crop_monocolor_borders(img, sides='LTRB', col=None, margin=10):
    """ Removes empty space on image sides """
    
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    
    edge_colors = list(map(img_rgb.getpixel, [(0, 0), (w - 1, h - 1), (w - 1, 0), (0, h - 1)]))
    if len(set(edge_colors)) > 1:
        warn('Cannot crop image, border color inconsistent')
        return img
    
    if not col:
        col = img_rgb.getpixel((0, 0))
    
    bg = Image.new("RGB", img_rgb.size, col)
    diff = ImageChops.difference(img_rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    
    bbox_crop = diff.getbbox()
    bbox = img_rgb.getbbox()
    
    if not bbox_crop:
        warn('Cannot crop image, border color inconsistent')
        return img
    
    bbox_crop_mg = (max(bbox_crop[0] - margin, 0), max(bbox_crop[1] - margin, 0),
                    min(bbox_crop[2] + margin, bbox[2]), min(bbox_crop[3] + margin, bbox[3]))
    mask = np.array(['L' in sides, 'T' in sides, 'R' in sides, 'B' in sides])
    bbox_final = tuple(np.where(mask, bbox_crop_mg, bbox))
    return img.crop(bbox_final)


def ungrid_image(img: PIL.Image, nx=1, ny=1, flatten=False):
    """
    For example, to split image on left and right parts:
        ungrid_image(img, nx=2, True)
    Without flatten=True returns row major [tile_j][tile_i]: PIL.Image
    """
    
    w, h = img.size
    assert w >= nx > 0 and h >= ny > 0
    cw, ch = w // nx, h // ny
    
    if w % nx != 0 or h % ny != 0:
        warn('Unexpected image size for pixel-perfect subdivision. Tiles will match cropped source image.')
    
    def box(i, j):
        # left, top, right, bottom for (i, j) tile
        return i * cw, j * ch, (i + 1) * cw, (j + 1) * ch
    
    res = [[img.crop(box(i, j)) for i in range(nx)] for j in range(ny)]
    return list(itertools.chain.from_iterable(res)) if flatten else res


def grid_images(images, max_horiz=np.iinfo(int).max):
    """ Combines images in row or column or both depending on max_horiz arg """
    
    n_images = len(images)
    n_horiz = min(n_images, max_horiz)
    h_sizes, v_sizes = [0] * n_horiz, [0] * (n_images // n_horiz)
    for i, im in enumerate(images):
        h, v = i % n_horiz, i // n_horiz
        h_sizes[h] = max(h_sizes[h], im.size[0])
        v_sizes[v] = max(v_sizes[v], im.size[1])
    
    h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
    im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
    for i, im in enumerate(images):
        im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
    return im_grid


def remove_strip(img: np.array, strip_axis: Direction, percent_at, margin=10):
    """
    Removes empty rectangle around vertical or horizontal cut:
    cuts an image, crops space around cut on both parts, joins back
    """
    
    w, h = img.size
    assert 0 <= percent_at <= 1
    
    if strip_axis == Direction.VERTICAL:
        imgs = [img.crop((0, 0, w * percent_at, h)),
                img.crop((w * percent_at, 0, w, h))]
        imgs = [crop_monocolor_borders(imgs[0], sides='R', margin=margin),
                crop_monocolor_borders(imgs[1], sides='L', margin=margin)]
        return grid_images(imgs, 2)
    elif strip_axis == Direction.HORIZONTAL:
        imgs = [img.crop((0, 0, w, h * percent_at)),
                img.crop((0, h * percent_at, w, h))]
        imgs = [crop_monocolor_borders(imgs[0], sides='B', margin=margin),
                crop_monocolor_borders(imgs[1], sides='T', margin=margin)]
        return grid_images(imgs, 1)
