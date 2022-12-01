'''
 Golden Axe explorer
 
 Copyright (c) 2021 ReWolf
 http://blog.rewolf.pl/
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published
 by the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.
 
 You should have received a copy of the GNU Lesser General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from functools import cache
from typing import List, Tuple
from PIL import Image
import itertools
import gatypes


def AddBorders(data: bytearray, width: int, height: int, left: int, right: int,
               top: int, bottom: int, color: int) -> bytearray:
    ret = bytearray()
    for y in range(0, height):
        ret.extend(bytearray([color] * left))
        ret.extend(data[y * width:y * width + width])
        ret.extend(bytearray([color] * right))
    if top != 0:
        tmp = bytearray([color] * ((width + left + right) * top))
        tmp.extend(ret)
        ret = tmp
    if bottom != 0:
        ret.extend(bytearray([color] * ((width + left + right) * bottom)))
    return ret


def AddClippingBox(sprite: gatypes.SpriteDescriptor,
                   clipping_box: gatypes.ClippingBox, color: int) -> bytearray:
    left_border = clipping_box.x_adjust - sprite.x
    right_border = clipping_box.width - sprite.width - left_border
    top_border = clipping_box.y_adjust - sprite.y
    bottom_border = clipping_box.height - sprite.height - top_border
    return AddBorders(sprite.data, sprite.width, sprite.height, left_border,
                      right_border, top_border, bottom_border, color)


MULT = 255.0 / 63


def ApplyPalette(buffer: bytearray, palette: gatypes.Palette) -> bytes:
    colors = [gatypes.Color(0, 0, 0)] * palette.palette_start_index
    colors.extend(palette.colors)
    colors.extend([gatypes.Color(0, 0, 0)] *
                  (256 - palette.palette_start_index))
    return bytes(
        itertools.chain.from_iterable([colors[c].tuple() for c in buffer]))


def CalculateClippingBox(
        sprites: List[gatypes.SpriteDescriptor]) -> gatypes.ClippingBox:
    min_x = min(sprites, key=lambda s: s.x).x
    min_y = min(sprites, key=lambda s: s.y).y
    max_x_w = max(sprites, key=lambda s: s.x + s.width)
    max_y_h = max(sprites, key=lambda s: s.y + s.height)
    width = max_x_w.x + max_x_w.width - min_x
    height = max_y_h.y + max_y_h.height - min_y
    x_adjust = max(sprites, key=lambda s: s.x).x
    y_adjust = max(sprites, key=lambda s: s.y).y
    return gatypes.ClippingBox(x_adjust, y_adjust, width, height)


def GetSpritesImage(sprites: List[gatypes.SpriteDescriptor],
                    palette: gatypes.Palette,
                    max_width: int = 1024) -> Image.Image:
    max_height = 0
    current_x = 0
    current_y = 0
    for sprite in sprites:
        if current_x + sprite.width > max_width:
            current_x = 0
            current_y += max_height
        current_x += sprite.width
        if sprite.height > max_height:
            max_height = sprite.height
    ret = Image.new("RGB", (
        max_width,
        current_y + max_height,
    ),
        color=(255, 255, 255))
    max_height = 0
    current_x = 0
    current_y = 0
    for sprite in sprites:
        if current_x + sprite.width > max_width:
            current_x = 0
            current_y += max_height
        colored_sprite = ApplyPalette(sprite.data,
                                      palette)
        img = Image.frombuffer('RGB', (sprite.width, sprite.height),
                               colored_sprite, 'raw', 'RGB', 0, 1)
        ret.paste(img, box=(current_x, current_y))
        current_x += sprite.width
        if sprite.height > max_height:
            max_height = sprite.height
    return ret


def SaveAnimatedImage(filename: str, sprites: List[gatypes.SpriteDescriptor], palette: gatypes.Palette, speed: float) -> Tuple[bool, str]:
    clipping_box = CalculateClippingBox(sprites)
    images = []
    for s in sprites:
        buf = AddClippingBox(s, clipping_box, 0xFF)
        colored_sprite = ApplyPalette(
            buf, palette)
        images.append(
            Image.frombuffer('RGB',
                             (clipping_box.width, clipping_box.height),
                             colored_sprite, 'raw', 'RGB', 0, 1))
    try:
        images[0].save(filename,
                       save_all=True,
                       append_images=images[1:],
                       optimize=True,
                       duration=round(1000 / speed),
                       loop=0)
    except ValueError as e:
        return False, str(e)
    return True, ''
