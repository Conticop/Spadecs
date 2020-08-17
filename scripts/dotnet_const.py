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
import weakref
from collections import namedtuple
from ctypes import *
from typing import Callable, Optional, Type

PLATFORM = sys.platform
X64 = sys.maxsize > 2 ** 32
PYTHON_3 = sys.version_info > (3, 0)
ENVIRON = os.environ
CURDIR = os.path.dirname(os.path.abspath(__file__))
Runtime = namedtuple("Runtime", "name version path")

FUNCTIONS = None  # type: dict
BINDINGS = None  # type: dict
BINDINGS_JSON = None  # type: dict
IMPORTED_FUNCTIONS = None  # type: dict

# [string] = (id(value), str(type(value))).
OBJECTS = None  # type: dict
# [id(value)] = value.
MEMORY = None  # type: weakref.WeakValueDictionary

CLR_LIB = None
CLR_HANDLE = None
CLR_DOMAIN = None
FUNCTION_IMPORTER = None  # type: Callable
PROTOCOL = None
PROTOCOL_OBJ = None
CONNECTION = None
CONFIG = None


def track_object(value, name: Optional[str] = None) -> bool:
    """
    Makes the given object/value "trackable" across language boundaries (Python -> .NET and vice versa).
    Optionally, specify a unique name to be assigned (to help identify an object easier).
    """

    assert value is not None, "Can not track a None value"
    obj_id = id(value)
    if obj_id in MEMORY:
        return False
    if name:
        if name in OBJECTS:
            return False
        OBJECTS[name] = (str(obj_id), str(type(value)))
    MEMORY[obj_id] = value
    return True


def _release_object(obj_id: int) -> bool:
    if obj_id in MEMORY:
        del MEMORY[obj_id]
        return True
    return False


def untrack_object(value, check_named: Optional[bool] = False) -> bool:
    """
    Removes "tracking" from the given value. Consider using untrack_named_object if name were assigned.
    """

    assert value is not None, "Can not untrack a None value"
    obj_id = id(value)
    if check_named:
        # Remove all 'obj_id' value(s) from OBJECTS. This is a hacked up implementation, but it will work for now.
        ks, vs, idx, size = list(OBJECTS.keys()), list(OBJECTS.values()), 0, len(OBJECTS)
        assert size == len(ks) and len(ks) == len(vs), "__should_never_see_this__"
        while idx < size:
            k, v = ks[idx], vs[idx]
            if v[0] == str(obj_id):
                del ks[idx], vs[idx], OBJECTS[k], k, v
                size -= 1
                continue  # Keep the loop going (in case there are multiple).
            idx += 1
            del k, v
        del ks, vs, idx, size
    return _release_object(obj_id)


def untrack_named_object(name: str) -> bool:
    """
    Removes "tracking" from the given named object.
    """

    if name in OBJECTS:
        obj_id = int(OBJECTS[name][0])
        del OBJECTS[name]
        return _release_object(obj_id)
    return False


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

        def pymethod_string(*args):
            # Special handling for `string` return type (automatically encode to UTF8).
            assert False, "THIS SHIT DOESN'T WORK!!        WHY?        HAS I EVER?"
            # retval = pymethod(*args)
            # retval = retval.encode("utf-8")
            # print(retval, type(retval))
            # chptr = c_char_p(retval)
            # print(chptr.value)
            # return chptr.value

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
        IMPORTED_FUNCTIONS[id(f)] = (managed_method, class_name, method_name, restype, *argtypes)

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
