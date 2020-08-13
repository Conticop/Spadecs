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

import os
import sys
from collections import namedtuple


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
CONNECTION = None
CONFIG = None


# class csig(object):
#     def __init__(self, *args):
#         self._args = args
#
#     @classmethod
#     def methods(cls, subject):
#         def g():
#             for name in dir(subject):
#                 method = getattr(subject, name)
#                 if isinstance(method, csig):
#                     yield name, method
#
#         return {name: method for name, method in g()}


def csig2(*types):
    def check_accepts(f):
        assert len(types) == f.func_code.co_argcount + 1
        FUNCTIONS[f.func_name] = (f, *types)

        def new_f(*args, **kwargs):
            # for (a, t) in zip(args, types):
            #     assert isinstance(a, t), "arg %r does not match %s" % (a, t)
            return f(*args, **kwargs)

        new_f.func_name = f.func_name
        return new_f

    return check_accepts


def csig3(*types):
    def check_accepts(f):
        assert len(types) == f.__code__.co_argcount + 1
        FUNCTIONS[f.__name__] = (f, *types)

        def new_f(*args, **kwargs):
            # for (a, t) in zip(args, types):
            #     assert isinstance(a, t), "arg %r does not match %s" % (a, t)
            return f(*args, **kwargs)

        new_f.__name__ = f.__name__
        return new_f

    return check_accepts


csig = csig3 if PYTHON_3 else csig2
