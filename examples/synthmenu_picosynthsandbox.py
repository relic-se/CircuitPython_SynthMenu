# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense
"""
Example for `pico_synth_sandbox Rev2 <https://github.com/dcooperdalrymple/pico_synth_sandbox-hardware/releases/tag/Rev2>`_ by @dcooperdalrymple.
"""

import board
import digitalio
import rotaryio
import ulab.numpy as np
import adafruit_debouncer
import adafruit_character_lcd.character_lcd as character_lcd

import synthmenu.character_lcd

lcd_rs = digitalio.DigitalInOut(board.GP7)
lcd_en = digitalio.DigitalInOut(board.GP6)
lcd_d4 = digitalio.DigitalInOut(board.GP22)
lcd_d5 = digitalio.DigitalInOut(board.GP26)
lcd_d6 = digitalio.DigitalInOut(board.GP27)
lcd_d7 = digitalio.DigitalInOut(board.GP28)

COLUMNS = 16
ROWS = 2

lcd = character_lcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, COLUMNS, ROWS)

def item_title(item:synthmenu.Item) -> str:
    return type(item).__name__

menu = synthmenu.character_lcd.Menu(lcd, COLUMNS, ROWS, "Menu", (
    synthmenu.Action(item_title, lambda: print("Hello World")),
    synthmenu.Group("Simple", (
        synthmenu.Number(item_title),
        synthmenu.Bool(item_title),
        synthmenu.Time(item_title),
        synthmenu.List(item_title, ("ASDF", "QWER", "UIOP")),
        synthmenu.Char(item_title),
    )),
    synthmenu.Group("Complex", (
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
    digitalio.DigitalInOut(board.GP13),
    digitalio.DigitalInOut(board.GP18),
)
buttons = []
for pin in button_pins:
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    buttons.append(adafruit_debouncer.Debouncer(pin))
buttons = tuple(buttons)

encoders = (
    rotaryio.IncrementalEncoder(board.GP12, board.GP11),
    rotaryio.IncrementalEncoder(board.GP17, board.GP16)
)
encoder_position = []
for encoder in encoders:
    encoder_position.append(encoder.position)

while True:
    for i, encoder in enumerate(encoders):
        position = encoder.position
        buttons[i].update()

        if position > encoder_position[i]:
            for j in range(position - encoder_position[i]):
                menu.next() if not i else menu.increment()
        elif position < encoder_position[i]:
            for j in range(encoder_position[i] - position):
                menu.previous() if not i else menu.decrement()
        if buttons[i].rose:
            if not i:
                menu.exit()
            elif isinstance(menu.selected.current_item, synthmenu.Group):
                menu.select()
        
        encoder_position[i] = position
