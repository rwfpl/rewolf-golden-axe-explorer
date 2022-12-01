meta:
  id: lzwfile
  file-extension: [CHR, MDI, MAP]

seq:
  - id: magic
    size: 10
    contents: [GOLDENAXE, 0x0C]
  - id: raw
    size-eos: true
    process: galzw
