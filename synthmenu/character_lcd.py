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
        
        super().__init__(title, items, loop)

    def draw(self, group:synthmenu.Group) -> None:
        group_len = self._columns // 4 - 1
        item_len = self._columns - group_len - 1
        
        self._lcd.cursor_position(0, 0)
        self._lcd.message = "{{:<{:d}}}:{{:<{:d}}}{{:<{:d}}}".format(group_len, item_len, self._columns).format(group.title[:group_len], group.current_item.title[:item_len], group.current_item.label[self._columns])
