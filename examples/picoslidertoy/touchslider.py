## pylint: disable=invalid-name
# SPDX-FileCopyrightText: Copyright (c) 2024 Tod Kurt
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
# SPDX-License-Identifier: MIT
"""
`touchslider`
================================================================================

Create linear (TouchSlider) and rotary (TouchWheel) capacative touch sliders
 using three `touchio` pins and special pad geometry.

Originally part of the 'touchwheels' project: https://github.com/todbot/touchwheels/
2023 - @todbot / Tod Kurt

2024 - @dcooperdalrymple / Cooper Dalrymple
- Added TouchWheelRotary class
- Changed pos method to read-only property
- Made TouchWheel properties private

"""

import time

import touchio

try:
    from typing import Callable

    from microcontroller import Pin
except ImportError:
    pass


class TouchWheel:
    """Simple capacitive touchweel made from three captouch pads"""

    def __init__(
        self,
        pins: tuple[Pin],
        offset: float | None = None,
        sector_scale: float | None = None,
        wrap_value: bool = True,
    ):
        if len(pins) < 3:
            raise ValueError("Touch wheel must have at least 3 touch pads to function")

        self._scale = sector_scale if sector_scale is not None else 1 / len(pins)
        # physical design is rotated 1/2 a sector anti-clockwise
        self._offset = offset if offset is not None else -self._scale / 2
        self._wrap_value = wrap_value
        self._touchins = []
        for pin in pins:
            self._touchins.append(touchio.TouchIn(pin))

    @property
    def pos(self) -> float | None:
        """
        Given three touchio.TouchIn pads, compute wheel position 0-1
        or return None if wheel is not pressed
        """
        a = self._touchins[0]
        b = self._touchins[1]
        c = self._touchins[2]

        # compute raw percentages
        a_pct = (a.raw_value - a.threshold) / a.threshold
        b_pct = (b.raw_value - b.threshold) / b.threshold
        c_pct = (c.raw_value - c.threshold) / c.threshold

        pos = None

        # cases when finger is touching two pads
        if a_pct >= 0 and b_pct >= 0:  #
            pos = self._scale * (0 + (b_pct / (a_pct + b_pct)))
        elif b_pct >= 0 and c_pct >= 0:  #
            pos = self._scale * (1 + (c_pct / (b_pct + c_pct)))
        elif c_pct >= 0 and a_pct >= 0 and self._wrap_value:  #
            pos = self._scale * (2 + (a_pct / (c_pct + a_pct)))

        # special cases when finger is just on a single pad.
        elif a_pct > 0 and b_pct <= 0 and c_pct <= 0:
            pos = 0 * self._scale
        elif a_pct <= 0 and b_pct > 0 and c_pct <= 0:
            pos = 1 * self._scale
        elif a_pct <= 0 and b_pct <= 0 and c_pct > 0 and self._wrap_value:
            pos = 2 * self._scale

        # wrap pos around the 0-1 circle if offset puts it outside that range
        return (pos + self._offset) % 1 if pos is not None else None


class TouchSlider(TouchWheel):
    """A TouchSlider is a linearized TouchWheel"""

    def __init__(self, touch_pins, offset=0, sector_scale=0.5, wrap_value=False):
        super().__init__(touch_pins, offset, sector_scale, wrap_value)


class TouchWheelRotary(TouchWheel):
    """A TouchWheelRotary is a standard TouchWheel but with an incremental value and button inputs.
    """

    on_left_press: Callable[[], None] = None
    on_right_press: Callable[[], None] = None
    on_up_press: Callable[[], None] = None
    on_down_press: Callable[[], None] = None

    on_left_long_press: Callable[[], None] = None
    on_right_long_press: Callable[[], None] = None
    on_up_long_press: Callable[[], None] = None
    on_down_long_press: Callable[[], None] = None

    on_increment: Callable[[], None] = None
    on_decrement: Callable[[], None] = None
    on_step_release: Callable[[int], None] = None

    def __init__(
        self,
        touch_pins,
        step_size=0.2,
        short_press_duration=0.05,
        long_press_duration=0.2,
        offset=-0.333 / 2,
        sector_scale=0.333,
    ):
        super().__init__(touch_pins, offset, sector_scale)
        self._step_size = min(max(step_size, 0.01), 0.25)
        self._short_press_duration = max(short_press_duration, 0.01)
        self._long_press_duration = max(long_press_duration, self._short_press_duration + 0.01)
        self._value = None
        self._time = None
        self._stepped = False
        self._steps = 0

    def update(self) -> None:
        value = self.pos

        # No touch
        if value is None and self._value is None:
            return

        current_time = time.monotonic()

        # Start of touch
        if self._value is None:
            self._value = value
            self._time = current_time
            self._stepped = False
            self._steps = 0
            return

        # End of touch
        if value is None:
            # Do final action if press or stepped
            if not self._stepped and current_time - self._time > self._short_press_duration:
                long_press = current_time - self._time > self._long_press_duration
                # left = 0.25, up = 1.0/0.0, right = 0.75, down = 0.5
                if abs(self._value - 0.25) < 0.125:
                    if long_press and callable(self.on_left_long_press):
                        self.on_left_long_press()
                    elif not long_press and callable(self.on_left_press):
                        self.on_left_press()
                elif abs(self._value - 0.5) < 0.125:
                    if long_press and callable(self.on_down_long_press):
                        self.on_down_long_press()
                    elif not long_press and callable(self.on_down_press):
                        self.on_down_press()
                elif abs(self._value - 0.75) < 0.125:
                    if long_press and callable(self.on_right_long_press):
                        self.on_right_long_press()
                    elif not long_press and not long_press and callable(self.on_right_press):
                        self.on_right_press()
                elif long_press and callable(self.on_up_long_press):
                    self.on_up_long_press()
                elif not long_press and callable(self.on_up_press):
                    self.on_up_press()
            elif self._stepped:
                if callable(self.on_step_release):
                    self.on_step_release(self._steps)
            self._value = None
            return

        # Fix wrapping
        unwrapped_value = value
        if abs(value - self._value) > 0.5:
            if value > self._value and self._value < 0.5:
                unwrapped_value -= 1.0
            elif value < self._value and self._value > 0.5:
                unwrapped_value += 1.0

        # Handle steps
        if abs(unwrapped_value - self._value) > self._step_size:
            if unwrapped_value > self._value:
                # Decrement
                while unwrapped_value - self._value > self._step_size:
                    self._stepped = True
                    self._steps -= 1
                    self._value += self._step_size
                    if callable(self.on_decrement):
                        self.on_decrement()
            elif unwrapped_value < self._value:
                # Increment
                while self._value - unwrapped_value > self._step_size:
                    self._stepped = True
                    self._steps += 1
                    self._value -= self._step_size
                    if callable(self.on_increment):
                        self.on_increment()
            self._value = self._value % 1
