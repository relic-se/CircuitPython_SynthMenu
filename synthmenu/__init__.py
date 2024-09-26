# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: MIT
"""
`synthmenu`
================================================================================

Menu management and display library


* Author(s): Cooper Dalrymple

Implementation Notes
--------------------

**Hardware:**

* If using :class:`synthmenu.character_lcd.Menu`, any standard 16x2 or 16x4 character LCD that is
  supported by Adafruit_CircuitPython_CharLCD can be used.

* If using :class:`synthmenu.displayio.Menu`, any displayio compatible display can be
  used. However, this library is specifically designed with an 128x64 or 128x128 OLED graphic
  display in mind.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

# imports

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/dcooperdalrymple/CircuitPython_SynthMenu.git"

import math
import json
import os
import ulab.numpy as np

try:
    from typing import Callable
except ImportError:
    pass

_CHARACTERS = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!-_#$%&+@~^,.`*?()=|/\\[]{}<>"

class Item:

    def __init__(self, title:str|Callable[[object], str] = ""):
        self._title = title

    @property
    def title(self) -> str:
        return self._title(self) if callable(self._title) else self._title
    
    @property
    def value(self) -> any:
        return None
    
    @value.setter
    def value(self, value:any) -> None:
        pass
    
    @property
    def label(self) -> str:
        return ""
    
    @property
    def data(self) -> any:
        return self.value
    
    on_update: Callable[[any, object], None] = None

    def _do_update(self):
        if callable(self.on_update): self.on_update(self.value, self)

    def select(self) -> bool|None:
        return True # Indicate that item can be selected

    def navigate(self, value:int) -> bool:
        return False # Indicate to move on to another item
    
    def previous(self) -> bool:
        return self.navigate(-1)
    
    def next(self) -> bool:
        return self.navigate(1)
    
    def increment(self) -> bool:
        return False # Indicate whether to redraw
    
    def decrement(self) -> bool:
        return False # Indicate whether to redraw
    
    def reset(self) -> bool:
        return False # Indicate whether to redraw
    
class Group(Item):

    loop:bool = False

    def __init__(self, title:str|Callable[[Item], str], items:tuple[Item] = None, loop:bool=False):
        super().__init__(title)
        self._items = items
        self._index = 0
        self.loop = loop
    
    @property
    def label(self) -> str:
        return ">"

    @property
    def current_item(self) -> Item:
        return self._items[self._index]
    
    def find(self, title:str) -> Item:
        for i in self._items:
            if i.title == title:
                return i
        return None
    
    @property
    def value(self) -> tuple:
        return tuple([i.value for i in self._items])
    
    @value.setter
    def value(self, value:tuple) -> None:
        for i in range(len(value)):
            if i >= len(self._items):
                break
            self._items[i].value = value[i]
        self._do_update()
    
    @property
    def data(self) -> dict:
        data = {}
        for i in self._items:
            data[i.title] = i.data
        return data
    
    @data.setter
    def data(self, value:dict):
        for title in value:
            item = self.find(title)
            if item:
                item.data = value[title]

    @property
    def index(self) -> int:
        return self._index
    
    @index.setter
    def index(self, value:int) -> None:
        self._index = value % len(self._items)
    
    @property
    def items(self) -> tuple[Item]:
        return self._items

    @property
    def length(self) -> int:
        return len(self._items)
    
    def navigate(self, value:int) -> bool:
        index = self._index + value
        if self.loop and index >= len(self._items):
            index = 0
        elif self.loop and index < 0:
            index = len(self._items) - 1
        else:
            index = min(max(index, 0), len(self._items) - 1)
        if index == self._index:
            return False
        self._index = index
        return True
    
    def increment(self) -> bool:
        if isinstance(self.current_item, Group):
            return False
        return self.current_item.increment()
    
    def decrement(self) -> bool:
        if isinstance(self.current_item, Group):
            return False
        return self.current_item.decrement()
    
    def reset(self, full:bool = False) -> bool:
        if full:
            for item in self._items:
                if issubclass(type(item), Group):
                    item.reset(True)
                else:
                    item.reset()
            return True
        else:
            return self.current_item.reset()

class Menu(Group):

    def __init__(self, title:str|Callable[[Item], str], items:tuple[Item] = None, loop:bool = False):
        super().__init__(title, items, loop)
        self._stack = [self]

    @property
    def selected(self) -> Item:
        return self._stack[-1]

    def write_file(self, path:str) -> bool:
        if not path.endswith(".json"):
            raise ValueError("File path must have a .json extension.")
        
        data = self.data
        if not data:
            return False
        
        try:
            with open(path, "w") as file:
                json.dump(data, file)
            return True
        except:
            return False
        
    def read_file(self, path:str) -> bool:
        if not path.endswith(".json"):
            raise ValueError("File path must have a .json extension.")
        
        try:
            os.stat(path)
        except:
            return False
        
        try:
            with open(path, "r") as file:
                data = json.load(file)
        except:
            return False
        
        if not data or not type(data) is dict:
            return False
        
        self.data = data
        return True
    
    def select(self, index:int = -1) -> bool:
        if not isinstance(self.selected, Group):
            return False
        if index < 0:
            index = self.selected.index
        else:
            index = index % self.selected.length
        result = self.selected.items[index].select()
        if result is False:
            return False
        elif result is not None:
            self._stack.append(self.selected.items[index])
        self.draw(self.selected)
        return True

    def navigate(self, value:int) -> bool:
        result = False
        if self.selected is self:
            result = super().navigate(value)
        elif isinstance(self.selected, Group):
            result = self.selected.navigate(value)
        if result: self.draw(self.selected)
        return result
    
    def exit(self) -> bool:
        if len(self._stack) == 1:
            return False
        self._stack.pop()
        self.draw(self.selected)
        return True
    
    def increment(self) -> bool:
        result = False
        if self.selected is not self:
            result = self.selected.increment()
        if result: self.draw(self.selected)
        return result
    
    def decrement(self) -> bool:
        result = False
        if self.selected is not self:
            result = self.selected.decrement()
        if result: self.draw(self.selected)
        return result
    
    def reset(self, full:bool = False) -> bool:
        result = super().reset(full)
        if result: self.draw(self.selected)
        return result
    
    def draw(self, item:Item) -> None:
        pass
    
class Action(Item):
    def __init__(
        self,
        title:str|Callable[[Item], str],
        callback:Callable[[], None] = None,
    ):
        super().__init__(title)
        self._callback = callback
    
    def select(self) -> bool|None:
        if callable(self._callback):
            self._callback()
        return None

class Number(Item):

    def __init__(
        self,
        title:str|Callable[[Item], str],
        step:float|int = 0.1,
        default:float|int = 0.0,
        minimum:float|int = 0.0,
        maximum:float|int = 1.0,
        smoothing:float = 1.0,
        loop:bool = False,
        show_sign:bool = False,
        decimals:int = 1,
        prepend:str = "",
        append:str = "",
    ):
        super().__init__(title)
        self._step = step
        self._default = default
        self._value = default
        self._minimum = minimum
        self._maximum = maximum
        self._smoothing = smoothing
        self._loop = loop
        self._show_sign = show_sign
        self.decimals = decimals
        self._prepend = prepend
        self._append = append

    @property
    def decimals(self) -> int:
        return self._decimals

    @decimals.setter
    def decimals(self, value:int) -> None:
        self._decimals = max(value, 0)

    @property
    def smoothing(self) -> bool:
        return self._smoothing != 1.0
    
    def _get_minimum(self) -> float|int:
        return 0.0 if self.smoothing else self._minimum
    
    def _get_maximum(self) -> float|int:
        return 1.0 if self.smoothing else self._maximum
    
    @property
    def value(self) -> float|int:
        if self.smoothing:
            return math.pow(self._value, self._smoothing) * (self._maximum - self._minimum) + self._minimum
        else:
            return self._value
    
    @value.setter
    def value(self, value:float|int) -> None:
        value = min(max(value, self._get_minimum()), self._get_maximum())
        if self._value != value:
            self._value = value
            self._do_update()

    @property
    def relative_value(self) -> float:
        return (self._value - self._get_minimum()) / (self._get_maximum() - self._get_minimum())
        
    @property
    def data(self) -> float|int:
        return self._value
    
    @property
    def label(self) -> str:
        value = self.value
        if type(value) is float:
            label = "{{:.{:d}f}}".format(self.decimals).format(value)
        else:
            label = ("{:+d}" if self._show_sign else "{:d}").format(value).replace("+0", "0")
        return "".join((self._prepend, label, self._append))
    
    def increment(self) -> bool:
        value = self._value + self._step
        if self._loop and value > self._get_maximum():
            value = self._get_minimum()
        else:
            value = min(value, self._get_maximum())
        if value == self._value:
            return False
        self.value = value
        return True
    
    def decrement(self) -> bool:
        value = self._value - self._step
        if self._loop and value < self._get_minimum():
            value = self._get_maximum()
        else:
            value = max(value, self._get_minimum())
        if value == self._value:
            return False
        self.value = value
        return True
    
    def reset(self) -> bool:
        if self._value == self._default:
            return False
        self.value = self._default
        return True

class Bool(Number):

    def __init__(
        self,
        title:str|Callable[[Item], str],
        default:bool = False,
        loop:bool = False,
        labels:tuple[str, str] = ("Off", "On"),
    ):
        super().__init__(
            title=title,
            step=1,
            default=int(default),
            minimum=0,
            maximum=1,
            loop=loop,
        )
        self._labels = labels

    @property
    def value(self) -> bool:
        return bool(self._value)
    
    @value.setter
    def value(self, value:bool) -> None:
        value = int(value)
        if self._value != value:
            self._value = value
            self._do_update()

    @property
    def label(self) -> str:
        return self._labels[self._value]

class Percentage(Number):
    
    def __init__(
        self,
        title:str|Callable[[Item], str],
        step:float=0.01,
        default:float=0.0,
        loop:bool=False,
    ):
        super().__init__(
            title,
            step=step,
            default=default,
            minimum=0.0,
            maximum=1.0,
            loop=loop,
        )
    
    @property
    def label(self) -> str:
        return "{:d}%".format(round(self.value * 100))
    
class Time(Number):

    def __init__(
        self,
        title:str|Callable[[Item], str],
        step:float=0.025,
        default:float=0.001,
        minimum:float=0.001,
        maximum:float=4.0,
        smoothing:float=3.0,
        decimals:int=3,
    ):
        super().__init__(
            title,
            step=step,
            default=default,
            minimum=minimum,
            maximum=maximum,
            smoothing=smoothing,
            loop=False,
            decimals=decimals,
            append="s",
        )
    
class List(Number):
    
    def __init__(
        self,
        title:str|Callable[[Item], str],
        items:tuple[str],
        default:int = 0,
        loop:bool = True,
    ):
        super().__init__(
            title,
            step=1,
            default=min(default, len(items) - 1),
            minimum = 0,
            maximum = len(items) - 1,
            loop=loop,
        )
        self._items = items

    @property
    def label(self) -> str:
        return self._items[self.value]

class Char(Number):

    def __init__(self, title:str|Callable[[Item], str]):
        super().__init__(
            title,
            step=1,
            default=0,
            minimum=0,
            maximum=len(_CHARACTERS)-1,
            loop=True,
        )
    
    @property
    def value(self) -> str:
        return _CHARACTERS[self._value]

    @value.setter
    def value(self, value:str|int):
        if type(value) is str:
            if not len(value):
                return
            value = _CHARACTERS.find(value[0])
            if value < 0:
                return
        self._value = value % len(_CHARACTERS)
        self._do_update()

    @property
    def label(self) -> str:
        return self.value

class String(Group):

    def __init__(self, title:str|Callable[[Item], str], length:int=16):
        self._length = length
        super().__init__(
            title,
            tuple([Char(str(i+1)) for i in range(length)]),
        )
    
    @property
    def value(self) -> tuple:
        return "".join([i.label for i in self._items])
    
    @value.setter
    def value(self, value:str) -> None:
        for i in range(min(len(value), self._length)):
            self._items[i].value = value[i]
        self._do_update()
    
    @property
    def data(self) -> str:
        return self.label
    
    @data.setter
    def data(self, value:str) -> None:
        self.value = value

    @property
    def label(self) -> str:
        return self.value

class WaveformList(List):

    def __init__(
        self,
        title:str|Callable[[Item], str],
        items:tuple[str, Callable[[], np.ndarray]],
    ):
        super().__init__(title, items)

    @property
    def label(self) -> str:
        return self._items[self.value][0]
    
    @property
    def data(self) -> np.ndarray:
        return self._items[self.value][1]()


class Waveform(Group):

    waveform:WaveformList = None
    loop_start:Percentage = None
    loop_end:Percentage = None

    def __init__(
        self,
        title:str|Callable[[Item], str],
        items:tuple[str, Callable[[], np.ndarray]],
    ):
        self.waveform = WaveformList(
            "Waveform",
            items,
        )
        self.loop_start = Percentage(
            "Loop Start",
            default=0.0,
        )
        self.loop_start.on_update = self._update_loop_start
        self.loop_end = Percentage(
            "Loop End",
            default=1.0,
        )
        self.loop_end.on_update = self._update_loop_end
        super().__init__(title, (self.waveform, self.loop_start, self.loop_end))

    def _update_loop_start(self, value:float, item:Item) -> None:
        if value > self.loop_end.value:
            self.loop_end.value = value

    def _update_loop_end(self, value:float, item:Item) -> None:
        if value < self.loop_start.value:
            self.loop_start.value = value


class AREnvelope(Group):

    attack_time:Time = None
    sustain_level:Number = None
    release_time:Time = None

    def __init__(self, title:str|Callable[[Item], str]):
        self.attack_time = Time("Attack Time")
        self.sustain_level = Number("Sustain Level", step=0.05)
        self.release_time = Time("Release Time")
        super().__init__(title, (self.attack_time, self.sustain_level, self.release_time))

class ADSREnvelope(Group):

    attack_time:Time = None
    attack_level:Number = None
    decay_time:Time = None
    sustain_level:Number = None
    release_time:Time = None

    def __init__(self, title:str|Callable[[Item], str]):
        self.attack_time = Time("Attack Time")
        self.attack_level = Number("Attack Level", default=1.0, step=0.05)
        self.decay_time = Time("Decay Time")
        self.sustain_level = Number("Sustain Level", default=0.75, step=0.05)
        self.release_time = Time("Release Time")
        super().__init__(title, (
            self.attack_time,
            self.attack_level,
            self.decay_time,
            self.sustain_level,
            self.release_time
        ))

class LFO(Group):

    depth:Number = None
    rate:Number = None

    def __init__(self, title:str|Callable[[Item], str]):
        self.depth = Number(
            "Depth",
            step=0.01,
            maximum=0.5,
            smoothing=2.0,
        )
        self.rate = Number(
            "Rate",
            step=0.01,
            maximum=32.0,
            smoothing=2.0,
        )
        super().__init__(title, (self.depth, self.rate))

class Filter(Group):

    type:List = None
    frequency:Number = None
    resonance:Number = None

    def __init__(self, title:str|Callable[[Item], str]):
        self.type = List(
            "Type",
            ("Low Pass", "High Pass", "Band Pass"),
        )
        self.frequency = Number(
            "Frequency",
            default=1.0,
            step=0.01,
            smoothing=3.0,
        )
        self.resonance = Number(
            "Resonance",
        )
        super().__init__(title, (
            self.type,
            self.frequency,
            self.resonance,
        ))

class Mix(Group):

    level:Number = None
    pan:Number = None

    def __init__(self, title:str|Callable[[Item], str]):
        self.level = Number(
            "Level",
            default=1.0,
            step=0.025,
        )
        self.pan = Number(
            "Pan",
            step=0.1,
            minimum=-1.0,
        )
        super().__init__(title, (
            self.level,
            self.pan,
        ))

class Tune(Group):

    coarse:Number = None
    fine:Number = None
    glide:Time = None
    bend:Number = None

    def __init__(self, title:str|Callable[[Item], str]):
        self.coarse = Number(
            "Coarse",
            step=1,
            minimum=-36,
            maximum=36,
            show_sign=True,
            decimals=0,
        )
        self.fine = Number(
            "Fine",
            step=1/12/12,
            minimum=-1/12,
            maximum=1/12,
            show_sign=True,
            decimals=3,
        )
        self.glide = Time(
            "Glide",
            step=0.05,
            minimum=0.0,
            maximum=2.0,
        )
        self.bend = Number(
            "Bend",
            step=1/24,
            minimum=-2.0,
            maximum=2.0,
            show_sign=True,
            decimals=2,
        )
        super().__init__(title, (
            self.coarse,
            self.fine,
            self.glide,
            self.bend,
        ))

class Patch(Group):

    patch:Number = None
    name:String = None

    def __init__(self, title:str|Callable[[Item], str], count:int=16):
        self.patch = Number(
            "Patch",
            step=1,
            default=0,
            maximum=count-1,
            loop=True,
            decimals=0,
        )
        self.name = String(
            "Name",
        )
        super().__init__(title, (self.patch, self.name))
