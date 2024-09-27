# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import board
import digitalio
import ulab.numpy as np
import adafruit_debouncer
import adafruit_character_lcd.character_lcd as character_lcd

import synthmenu.character_lcd

lcd_rs = digitalio.DigitalInOut(board.GP0)
lcd_en = digitalio.DigitalInOut(board.GP1)
lcd_d7 = digitalio.DigitalInOut(board.GP2)
lcd_d6 = digitalio.DigitalInOut(board.GP3)
lcd_d5 = digitalio.DigitalInOut(board.GP4)
lcd_d4 = digitalio.DigitalInOut(board.GP5)
lcd_backlight = digitalio.DigitalInOut(board.GP6)

COLUMNS = 16
ROWS = 2

lcd = character_lcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, COLUMNS, ROWS, lcd_backlight)

def item_title(item:synthmenu.Item) -> str:
    return type(item).__name__

menu = synthmenu.character_lcd.Menu(lcd, COLUMNS, ROWS, "CharLCD Menu", (
    synthmenu.Action(item_title, lambda: print("Hello World")),
    synthmenu.Group("Simple Items", (
        synthmenu.Action("Return", lambda: menu.exit()),
        synthmenu.Number(item_title),
        synthmenu.Bool(item_title),
        synthmenu.Time(item_title),
        synthmenu.List(item_title, ("ASDF", "QWER", "UIOP")),
        synthmenu.Char(item_title),
    )),
    synthmenu.Group("Complex Items", (
        synthmenu.Action("Return", lambda: menu.exit()),
        synthmenu.String(item_title, length=COLUMNS),
        synthmenu.Waveform(item_title, (
            ("Sine", lambda: np.array(np.sin(np.linspace(0, 2*np.pi, COLUMNS, endpoint=False)) * 32767, dtype=np.int16)),
            ("Saw", lambda: np.linspace(32767, -32767, num=COLUMNS, dtype=np.int16)),
            ("Triangle", lambda: np.concatenate((
                np.linspace(-32767, 32767, num=COLUMNS//2, dtype=np.int16),
                np.linspace(32767, -32767, num=COLUMNS//2, dtype=np.int16)
            ))),
            ("Square", lambda: np.concatenate((np.full(COLUMNS//2, 32767, dtype=np.int16), np.full(COLUMNS//2, -32767, dtype=np.int16)))),
        )),
        synthmenu.AREnvelope(item_title),
        synthmenu.ADSREnvelope(item_title),
        synthmenu.LFO(item_title),
        synthmenu.Filter(item_title),
        synthmenu.Mix(item_title),
        synthmenu.Tune(item_title),
        synthmenu.Patch(item_title),
    )),
))

button_pins = (
    digitalio.DigitalInOut(board.GP2),
    digitalio.DigitalInOut(board.GP3),
    digitalio.DigitalInOut(board.GP4),
    digitalio.DigitalInOut(board.GP5),
)
buttons = []
for pin in button_pins:
    pin.direction = digitalio.Direction.INPUT
    buttons.append(adafruit_debouncer.Debouncer(pin))
buttons = tuple(buttons)

while True:
    for button in buttons:
        button.update()
    
    if buttons[0].fell:
        if isinstance(menu.selected, synthmenu.Group):
            menu.previous()
        else:
            menu.decrement()
    if buttons[1].fell:
        if isinstance(menu.selected, synthmenu.Group):
            menu.next()
        else:
            menu.increment()
    if buttons[2].fell:
        if not menu.select():
            menu.exit()
    if buttons[3].fell:
        menu.exit()
