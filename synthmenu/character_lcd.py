# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: MIT

from adafruit_character_lcd.character_lcd import Character_LCD_Mono

import synthmenu

try:
    from typing import Callable
except ImportError:
    pass

class Menu(synthmenu.Menu):

    def __init__(
        self,
        lcd:Character_LCD_Mono,
        columns:int,
        lines:int,
        title:str|Callable[[], str] = "",
        items:tuple[synthmenu.Item] = None,
        loop:bool = False
    ):
        self._lcd = lcd
        self._columns = columns
        self._lines = lines
        if self._lines < 2:
            raise ValueError("At least 2 lines are required")
        self._lcd.blink = False
        super().__init__(title, items, loop)

    def _has_cursor(self, item: synthmenu.Item) -> bool:
        return isinstance(item, synthmenu.String) or isinstance(item, synthmenu.Sequence)

    def draw(self) -> None:
        self._lcd.cursor_position(0, 0)
        
        item = self.selected

        title = item.title
        if isinstance(item, synthmenu.Group):
            item_len = min(len(item.current_item.title), self._columns - 4)
            title_len = min(max(len(item.title), 3), self._columns - 1 - item_len)
            gap_len = self._columns - title_len - 1 - item_len
            title = "{{:<{:d}}}:{:s}{{:<{:d}}}".format(title_len, " " * gap_len, item_len).format(item.title[:title_len], item.current_item.title[:item_len])

        value = item.label
        if isinstance(item, synthmenu.Group) and not self._has_cursor(item):
            value = "Enter" if isinstance(item.current_item, synthmenu.Group) and not self._has_cursor(item.current_item) else item.current_item.label

        lines = [title, value]
        for i in range(len(lines)):
            lines[i] = "{{:<{:d}}}".format(self._columns).format(lines[i][:self._columns])
        self._lcd.message = "\n".join(lines)

        self._lcd.cursor = self._has_cursor(item)
        if self._has_cursor(item):
            self._lcd.cursor_position(item.index % self._columns, 1)
