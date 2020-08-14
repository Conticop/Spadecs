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
from typing import Callable, Optional, Type

PLATFORM = sys.platform
X64 = sys.maxsize > 2 ** 32
PYTHON_3 = sys.version_info > (3, 0)
ENVIRON = os.environ
CURDIR = os.path.dirname(os.path.abspath(__file__))
Runtime = namedtuple("Runtime", "name version path")
FUNCTIONS = {}
BINDINGS = {}
BINDINGS_JSON = {}
IMPORTED_FUNCTIONS = {}
CLR_LIB = None
CLR_HANDLE = None
CLR_DOMAIN = None
FUNCTION_IMPORTER = None  # type: Callable
PROTOCOL = None
PROTOCOL_OBJ = None
CONNECTION = None
CONNECTION_OBJ = None
CONFIG = None


def pyexport(restype: Optional[Type['_CData']] = None, *argtypes: Type['_CData']):
    """
    Decorator used to register user-defined function as a binding to be used/called in .NET.
    The first argument is a return type (None means void; no return value).
    The rest is optional (specify argument types).
    Use c_<type>.
    """

    def _unpack_args(*args) -> list:
        return [v.decode("utf-8") if argtypes[i] is c_char_p and isinstance(v, bytes) else v for i, v in enumerate(args)]

    def pybinding(f):
        assert len(argtypes) == f.__code__.co_argcount

        def pymethod(*args):
            assert len(args) == len(argtypes), "Invalid number of arguments"
            return f(*_unpack_args(*args))

        def pymethod_string(*args) -> str:
            # Special handling for `string` return type (automatically decode to UTF8).
            return pymethod(*args).decode("utf-8")

        pymethod_string.__name__ = pymethod.__name__ = f.__name__
        func = pymethod_string if restype is c_char_p else pymethod
        FUNCTIONS[f.__name__] = (func, restype, *argtypes)
        return func

    return pybinding


def _pack_args(*args) -> list:
    return [v.encode("utf-8") if isinstance(v, str) else v for v in args]


def pyimport(assembly_name: str, class_name: str, method_name: str, restype: Optional[Type['_CData']] = None, *argtypes: Type['_CData']):
    """
    Decorator used to import user-defined function from .NET to be used/called in Python.
    """

    def netbinding(f):
        assert len(argtypes) == f.__code__.co_argcount
        fptr = FUNCTION_IMPORTER(class_name, method_name, assembly_name)
        managed_method = CFUNCTYPE(restype, *argtypes)(fptr.value)
        IMPORTED_FUNCTIONS[id(f)] = (managed_method, class_name, method_name, *argtypes)

        def netmethod(*args):
            assert len(args) == len(argtypes), "Invalid number of arguments"
            return managed_method(*_pack_args(*args))

        def netmethod_string(*args) -> str:
            # Special handling for `string` return type (automatically decode to UTF8).
            return netmethod(*args).decode("utf-8")

        netmethod_string.__name__ = netmethod.__name__ = f.__name__
        return netmethod_string if restype is c_char_p else netmethod

    return netbinding


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
