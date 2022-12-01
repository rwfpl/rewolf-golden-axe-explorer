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

from dataclasses import dataclass
from typing import List, Tuple
import struct

STRUCT_USHORT_unpack = struct.Struct('<H').unpack
STRUCT_UINT_unpack = struct.Struct('<I').unpack


@dataclass
class ClippingBox:
    x_adjust: int
    y_adjust: int
    width: int
    height: int


@dataclass
class Color:
    r: int
    g: int
    b: int

    def tuple(self) -> Tuple[int, int, int]:
        return self.r, self.g, self.b


@dataclass
class ImageSize:
    width: int
    height: int


@dataclass
class Palette:
    colors: List[Color]
    index: int    
    palette_start_index: int = 0


@dataclass
class SpriteDescriptor:
    id: int
    width: int
    height: int
    x: int
    y: int
    data: bytearray

    def minColor(self) -> int:
        return min(self.data)
