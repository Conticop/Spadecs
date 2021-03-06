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

"""
This file defines all Python functions (API) which are exported to .NET for consumption.
"""

from ctypes import *
import dotnet_const
from dotnet_const import pyexport
import json
import pyspades
from pyspades.constants import ERROR_KICKED


@pyexport(c_int32, c_char_p)
def my_pythonic_function(value: str) -> int:
    print("(.NET to Python)", value)
    return 123


@pyexport(None, c_ubyte)
def cplayer_kick_by_id(pid: int) -> None:
    # print("cplayer_kick_by_id", pid)
    if pid in dotnet_const.PROTOCOL_OBJ.players:
        ply = dotnet_const.PROTOCOL_OBJ.players[pid]
        # print("Player:", ply)
        if ply:
            ply.disconnect(ERROR_KICKED)


@pyexport(None)
def dotnet_get_objects() -> None:
    # noinspection PyUnresolvedReferences
    from dotnet_exports import dotnet_event_update_objects
    # This is a stupid fix (can't return a string directly), but I don't have time to do a cleaner implementation.
    dotnet_event_update_objects(json.dumps(dotnet_const.OBJECTS, separators=(',', ':')))
