# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: MIT

import displayio
from micropython import const
import terminalio
import ulab.numpy as np
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
INDICATOR_STROKE = const(2)
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
            width=CHAR_WIDTH - 1,
            height=INDICATOR_STROKE,
            y=LINE_SIZE + (self._height - LINE_SIZE) // 2 + CHAR_HEIGHT // 2 + INDICATOR_MARGIN,
        )
        self._indicator_item.hidden = True
        self._buffer.append(self._indicator_item)

        self._chart_group = displayio.Group(y=LINE_SIZE + 1)

        chart_color = displayio.Palette(1)
        chart_color[0] = 0xFFFFFF
        self._chart_group.append(vectorio.Polygon(
            pixel_shader=chart_color,
            points=[(0, 0) for i in range(3)], # Empty shape
        ))

        for i in range(2):
            self._chart_group.append(vectorio.Rectangle(
                pixel_shader=scrollbar_color,
                width=INDICATOR_STROKE,
                height=self._chart_height - INDICATOR_MARGIN * 2,
                x=-1,
                y=INDICATOR_MARGIN,
            ))
            self._chart_group[-1].hidden = True

        self._chart_group.hidden = True
        self._buffer.append(self._chart_group)
        
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
    
    def draw(self) -> None:
        item = self.selected

        is_string = isinstance(item, synthmenu.String)
        is_waveform = isinstance(item, synthmenu.WaveformList) or isinstance(item, synthmenu.Waveform)
        is_waveform_group = isinstance(item, synthmenu.Waveform)
        is_envelope = isinstance(item, synthmenu.AREnvelope) or isinstance(item, synthmenu.ADSREnvelope)
        is_value_group = is_string or is_waveform_group or is_envelope
        is_value = not isinstance(item, synthmenu.Group) or is_string or is_waveform_group or is_envelope

        self._draw_items.hidden = is_value
        self._value_item.hidden = not is_value or is_waveform or is_envelope
        self._scrollbar_item.hidden = is_value
        self._indicator_item.hidden = not is_string
        self._chart_group.hidden = not is_waveform and not is_envelope
        self._chart_group[1].hidden = not is_waveform_group and not is_envelope
        self._chart_group[2].hidden = not is_waveform_group

        if is_value_group:
            self._title_item[1].text = "{:s}: {:s}".format(item.title, item.current_item.title)
        elif is_waveform:
            self._title_item[1].text = "{:s}: {:s}".format(item.title, item.label)
        else:
            self._title_item[1].text = item.title

        if not is_value:
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

        elif is_waveform:
            self._draw_waveform(item.waveform.data if is_waveform_group else item.data)
            if is_waveform_group:
                self._chart_group[1].x = min(max(int(item.loop_start.value * self._width), 0), self._width - INDICATOR_STROKE)
                self._chart_group[2].x = min(max(int(item.loop_end.value * self._width), 0), self._width - INDICATOR_STROKE)

        elif is_envelope:
            if isinstance(item, synthmenu.AREnvelope):
                values = (
                    (item.attack_time.relative_value, item.sustain_level.value),
                    (item.release_time.relative_value, item.sustain_level.value),
                )
                if item.index == 0: # attack_time
                    pos = item.attack_time.relative_value / 6
                elif item.index == 1: # sustain_level
                    pos = (1 - (item.attack_time.relative_value + item.release_time.relative_value) / 3) / 2 + item.attack_time.relative_value / 3
                else: # release_time
                    pos = 1 - item.release_time.relative_value / 6
            else:
                values = (
                    (item.attack_time.relative_value, item.attack_level.value),
                    (item.decay_time.relative_value, item.sustain_level.value),
                    (item.release_time.relative_value, item.sustain_level.value),
                )
                if item.index == 0: # attack_time
                    pos = item.attack_time.relative_value / 8
                elif item.index == 1: # attack_level
                    pos = item.attack_time.relative_value / 4
                elif item.index == 2: # decay_time
                    pos = item.attack_time.relative_value / 4 + item.decay_time.relative_value / 8
                elif item.index == 3: # sustain_level
                    pos = (1 - (item.attack_time.relative_value + item.decay_time.relative_value + item.release_time.relative_value) / 4) / 2 + (item.attack_time.relative_value + item.decay_time.relative_value) / 4
                else: # release_time
                    pos = 1 - item.release_time.relative_value / 8
            self._draw_envelope(values)
            self._chart_group[1].x = round(pos * (self._width - INDICATOR_STROKE))

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

    @property
    def _chart_height(self) -> int:
        return self._height - LINE_SIZE - 1

    def _draw_waveform(self, data:np.ndarray, resolution:float = 0.25) -> None:
        if data.dtype != np.int16:
            raise ValueError("Chart data must be of data type np.int16")
        size = min(max(resolution * self._width, 1), self._width)
        if len(data) != size:
            data = np.interp(
                np.arange(0.0, len(data), len(data) / size, dtype=np.float),
                np.arange(0, len(data), 1, dtype=np.uint16),
                data
            )
        else:
            data = np.array(data, dtype=np.float)
        height = self._chart_height
        x_scale = self._width / size
        data = np.array((data / -32767 + 1) * height / 2, dtype=np.int16)
        points = []
        for i in range(len(data)):
            points.append((int(i * x_scale), min(max(data[i], 0), height - INDICATOR_STROKE)))
        for i in range(len(data) - 1, -1, -1):
            points.append((int(i * x_scale), min(max(data[i] + 1, 1), height)))
        self._chart_group[0].points = points

    def _draw_envelope(self, values:tuple[tuple[float, float]], fill:bool = False) -> None:
        if len(values) < 2:
            raise ValueError("Envelope must have at least 2 positions")
        points = [(0, self._chart_height - INDICATOR_STROKE)]
        for i, value in enumerate(values):
            if i < len(values) - 1:
                points.append((
                    round(points[-1][0] + value[0] / (len(values) + 1) * (self._width - 1)),
                    round((1 - value[1]) * (self._chart_height - INDICATOR_STROKE))
                ))
            else:
                points.append((
                    round((1 - value[0] / (len(values) + 1)) * (self._width - 1)),
                    round((1 - value[1]) * (self._chart_height - INDICATOR_STROKE))
                ))
        points.append((self._width - 1, self._chart_height - INDICATOR_STROKE))
        if fill:
            points.append((self._width - 1, self._chart_height))
            points.append((0, self._chart_height))
        else:
            for i in range(len(points) - 1, -1, -1):
                points.append((points[i][0], points[i][1] + INDICATOR_STROKE))
        self._chart_group[0].points = points
