# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from galzw import Galzw


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Lzwfile(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(10)
        if not self.magic == b"\x47\x4F\x4C\x44\x45\x4E\x41\x58\x45\x0C":
            raise kaitaistruct.ValidationNotEqualError(b"\x47\x4F\x4C\x44\x45\x4E\x41\x58\x45\x0C", self.magic, self._io, u"/seq/0")
        self._raw_raw = self._io.read_bytes_full()
        _process = Galzw()
        self.raw = _process.decode(self._raw_raw)


