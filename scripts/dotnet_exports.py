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
This file defines all dynamically imported functions (API) from .NET for consumption in Python.
"""

from ctypes import *
from dotnet_const import pyimport

_ASSEMBLY, _CLASS = "Spadecs, Version=1.0.0.0", "Spadecs.EventManager"


@pyimport(_ASSEMBLY, _CLASS, "GetTestString", c_char_p)
def dotnet_get_test_string() -> str:
    pass  # The body of this function will be automagically replaced at runtime.


@pyimport(_ASSEMBLY, _CLASS, "OnPrePlayerConnect", c_ubyte, c_char_p)
def dotnet_event_pre_player_connect(ip_address: str) -> int:
    pass  # The body of this function will be automagically replaced at runtime.


@pyimport(_ASSEMBLY, _CLASS, "OnPostPlayerConnect", c_ubyte, c_char_p, c_ubyte)
def dotnet_event_post_player_connect(ip_address: str, pid: int) -> int:
    pass  # The body of this function will be automagically replaced at runtime.
