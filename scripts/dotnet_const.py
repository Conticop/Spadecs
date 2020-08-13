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
