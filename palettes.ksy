meta:
  id: palettes
  file-extension: dat

seq:
  - id: palettes
    type: palette
    repeat: eos

types:
  color:
    seq:
      - id: r
        type: u1
      - id: g
        type: u1
      - id: b
        type: u1
  
  palette:
    seq:
      - id: palette_start_index
        type: u1
      - id: colors
        type: color
        repeat: expr
        repeat-expr: 16