meta:
  id: goldenaxe_parser
  file-extension: spr
  endian: le
seq:
  - id: sprites_number
    type: u2
  - id: sprites
    type: sprite_entry
    repeat: expr
    repeat-expr: sprites_number

types:
  sprite_entry:
    seq:
      - id: offset
        type: u2
      - id: size
        type: u2
    instances:
      magic:
        pos: offset << 4
        size: 10
        contents: [GOLDENAXE, 0x0C]

      data:
        pos: (offset << 4) + 10
        size: (size << 4) - 10
        process: galzw
        type: decompressed_sprite

  decompressed_sprite:
    seq:
      - id: magic
        contents: [ 0xFF, 0xFF ]
      - id: sprites_number
        type: u2
        
      - id: unk00
        type: u2
      - id: unk01
        type: u2
        repeat: expr
        repeat-expr: (unk00/2)-3

      - id: sprite
        type: sprite_blob
        repeat: expr
        repeat-expr: sprites_number

  sprite_blob:
    seq:
      - id: sprite_data_size
        type: u2
      - id: width
        type: u2
      - id: height
        type: u1
      - id: unk01
        type: u1
      - id: pixel_delta
        type: u1
      - id: unk02_1
        type: u1
      - id: unk03
        type: u2
      - id: unk04
        type: u2
      - id: unk05
        type: u2
      - id: unk06
        type: u2
      - id: unk07
        type: s2
      - id: unk08
        type: s2
      - id: unk09
        type: u2
      - id: unk10
        type: u2
      - id: unk11
        type: s2
      - id: unk12
        type: s2
      - id: unk13
        type: u2
      - id: unk14
        type: u2
      - id: sprite_data
        size: sprite_data_size - 32
        process: pixeldecoder(pixel_delta)