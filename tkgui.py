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
import time
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk
from threading import Thread
from typing import Callable, List, Dict

import pathlib

import gatypes
import graph_util

import goldenaxe_parser
import palettes
import lzwfile

from enum import Enum


class InputType(Enum):
    NONE = 0
    SPR_FILE = 1
    CHR_FILE = 2
    MAP_FILE = 3


class CustomListbox:

    def __init__(self, name: str, parent: tk.Frame, select_function: Callable, column: int):
        self.label = tk.Label(parent, text=name)
        self.label.grid(column=2*column, row=0, sticky='NW')
        self.scroll = tk.Scrollbar(parent, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            parent, yscrollcommand=self.scroll.set, exportselection=0)
        self.scroll.config(command=self.listbox.yview)
        self.listbox.grid(column=2*column, row=1, sticky='NESW')
        self.scroll.grid(column=2*column+1, row=1, sticky='NS')
        self.listbox.bind('<<ListboxSelect>>', select_function)


class PaletteListbox(CustomListbox):

    def __init__(self, name: str, parent: tk.Frame, select_function: Callable, column: int):
        super().__init__(name, parent, select_function, column)
        self.palettes: List[gatypes.Palette] = []
        self.palette_start_index = -1
        self.palettes_lb_mapping: Dict[int, int] = dict()

    def setPalettes(self, palettes: List[gatypes.Palette]) -> None:
        self.palettes = palettes

    def getSelectedPalette(self) -> gatypes.Palette:
        cs = self.listbox.curselection()
        if cs and cs[0] in self.palettes_lb_mapping:
            return self.palettes[self.palettes_lb_mapping[cs[0]]]
        return gatypes.Palette([], 0)

    def updatePalettesListBox(self, palette_start_index: int) -> None:
        if palette_start_index == self.palette_start_index:
            return
        self.palette_start_index = palette_start_index
        current_palette = self.getSelectedPalette()
        self.listbox.delete(0, tk.END)
        selected_index = -1
        self.palettes_lb_mapping.clear()
        for p in self.palettes:
            if p.palette_start_index != palette_start_index:
                continue
            self.listbox.insert(
                tk.END, 'Pal_{:X} idx: {:X} colors: {}'.format(p.index, p.palette_start_index, len(p.colors)))
            self.palettes_lb_mapping[self.listbox.size() - 1] = p.index
            if current_palette.index == p.index:
                selected_index = self.listbox.size() - 1
        if selected_index != -1:
            self.listbox.selection_set(selected_index)
        else:
            self.listbox.selection_set(0)


class PaletteFrame:

    def __init__(self, parent: tk.Frame, column: int, row: int):
        self.palette_frame = tk.Frame(parent)
        self.palette_frame.grid(column=column, row=row, columnspan=3, sticky='W')
        self.palette_boxes = []
        for i in range(0, 4):
            for j in range(0, 64):
                box = tk.Canvas(self.palette_frame,
                                width=12,
                                height=12,
                                bg='white')
                box.grid(column=j, row=i, sticky='W')
                self.palette_boxes.append(box)

    def updatePaletteFrame(self, palette: gatypes.Palette) -> None:
        colors = palette.colors
        for i in range(0, 256):
            if i >= palette.palette_start_index and i < palette.palette_start_index + len(palette.colors):
                color = colors[i - palette.palette_start_index]
                self.palette_boxes[i].configure(
                    bg='#' + format(color.r, '02x') + format(color.g, '02x') + format(color.b, '02x'))
            else:
                self.palette_boxes[i].configure(bg='white')

class ControlFrame:

    def __init__(self, parent: tk.Frame, column: int, row: int):
        pass

def isSupportedExt(filename: str) -> bool:
    return filename[-4:].lower() in frozenset(['.spr', '.chr', '.map'])


def getPaletteFromSprites(sprites: List[gatypes.SpriteDescriptor]) -> int:
    return max(map(lambda s: min(s.data), sprites)) & 0xF0

