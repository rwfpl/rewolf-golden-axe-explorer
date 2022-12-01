# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from galzw import Galzw
from pixeldecoder import Pixeldecoder


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class GoldenaxeParser(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.sprites_number = self._io.read_u2le()
        self.sprites = [None] * (self.sprites_number)
        for i in range(self.sprites_number):
            self.sprites[i] = GoldenaxeParser.SpriteEntry(self._io, self, self._root)


    class SpriteEntry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset = self._io.read_u2le()
            self.size = self._io.read_u2le()

        @property
        def magic(self):
            if hasattr(self, '_m_magic'):
                return self._m_magic if hasattr(self, '_m_magic') else None

            _pos = self._io.pos()
            self._io.seek((self.offset << 4))
            self._m_magic = self._io.read_bytes(10)
            self._io.seek(_pos)
            return self._m_magic if hasattr(self, '_m_magic') else None

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data if hasattr(self, '_m_data') else None

            _pos = self._io.pos()
            self._io.seek(((self.offset << 4) + 10))
            self._raw__raw__m_data = self._io.read_bytes(((self.size << 4) - 10))
            _process = Galzw()
            self._raw__m_data = _process.decode(self._raw__raw__m_data)
            _io__raw__m_data = KaitaiStream(BytesIO(self._raw__m_data))
            self._m_data = GoldenaxeParser.DecompressedSprite(_io__raw__m_data, self, self._root)
            self._io.seek(_pos)
            return self._m_data if hasattr(self, '_m_data') else None


    class DecompressedSprite(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(2)
            if not self.magic == b"\xFF\xFF":
                raise kaitaistruct.ValidationNotEqualError(b"\xFF\xFF", self.magic, self._io, u"/types/decompressed_sprite/seq/0")
            self.sprites_number = self._io.read_u2le()
            self.unk00 = self._io.read_u2le()
            self.unk01 = [None] * ((self.unk00 // 2 - 3))
            for i in range((self.unk00 // 2 - 3)):
                self.unk01[i] = self._io.read_u2le()

            self.sprite = [None] * (self.sprites_number)
            for i in range(self.sprites_number):
                self.sprite[i] = GoldenaxeParser.SpriteBlob(self._io, self, self._root)



    class SpriteBlob(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.sprite_data_size = self._io.read_u2le()
            self.width = self._io.read_u2le()
            self.height = self._io.read_u1()
            self.unk01 = self._io.read_u1()
            self.pixel_delta = self._io.read_u1()
            self.unk02_1 = self._io.read_u1()
            self.unk03 = self._io.read_u2le()
            self.unk04 = self._io.read_u2le()
            self.unk05 = self._io.read_u2le()
            self.unk06 = self._io.read_u2le()
            self.unk07 = self._io.read_s2le()
            self.unk08 = self._io.read_s2le()
            self.unk09 = self._io.read_u2le()
            self.unk10 = self._io.read_u2le()
            self.unk11 = self._io.read_s2le()
            self.unk12 = self._io.read_s2le()
            self.unk13 = self._io.read_u2le()
            self.unk14 = self._io.read_u2le()
            self._raw_sprite_data = self._io.read_bytes((self.sprite_data_size - 32))
            _process = Pixeldecoder(self.pixel_delta)
            self.sprite_data = _process.decode(self._raw_sprite_data)



