# This source file is part of Spadecs.
# Spadecs is available through the world-wide-web at this URL:
#   https://github.com/Conticop/Spadecs
#
# This source file is subject to the MIT license.
#
# Copyright (c) 2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import enum
import os
import sys
from collections import namedtuple
from ctypes import *
from typing import Optional, Type

PLATFORM = sys.platform
X64 = sys.maxsize > 2 ** 32
PYTHON_3 = sys.version_info > (3, 0)
ENVIRON = os.environ
CURDIR = os.path.dirname(os.path.abspath(__file__))
Runtime = namedtuple("Runtime", "name version path")
FUNCTIONS = {}
BINDINGS = {}
BINDINGS_JSON = {}
PROTOCOL = None
PROTOCOL_OBJ = None
CONNECTION = None
CONNECTION_OBJ = None
CONFIG = None


def csig(restype: Optional[Type['_CData']] = None, *argtypes: Type['_CData']):
    """
    Decorator used to register user-defined function as a binding.
    The first argument is a return type (None means void; no return value).
    The rest is optional (specify argument types).
    Use c_<type>.
    """
    def pybinding(f):
        assert len(argtypes) == (f.__code__ if PYTHON_3 else f.func_code).co_argcount
        FUNCTIONS[f.__name__ if PYTHON_3 else f.func_name] = [f, restype, *argtypes]
        return f

    return pybinding


class StructureWithEnums(Structure):
    _map = {}

    def __getattribute__(self, name):
        _map = Structure.__getattribute__(self, "_map")
        value = Structure.__getattribute__(self, name)
        if name in _map:
            EnumClass = _map[name]
            if isinstance(value, Array):
                return [EnumClass(x) for x in value]
            return EnumClass(value)
        return value

    def __str__(self):
        result = ["struct {0} {{".format(self.__class__.__name__)]
        for field in self._fields_:
            attr, attrType = field
            if attr in self._map:
                attrType = self._map[attr]
            value = getattr(self, attr)
            result.append("    {0} [{1}] = {2!r};".format(attr, attrType.__name__, value))
        result.append("};")
        return "\n".join(result)

    __repr__ = __str__


class ETeam(enum.IntEnum):
    BLUE = 0
    GREEN = 1
    SPECTATOR = 2


class Vector3(Structure):
    _fields_ = [
        ("X", c_float),
        ("Y", c_float),
        ("Z", c_float)
    ]


class CPlayer(StructureWithEnums):
    _fields_ = [
        ("Address", c_char_p),
        ("Name", c_char_p),
        ("Position", POINTER(Vector3)),
        ("Rotation", POINTER(Vector3)),
        ("Health", c_int32),
        ("Team", c_int32),
        ("ID", c_byte)
    ]
    _map = {
        "Team": ETeam
    }
