# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: MIT

import displayio
from micropython import const
import terminalio
import vectorio
from adafruit_display_text import label

import synthmenu

try:
    from typing import Callable
    from fontio import FontProtocol
except ImportError:
    pass

LINE_SIZE = const(16)
BORDER_WIDTH = const(1)
PADDING = const(2)

SCROLLBAR_WIDTH = const(2)

CHAR_WIDTH = const(6)
CHAR_HEIGHT = const(8)
INDICATOR_WIDTH = const(5)
INDICATOR_HEIGHT = const(2)
INDICATOR_MARGIN = const(2)

class Menu(synthmenu.Menu):

    title_background_color:int = 0xFFFFFF
    title_label_color:int = 0x000000

    item_border_color:int = 0x000000
    item_border_selected_color:int = 0xFFFFFF

    item_background_color:int = 0x000000
    item_background_selected_color:int = 0xFFFFFF

    item_title_color:int = 0xFFFFFF
    item_title_selected_color:int = 0x000000

    item_label_color:int = 0xFFFFFF
    item_label_selected_color:int = 0x000000

    def __init__(
        self,
        width:int = 128,
        height:int = 64,
        title:str|Callable[[], str] = "",
        items:tuple[synthmenu.Item] = None,
        loop:bool = False,
        title_font:FontProtocol = terminalio.FONT,
        text_font:FontProtocol = terminalio.FONT,
    ):
        self._width = width
        self._height = height
        if self.lines < 2:
            raise ValueError("At least 2 lines are required")
        
        self._buffer = displayio.Group()

        self._title_item = displayio.Group()

        title_background_color = displayio.Palette(1)
        title_background_color[0] = self.title_background_color
        self._title_item.append(vectorio.Rectangle(
            pixel_shader=title_background_color,
            width=self._width,
            height=LINE_SIZE,
        ))

        title_label = label.Label(title_font, text="", color=self.title_label_color)
        title_label.anchor_point = (0.5, 0.5)
        title_label.anchored_position = (self._width // 2, LINE_SIZE//2)
        self._title_item.append(title_label)

        self._buffer.append(self._title_item)

        self._draw_items = displayio.Group(y=LINE_SIZE)
        for i in range(self.lines):
            item = displayio.Group(x=0, y=LINE_SIZE*i)

            border_color = displayio.Palette(1)
            border_color[0] = self.item_border_color
            item.append(vectorio.Rectangle(
                pixel_shader=border_color,
                width=self._width - SCROLLBAR_WIDTH,
                height=LINE_SIZE,
            ))

            background_color = displayio.Palette(1)
            background_color[0] = self.item_background_color
            item.append(vectorio.Rectangle(
                pixel_shader=background_color,
                width=self._width - BORDER_WIDTH * 2 - SCROLLBAR_WIDTH,
                height=LINE_SIZE - BORDER_WIDTH * 2,
                x=BORDER_WIDTH,
                y=BORDER_WIDTH,
            ))

            title_text = label.Label(text_font, text="", color=self.item_title_color)
            title_text.anchor_point = (0, 0.5)
            title_text.anchored_position = (BORDER_WIDTH+PADDING, LINE_SIZE//2)
            item.append(title_text)

            label_text = label.Label(text_font, text="", color=self.item_label_color)
            label_text.anchor_point = (1.0, 0.5)
            label_text.anchored_position = (self._width-BORDER_WIDTH-PADDING-SCROLLBAR_WIDTH, LINE_SIZE//2)
            item.append(label_text)

            item.hidden = True
            self._draw_items.append(item)
        self._buffer.append(self._draw_items)

        self._value_item = displayio.Group(y=LINE_SIZE)
        value_text = label.Label(text_font, text="", color=self.item_label_color)
        value_text.anchor_point = (0.5, 0.5)
        value_text.anchored_position = (self._width//2, (self._height-LINE_SIZE)//2)
        self._value_item.append(value_text)
        self._value_item.hidden = True
        self._buffer.append(self._value_item)

        scrollbar_color = displayio.Palette(1)
        scrollbar_color[0] = 0xFFFFFF
        self._scrollbar_item = vectorio.Rectangle(
            pixel_shader=scrollbar_color,
            width=SCROLLBAR_WIDTH,
            height=1,
            x=self._width-SCROLLBAR_WIDTH,
            y=LINE_SIZE,
        )
        self._buffer.append(self._scrollbar_item)

        self._indicator_item = vectorio.Rectangle(
            pixel_shader=scrollbar_color,
            width=INDICATOR_WIDTH,
            height=INDICATOR_HEIGHT,
            y=LINE_SIZE + (self._height - LINE_SIZE) // 2 + CHAR_HEIGHT // 2 + INDICATOR_MARGIN,
        )
        self._indicator_item.hidden = True
        self._buffer.append(self._indicator_item)
        
        super().__init__(title, items, loop)

        self.draw(self.selected)

    @property
    def scrollbar_color(self) -> int:
        return self._scrollbar_item.pixel_shader[0]
    
    @scrollbar_color.setter
    def scrollbar_color(self, value:int) -> None:
        self._scrollbar_item.pixel_shader[0] = value

    @property
    def lines(self) -> int:
        return self._height // LINE_SIZE - 1
    
    @property
    def group(self) -> displayio.Group:
        return self._buffer
    
    def draw(self, item:synthmenu.Item) -> None:
        self._title_item[1].text = item.title

        is_string = isinstance(item, synthmenu.String)
        show_value = not isinstance(item, synthmenu.Group) or is_string

        self._draw_items.hidden = show_value
        self._value_item.hidden = not show_value
        self._scrollbar_item.hidden = show_value
        self._indicator_item.hidden = not is_string

        if not show_value:
            j = item.index - self.lines // 2
            if not item.loop:
                j = min(max(j, 0), max(item.length - self.lines, 0))
            for i in range(self.lines):
                if item.loop or j < item.length:
                    self._draw_item(i, item.items[j % item.length], j == item.index)
                else:
                    self._clear_item(i)
                j += 1
            
            self._scrollbar_item.height = int((self._height - LINE_SIZE) / item.length)
            self._scrollbar_item.y = int(LINE_SIZE + (self._height - LINE_SIZE - self._scrollbar_item.height) * item.index / max(item.length - 1, 1))

        else:
            self._value_item[0].text = str(item.label)
            if is_string:
                self._indicator_item.x = (self._width - CHAR_WIDTH * item.length) // 2 + CHAR_WIDTH * item.index
        
    def _draw_item(self, index:int, item:synthmenu.Item, selected:bool = False) -> None:
        draw_item = self._draw_items[index % len(self._draw_items)]
        draw_item[0].pixel_shader[0] = self.item_border_selected_color if selected else self.item_border_color
        draw_item[1].pixel_shader[0] = self.item_background_selected_color if selected else self.item_background_color
        draw_item[2].text = str(item.title).strip()
        draw_item[2].color = self.item_title_selected_color if selected else self.item_title_color
        draw_item[3].text = str(item.label).strip()
        draw_item[3].color = self.item_label_selected_color if selected else self.item_label_color

        draw_item.hidden = False

    def _clear_item(self, index:int) -> None:
        self._draw_items[index % len(self._draw_items)].hidden = True
