'''
 Golden Axe tools.
 
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


def BitMask(n: int) -> int:
    return (1 << n) - 1


class BitReader:
    '''Bit reader specific to Golden Axe "buggy" implementation.'''

    def __init__(self, data: memoryview) -> None:
        self.data = data
        self.data_pos = 0
        self.bits = 0
        self.bits_len = 0
        self.cache_size = 0

    def isEnd(self) -> bool:
        return self.data_pos == len(self.data) and self.bits_len == 0

    def __fillCache(self) -> bool:
        self.bits = 0
        self.bits_len = 0
        cur = 0
        while cur < self.cache_size and self.data_pos < len(self.data):
            self.bits |= (self.data[self.data_pos] << self.bits_len)
            self.bits_len += 8
            self.data_pos += 1
            cur += 1
        if self.isEnd():
            return False
        return True

    def clear(self) -> None:
        self.bits = 0
        self.bits_len = 0
        self.cache_size = 0

    def getBits(self, n: int) -> int:
        self.cache_size = n
        r = 0
        if n <= self.bits_len:
            self.bits_len -= n
            r = self.bits & BitMask(n)
            self.bits >>= n
        else:
            r = self.bits
            blen = self.bits_len
            if not self.__fillCache():
                return -1
            r |= (self.getBits(n - blen) << blen)
        return r
