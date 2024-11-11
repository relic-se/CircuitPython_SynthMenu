# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import adafruit_debouncer
import adafruit_displayio_ssd1306
import board
import busio
import digitalio
import displayio
import ulab.numpy as np

import synthmenu
import synthmenu.displayio

WIDTH = 128
HEIGHT = 64

displayio.release_displays()

i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)


def item_title(item: synthmenu.Item) -> str:
    return type(item).__name__


menu = synthmenu.displayio.Menu(
    WIDTH,
    HEIGHT,
    "displayio Menu",
    (
        synthmenu.Action(item_title, lambda: print("Hello World")),
        synthmenu.Group(
            "Simple Items",
            (
                synthmenu.Action("Return", lambda: menu.exit()),
                synthmenu.Number(item_title),
                synthmenu.Bool(item_title),
                synthmenu.Time(item_title),
                synthmenu.List(item_title, ("ASDF", "QWER", "UIOP")),
                synthmenu.Char(item_title),
            ),
        ),
        synthmenu.Group(
            "Complex Items",
            (
                synthmenu.Action("Return", lambda: menu.exit()),
                synthmenu.String(item_title, length=8),
                synthmenu.Waveform(
                    item_title,
                    (
                        (
                            "Sine",
                            lambda: np.array(
                                np.sin(np.linspace(0, 2 * np.pi, WIDTH, endpoint=False)) * 32767,
                                dtype=np.int16,
                            ),
                        ),
                        ("Saw", lambda: np.linspace(32767, -32767, num=WIDTH, dtype=np.int16)),
                        (
                            "Triangle",
                            lambda: np.concatenate(
                                (
                                    np.linspace(-32767, 32767, num=WIDTH // 2, dtype=np.int16),
                                    np.linspace(32767, -32767, num=WIDTH // 2, dtype=np.int16),
                                )
                            ),
                        ),
                        (
                            "Square",
                            lambda: np.concatenate(
                                (
                                    np.full(WIDTH // 2, 32767, dtype=np.int16),
                                    np.full(WIDTH // 2, -32767, dtype=np.int16),
                                )
                            ),
                        ),
                    ),
                ),
                synthmenu.AREnvelope(item_title),
                synthmenu.ADSREnvelope(item_title),
                synthmenu.LFO(item_title),
                synthmenu.Filter(item_title),
                synthmenu.Mix(item_title),
                synthmenu.Tune(item_title),
                synthmenu.Patch(item_title),
            ),
        ),
    ),
)

display.root_group = menu.group

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
