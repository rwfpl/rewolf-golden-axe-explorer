
class Pixeldecoder:

    def __init__(self, delta: int) -> None:
        self.delta = delta

    def decode(self, pixels: memoryview) -> bytearray:
        cur_off = 0
        output = bytearray()
        while cur_off < len(pixels):
            if pixels[cur_off] < 0x80:
                output.extend([pixels[cur_off + 1]]*pixels[cur_off])
                cur_off += 2
            else:
                c = 256 - pixels[cur_off]
                output.extend(
                    p if p else p for p in pixels[cur_off + 1:cur_off + 1 + c])
                cur_off += 1 + c
        return output