class Application(tk.Frame):
    def __init__(self, master=None) -> None:
        tk.Frame.__init__(self, master)

        self.palette_start_index = -1
        self.input_type = InputType.NONE
        self.photos: List[ImageTk.PhotoImage] = []
        self.sprites: List[gatypes.SpriteDescriptor] = []
        self.animation_thread_running = False
        self.close_when_thread_is_finished = False
        self.grid(sticky=tk.N + tk.S + tk.E + tk.W, padx=4, pady=4)
        self.createWidgets()
        self.master.protocol('WM_DELETE_WINDOW', lambda: self.onClose())

        if len(sys.argv) > 1 and sys.argv[1]:
            self.handleGameDirectoryChange(sys.argv[1])

    def handleGameDirectoryChange(self, game_dir: str):
        self.game_directory = game_dir
        self.string_game_dir.set(self.game_directory)
        self.parsePalDat(self.game_directory)
        self.loadGameDirectory(self.game_directory)

    def onClose(self) -> None:
        if self.animation_thread_running:
            self.close_when_thread_is_finished = True
            self.animation_enabled.set(0)
        else:
            self.master.destroy()

    def parsePalDat(self, filename: str) -> None:
        try:
            self.pal_dat = palettes.Palettes.from_file(
                os.path.join(filename, 'pal.dat'))
        except FileNotFoundError as e:
            messagebox.showerror('Error', str(e))
            return
        pals = []
        i = 0
        for p in self.pal_dat.palettes:
            pals.append(gatypes.Palette([gatypes.Color(
                int(c.r*graph_util.MULT), int(c.g*graph_util.MULT), int(c.b*graph_util.MULT)) for c in p.colors], i, p.palette_start_index))
            i += 1
        self.lb_palettes.setPalettes(pals)
        self.lb_palettes.updatePalettesListBox(0)

    def parseSprFile(self, spr_filename: str) -> None:
        self.sprites.clear()
        #self.checkbox_render_all.deselect()
        self.lb_sprites.listbox.configure(state=tk.NORMAL)
        self.lb_sprites.listbox.delete(0, tk.END)
        self.chrfile = goldenaxe_parser.GoldenaxeParser.from_file(spr_filename)
        i = 0
        for ss in self.chrfile.sprites:
            if not ss.size:
                continue
            for s in ss.data.sprite:
                if len(s.sprite_data) < s.width*s.height:
                    print('output too short, extending:',
                          s.width*s.height - len(s.sprite_data))
                    s.sprite_data.extend(
                        [0]*(s.width*s.height - len(s.sprite_data)))
                sprite = gatypes.SpriteDescriptor(
                    i, s.width, s.height, 0, 0, s.sprite_data)
                self.sprites.append(sprite)
                self.lb_sprites.listbox.insert(tk.END, '%06x (%d, %d)' % (
                    sprite.id, sprite.width, sprite.height))
                i += 1
        self.onRenderAllChange()

    def parseChrFile(self, chr_filename: str) -> None:
        self.sprites.clear()
        #self.checkbox_render_all.deselect()
        self.lb_sprites.listbox.configure(state=tk.NORMAL)
        self.lb_sprites.listbox.delete(0, tk.END)
        self.chrfile = lzwfile.Lzwfile.from_file(chr_filename)
        i = 0
        cur_pos = 0
        while cur_pos < len(self.chrfile.raw) - 64:
            sprite = gatypes.SpriteDescriptor(i, 8, 8, 0, 0, bytearray(
                [p if p else p for p in self.chrfile.raw[cur_pos:cur_pos+64]]))
            self.sprites.append(sprite)
            self.lb_sprites.listbox.insert(tk.END, '%06x (%d, %d)' % (
                sprite.id, sprite.width, sprite.height))
            i += 1
            cur_pos += 64
        self.onRenderAllChange()

    '''
{0, 9, 10, 17, 18}
{0, 1, 9, 10, 17, 18}
{0, 9, 10, 11, 12, 16, 17, 18, 19, 20}
{0, 9, 10, 11, 12, 13, 17, 18, 19, 20, 21}
{0, 9, 10, 17, 18}
{0, 9, 17}
{0, 9, 10, 11, 17, 18, 19}
{0, 9, 17}
    '''

    def renderMap(self) -> None:
        if not self.tiles:
            return
        min_color = getPaletteFromSprites(self.tiles)
        print('palette:', hex(min_color))
        self.lb_palettes.updatePalettesListBox(min_color)
        selected_palette = self.lb_palettes.getSelectedPalette()
        self.paletet_frame.updatePaletteFrame(selected_palette)

        map_img = Image.new(
            "RGB", (self.map_width*8, self.map_height*8), color=(255, 255, 255))

        self.canvas.update()
        current_y = 0
        tile_types = set()
        for y in range(0, self.map_height):
            current_x = 0
            for x in range(0, self.map_width):
                tile = self.map_data[y*self.map_width + x]
                tile_index = (tile & 0x07FF) >> 1
                if tile_index >= len(self.tiles):
                    print('unknown tile:', hex(tile_index), x, y)
                    tile_index = 0
                colored_tile = graph_util.ApplyPalette(
                    self.tiles[tile_index].data, selected_palette)
                img = Image.frombuffer(
                    'RGB', (self.tiles[tile_index].width, self.tiles[tile_index].height), colored_tile, 'raw', 'RGB', 0, 1)
                #draw = ImageDraw.Draw(img)
                #draw.text((0,0), str(tile>>11), ((tile>>11)*8, 0, 255))
                #img.putpixel((0,0), ((tile>>11)*8, 0, 0))
                tile_types.add(tile >> 11)
                map_img.paste(img, box=(current_x, current_y))
                current_x += 8
            current_y += 8

        print(tile_types)
        scale = self.scale_slider.get()
        self.map_img = map_img.resize(
            (round(self.map_width * 8 * scale), round(self.map_height * 8 * scale)))
        self.photos = [ImageTk.PhotoImage(self.map_img), ]
        self.canvas.create_image(x, y, image=self.photos[-1], anchor=tk.NW)
        # map_img.close()

    def parseMapFile(self, map_filename: str) -> None:
        self.sprites.clear()
        self.tiles = []
        #self.checkbox_render_all.deselect()
        self.lb_sprites.listbox.configure(state=tk.NORMAL)
        self.lb_sprites.listbox.delete(0, tk.END)
        self.mapfile = lzwfile.Lzwfile.from_file(map_filename)
        self.chrfile = lzwfile.Lzwfile.from_file(map_filename[:-4] + '.CHR')
        i = 0
        cur_pos = 0
        while cur_pos < len(self.chrfile.raw) - 64:
            tile = gatypes.SpriteDescriptor(i, 8, 8, 0, 0, bytearray(
                [p if p else p for p in self.chrfile.raw[cur_pos:cur_pos+64]]))
            self.tiles.append(tile)
            i += 1
            cur_pos += 64
        self.map_width: int = gatypes.STRUCT_USHORT_unpack(self.mapfile.raw[0:2])[
            0]
        self.map_height: int = gatypes.STRUCT_USHORT_unpack(self.mapfile.raw[2:4])[
            0]
        self.map_data: List[int] = [gatypes.STRUCT_USHORT_unpack(
            self.mapfile.raw[4 + i*2: 4 + i*2 + 2])[0] for i in range(0, self.map_height*self.map_width)]
        self.renderMap()

    def loadGameDirectory(self, directory: str):
        (_, _, filenames) = next(os.walk(directory))
        self.lb_files.listbox.delete(0, tk.END)
        for fn in filenames:
            if not isSupportedExt(fn):
                continue
            self.lb_files.listbox.insert(tk.END, fn)

    def loadPalDat(self, event):
        dirname = filedialog.askdirectory(mustexist=True)
        if dirname:
            self.handleGameDirectoryChange(dirname)

    def loadGameFile(self, filename: str) -> None:
        extension = pathlib.Path(filename).suffix.lower()
        if extension == '.spr':
            self.input_type = InputType.SPR_FILE
            self.parseSprFile(filename)
        elif extension == '.chr':
            self.input_type = InputType.CHR_FILE
            self.parseChrFile(filename)
        elif extension == '.map':
            self.input_type = InputType.MAP_FILE
            self.parseMapFile(filename)

    def getScaledSpriteSize(
            self, sprite: gatypes.SpriteDescriptor) -> gatypes.ImageSize:
        scale = self.scale_slider.get()
        return gatypes.ImageSize(round(sprite.width * scale),
                                 round(sprite.height * scale))

    def drawBytesOnCanvas(self, img_buffer: bytearray, width: int, height: int,
                          x: int, y: int,
                          palette: gatypes.Palette) -> gatypes.ImageSize:
        colored_sprite = graph_util.ApplyPalette(img_buffer, palette)
        scale = self.scale_slider.get()
        img = Image.frombuffer('RGB', (width, height), colored_sprite, 'raw',
                               'RGB', 0, 1).resize((round(width * scale),
                                                    round(height * scale)))
        if x == 0 and y == 0:
            self.photos = []
        self.photos.append(ImageTk.PhotoImage(img))
        self.canvas.create_image(x, y, image=self.photos[-1], anchor=tk.NW)
        r = gatypes.ImageSize(*img.size)
        img.close()
        return r

    def drawSpriteOnCanvas(self, sprite: gatypes.SpriteDescriptor, x: int,
                           y: int,
                           palette: gatypes.Palette) -> gatypes.ImageSize:
        return self.drawBytesOnCanvas(sprite.data, sprite.width, sprite.height,
                                      x, y, palette)

    def renderSpriteList(self,
                         sprites: List[gatypes.SpriteDescriptor]) -> None:
        if self.input_type == InputType.MAP_FILE:
            self.renderMap()
            return
        if not sprites:
            return
        min_color = getPaletteFromSprites(sprites)
        print('palette:', hex(min_color))
        #self.updatePaletteFrame()
        self.lb_palettes.updatePalettesListBox(min_color)
        self.canvas.update()
        canvas_width = self.canvas.winfo_width()
        max_height = 0
        current_x = 0
        current_y = 0
        for sprite in sprites:
            #print('min color:', sprite.minColor())
            scaled_size = self.getScaledSpriteSize(sprite)
            if current_x + scaled_size.width > canvas_width:
                current_x = 0
                current_y += max_height
            actual_size = self.drawSpriteOnCanvas(sprite, current_x, current_y,
                                                  self.lb_palettes.getSelectedPalette())
            current_x += actual_size.width
            if actual_size.height > max_height:
                max_height = actual_size.height

    def renderAllSprites(self) -> None:
        self.renderSpriteList(self.sprites)

    def getSelectedFile(self) -> str:
        return self.lb_files.listbox.get(self.lb_files.listbox.curselection())

    def getSelectedSprites(self) -> List[gatypes.SpriteDescriptor]:
        if self.render_all.get():
            return self.sprites
        else:
            selected_sprites = self.lb_sprites.listbox.curselection()
            return [self.sprites[i] for i in selected_sprites]

    def animate(self, sprites: List[gatypes.SpriteDescriptor]) -> None:
        self.animation_thread_running = True
        clipping_box = graph_util.CalculateClippingBox(sprites)

        sprite_index = 0
        while self.animation_enabled.get():
            if sprites:
                s = sprites[sprite_index]
                buf = graph_util.AddClippingBox(s, clipping_box, 0xFF)
                self.drawBytesOnCanvas(buf, clipping_box.width,
                                       clipping_box.height, 0, 0,
                                       self.lb_palettes.getSelectedPalette())
                sprite_index += 1
                sprite_index %= len(sprites)
            time.sleep(1.0 / self.speed_var.get())
        self.animation_thread_running = False

    def animateSprites(self) -> None:
        selected_sprites = self.getSelectedSprites()
        if not selected_sprites:
            return
        self.current_sprite_animation_index = 0
        self.animation_thread = Thread(
            target=lambda: self.animate(selected_sprites))
        self.animation_thread.start()

    def onFileSelect(self, event) -> None:
        filename = os.path.join(self.game_directory, self.getSelectedFile())
        self.loadGameFile(filename)

    def onPaletteSelect(self, event) -> None:
        self.paletet_frame.updatePaletteFrame(self.lb_palettes.getSelectedPalette())
        if not self.animation_enabled.get():
            self.renderSpriteList(self.getSelectedSprites())

    def onSpriteSelect(self, event) -> None:
        sprites = self.getSelectedSprites()
        self.renderSpriteList(sprites)

    def onScaleChange(self) -> None:
        if not self.animation_enabled.get():
            self.renderSpriteList(self.getSelectedSprites())

    def onRenderAllChange(self) -> None:
        if self.render_all.get():
            self.lb_sprites.listbox.configure(state=tk.DISABLED)
            self.renderAllSprites()
        else:
            self.lb_sprites.listbox.configure(state=tk.NORMAL)
            self.onSpriteSelect(None)

    def onMultiSelectChange(self) -> None:
        if self.multiple_selection_enabled.get():
            self.lb_sprites.listbox.configure(selectmode=tk.MULTIPLE)
        else:
            self.lb_sprites.listbox.configure(selectmode=tk.BROWSE)
            cur_sel = self.lb_sprites.listbox.curselection()
            if cur_sel:
                self.lb_sprites.listbox.selection_clear(
                    cur_sel[0], cur_sel[-1])
                self.lb_sprites.listbox.selection_set(cur_sel[0])

    def onAnimationChange(self) -> None:
        if self.animation_enabled.get():
            self.animateSprites()
        else:
            self.renderSpriteList(self.getSelectedSprites())

    def saveStatic(self, filename: str) -> None:
        if self.input_type == InputType.MAP_FILE:
            img = self.map_img
        else:
            sprites = self.getSelectedSprites()
            palette = self.lb_palettes.getSelectedPalette()
            img = graph_util.GetSpritesImage(sprites, palette)
        try:
            img.save(filename)
        except ValueError as e:
            messagebox.showerror('Error', str(e))

    def onSave(self) -> None:
        filename = filedialog.asksaveasfilename(
            filetypes=(('PNG files.', '*.png'), ('GIF files.', '*.gif')),
            initialdir=self.game_directory)
        if self.animation_enabled.get():
            result, error = graph_util.SaveAnimatedImage(filename, self.getSelectedSprites(
            ), self.lb_palettes.getSelectedPalette(), self.speed_var.get())
            if not result:
                messagebox.showerror('Error', error)
        else:
            self.saveStatic(filename)

    def createWidgets(self) -> None:
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)

        self.label_mk_exe = tk.Label(self, text='Game directory:')
        self.label_mk_exe.grid(column=0, row=0, sticky='NW')

        self.string_game_dir = tk.StringVar()
        self.text_pal_dat = tk.Entry(self, textvariable=self.string_game_dir)
        self.text_pal_dat.grid(column=0, row=1, columnspan=2, sticky='NEW')
        self.text_pal_dat.bind("<Button-1>", lambda e: self.loadPalDat(e))

        self.pal_sprites_frame = tk.Frame(self)
        self.pal_sprites_frame.grid(column=0, row=2, rowspan=3, sticky='NESW')
        self.pal_sprites_frame.rowconfigure(1, weight=1)
        self.pal_sprites_frame.columnconfigure(0, weight=1)
        self.pal_sprites_frame.columnconfigure(2, weight=1)
        self.pal_sprites_frame.columnconfigure(4, weight=1)

        self.lb_files = CustomListbox(
            'Files:', self.pal_sprites_frame, lambda e: self.onFileSelect(e), 0)
        self.lb_palettes = PaletteListbox(
            'Palettes:', self.pal_sprites_frame, lambda e: self.onPaletteSelect(e), 1)
        self.lb_sprites = CustomListbox(
            'Sprites:', self.pal_sprites_frame, lambda e: self.onSpriteSelect(e), 2)

        self.canvas = tk.Canvas(self, bg='#FFFFFF')
        self.canvas.grid(column=1, row=2, columnspan=3, sticky='NESW')
        self.canvas_image = Image.new("RGB", (0, 0), color=(255, 255, 255))

        self.paletet_frame = PaletteFrame(self, 1, 3)

        self.control_frame = tk.Frame(self)
        self.control_frame.grid(column=1, row=4, columnspan=2, sticky='NESW')
        self.control_frame.columnconfigure(2, weight=1)
        self.scale_slider = tk.Scale(self.control_frame,
                                     label='Scale:',
                                     from_=1,
                                     to=10,
                                     orient=tk.HORIZONTAL,
                                     resolution=0.1,
                                     command=lambda e: self.onScaleChange())
        self.scale_slider.grid(column=1, row=0, sticky='WE')

        self.render_all = tk.IntVar()
        self.checkbox_render_all = tk.Checkbutton(
            self.control_frame,
            variable=self.render_all,
            text='Render all sprites in one view',
            command=lambda: self.onRenderAllChange())
        self.checkbox_render_all.grid(column=0, row=0, sticky='W')

        self.multiple_selection_enabled = tk.IntVar()
        self.checkbox_multi_select = tk.Checkbutton(
            self.control_frame,
            variable=self.multiple_selection_enabled,
            text='Multiple sprite selection mode',
            command=lambda: self.onMultiSelectChange())
        self.checkbox_multi_select.grid(column=0, row=1, sticky='W')

        self.animation_enabled = tk.IntVar()
        self.checkbox_animation = tk.Checkbutton(
            self.control_frame,
            variable=self.animation_enabled,
            text='Enable animation',
            command=lambda: self.onAnimationChange())
        self.checkbox_animation.grid(column=0, row=2, sticky='W')
        self.speed_var = tk.DoubleVar(value=12.0)
        self.speed_slider = tk.Scale(self.control_frame,
                                     label='Animation speed:',
                                     from_=1,
                                     to=50,
                                     orient=tk.HORIZONTAL,
                                     variable=self.speed_var)
        self.speed_slider.grid(column=1, row=2, sticky='W')

        self.button_save = tk.Button(self.control_frame,
                                     text='Save',
                                     padx=25,
                                     command=lambda: self.onSave())
        self.button_save.grid(column=2, row=0, rowspan=3, sticky='NES')


app = Application()
app.master.title('Golden Axe viewer')
app.mainloop()
