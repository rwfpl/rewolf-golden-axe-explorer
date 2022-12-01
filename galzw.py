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

from typing import DefaultDict
from bitreader import BitReader
from collections import defaultdict
import binascii


class Galzw:
    flag90: bool
    decompressed: bytearray

    def __storeByte(self, byte: int) -> None:
        if not self.flag90:
            if byte == 0x90:
                self.flag90 = True
            else:
                self.flag90data = byte
                self.decompressed.append(byte)
        else:
            self.flag90 = False
            if byte == 0:
                self.decompressed.append(0x90)
            else:
                self.decompressed.extend([self.flag90data] * (byte-1))

    def decode(self, compressed_data: memoryview) -> bytes:
        # print(binascii.hexlify(compressed_data))
        self.flag90 = False
        self.flag90data = -1
        self.decompressed = bytearray()

        br = BitReader(compressed_data)
        d: DefaultDict[int, int] = defaultdict(int)
        htab = {i: i for i in range(0, 256)}

        C = 8
        MAX_CODE_BITS = 12
        M_CLR = 1 << C
        req_bits = C + 1
        next_code = M_CLR + 1
        next_shift = 1 << req_bits
        finchar = br.getBits(req_bits)
        oldcode = finchar
        self.__storeByte(finchar)

        while not br.isEnd():
            cur_code = br.getBits(req_bits)
            if cur_code == M_CLR:
                br.clear()
                req_bits = C + 1
                next_code = M_CLR
                next_shift = 1 << req_bits
                cur_code = br.getBits(req_bits)
            if cur_code == -1:
                return bytes(self.decompressed)

            incode = cur_code
            output = []
            if next_code <= cur_code:
                output.append(finchar)
                cur_code = oldcode

            while cur_code >= M_CLR:
                if cur_code not in htab:
                    #print('missing code in htab: ', hex(cur_code), br.data_pos, len(compressed_data), br.bits_len, br.bits_len/8.0, hex(br.bits), hex(max(htab.keys())))
                    return bytes(self.decompressed)
                output.append(htab[cur_code])
                #print('d:', hex(cur_code), hex(d[cur_code]))
                cur_code = d[cur_code]

            finchar = htab[cur_code]
            output.append(finchar)

            for b in reversed(output):
                self.__storeByte(b)

            if next_code < 1 << MAX_CODE_BITS:
                htab[next_code] = finchar
                d[next_code] = oldcode
                if next_code == oldcode:
                    print('endless loop ', next_code,
                          hex(len(self.decompressed)))
                    return bytes(self.decompressed)
                next_code += 1
                if next_code >= next_shift:
                    if req_bits < MAX_CODE_BITS:
                        req_bits += 1
                        next_shift = 1 << req_bits

            oldcode = incode
        return bytes(self.decompressed)
