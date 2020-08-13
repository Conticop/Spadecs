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

import atexit
import builtins
import functools
import glob
import inspect
import json
import os
import re
import shutil
import signal
import sys
import dotnet_const  # TODO: investigate if this will require import-fixup on actual server code
from ctypes import *
from subprocess import check_output
from types import FunctionType
from typing import List, Optional, Tuple


# def is_static_method(klass: type, attr: str, value=None):
#     if value is None:
#         value = getattr(klass, attr)
#     assert getattr(klass, attr) == value
#     for cls in inspect.getmro(klass):
#         if inspect.isroutine(value):
#             if attr in cls.__dict__:
#                 return isinstance(cls.__dict__[attr], staticmethod)
#     return False


# class CPlayer(Structure):
#     _fields_ = [
#         ("Address", c_char_p),
#         ("Name", c_char_p),
#         ("Position", POINTER(Vector3)),  # TODO: struct
#         ("Rotation", POINTER(Vector3)),  # TODO: struct
#         ("Health", c_int32),  # TODO: possibly c_byte
#         ("Team", c_byte),  # TODO: enum
#         ("ID", c_byte)
#     ]


# class PyObject(Structure):
#     _fields_ = []


# class PyOnLoadParams(PyObject):
#     _fields_ = [
#         ("json", c_char_p)
#     ]


"""
Monkey-patch/Poly-fill for Python 2, implementing "shutil.which" function.
"""
if not hasattr(shutil, "which"):
    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(fn, mode):
        return os.path.exists(fn) and os.access(fn, mode) and not os.path.isdir(fn)


    def shutil_which(cmd, mode=os.F_OK | os.X_OK, path=None):
        # Short circuit. If we're given a full path which matches the mode
        # and it exists, we're done here.
        if _access_check(cmd, mode):
            return cmd

        path = (path or dotnet_const.ENVIRON.get("PATH", os.defpath)).split(os.pathsep)

        if dotnet_const.PLATFORM == "win32":
            # The current directory takes precedence on Windows.
            curdir = os.curdir
            if curdir not in path:
                path.insert(0, curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = dotnet_const.ENVIRON.get("PATHEXT", "").split(os.pathsep)
            # See if the given file matches any of the expected path extensions.
            # This will allow us to short circuit when given "python.exe".
            # matches = [cmd for ext in pathext if cmd.lower().endswith(ext.lower())]
            matches = any(cmd.lower().endswith(ext.lower()) for ext in pathext)
            # If it does match, only test that one, otherwise we have to try
            # others.
            files = [cmd] if matches else [cmd + ext.lower() for ext in pathext]
        else:
            # On other platforms you don't have things like PATHEXT to tell you
            # what file suffixes are executable, so just pass on cmd as-is.
            files = [cmd]

        seen = set()
        for dt in path:
            normdir = os.path.normcase(dt)
            if normdir not in seen:
                seen.add(normdir)
                for f in files:
                    name = os.path.join(dt, f)
                    if _access_check(name, mode):
                        return name
        return None


    shutil.which = shutil_which


def get_platform_name() -> str:
    if dotnet_const.PLATFORM == "win32":
        return "Windows"
    if dotnet_const.PLATFORM == "darwin":
        return "Mac"
    return "Linux"


def get_exe_name(name: str) -> str:
    if dotnet_const.PLATFORM == "win32":
        return "{}.exe".format(name)
    return name


def get_library_name(name: str) -> str:
    if dotnet_const.PLATFORM == "win32":
        return "{}.dll".format(name)
    if dotnet_const.PLATFORM == "darwin":
        return "lib{}.dylib".format(name)
    return "lib{}.so".format(name)


def LoadLibrary(name: str):
    if dotnet_const.PLATFORM == "win32":
        return WinDLL(name)
    return CDLL(name)


def get_dotnet_dir() -> Optional[str]:
    """
    Retrieve .NET Core installation directory.
    """
    tmp = "DOTNETHOME_X{}".format("64" if dotnet_const.X64 else "86")
    if tmp in dotnet_const.ENVIRON:
        tmp = dotnet_const.ENVIRON[tmp]
        if os.path.isdir(tmp):
            return tmp
    if "DOTNETHOME" in dotnet_const.ENVIRON:
        tmp = dotnet_const.ENVIRON["DOTNETHOME"]
        if os.path.isdir(tmp):
            return tmp
    if "DOTNET_ROOT" in dotnet_const.ENVIRON:
        tmp = dotnet_const.ENVIRON["DOTNET_ROOT"]
        if os.path.isdir(tmp):
            return tmp
    tmp = shutil.which(get_exe_name("dotnet"))
    if tmp:
        try:
            tmp2 = os.readlink(tmp) if dotnet_const.PYTHON_3 else tmp
            tmp = tmp2 if os.path.isabs(tmp2) else os.path.abspath(os.path.join(os.path.dirname(tmp), tmp2))
        except OSError:
            pass
        tmp = os.path.dirname(tmp)
        if os.path.isdir(tmp):
            return tmp
    return None


def get_dotnet_runtimes() -> List[dotnet_const.Runtime]:
    """
    Fetch a list of all installed .NET Core runtimes.
    """
    runtimes = []
    for line in check_output([get_exe_name("dotnet"), "--list-runtimes"]).decode("utf-8").splitlines():
        name, version, path = line.split(" ", 2)
        path = os.path.join(path[1:-1], version)
        runtimes.append(dotnet_const.Runtime(name=name, version=version, path=path))
    return runtimes


def get_latest_runtime(dotnet_dir: str = None, version_major: int = 5, version_minor: int = 0, version_build: int = 0) \
        -> Optional[str]:
    """
    Search and select the latest installed .NET Core runtime directory.
    :type dotnet_dir: str
    :type version_major: int
    :type version_minor: int
    :type version_build: int
    """
    dotnet_dir = dotnet_dir or get_dotnet_dir()
    if not dotnet_dir:
        return None
    if "DOTNETRUNTIMEVERSION" in dotnet_const.ENVIRON:
        tmp = os.path.join(dotnet_dir, "shared", "Microsoft.NETCore.App", dotnet_const.ENVIRON["DOTNETRUNTIMEVERSION"])
        if os.path.isdir(tmp):
            return tmp
    runtime = None
    for r in get_dotnet_runtimes():
        if r.name == "Microsoft.NETCore.App":
            vmatch = re.match(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<build>\d+)", r.version)
            if vmatch:
                tmp_major = int(vmatch.group("major"))
                tmp_minor = int(vmatch.group("minor"))
                tmp_build = int(vmatch.group("build"))
                if tmp_major > version_major:
                    version_major = tmp_major
                    version_minor = tmp_minor
                    version_build = tmp_build
                    runtime = r
                    continue
                if version_major == tmp_major:
                    if tmp_minor > version_minor:
                        version_minor = tmp_minor
                        version_build = tmp_build
                        runtime = r
                        continue
                    if version_minor == tmp_minor:
                        if tmp_build > version_build:
                            version_build = tmp_build
                            runtime = r
                            continue
                        if runtime is None:
                            runtime = r
                            continue
    if runtime is None:
        return None
    tmp = os.path.join(dotnet_dir, "shared", "Microsoft.NETCore.App", runtime.version)
    if os.path.isdir(tmp):
        return tmp
    tmp = os.path.join(runtime.path, runtime.version)
    if os.path.isdir(tmp):
        return tmp
    return None


def LoadCoreCLR(assembly_path: str, assembly_name: str, class_name: str,
                runtime_version: Optional[Tuple[int, int, int]] = None,
                load_name: Optional[str] = "OnLoad", unload_name: Optional[str] = "OnUnload"):
    dotnet_dir = get_dotnet_dir()
    assert dotnet_dir is not None, ".NET Core is not installed"
    runtime_path = get_latest_runtime(dotnet_dir, *runtime_version)
    assert runtime_path is not None, ".NET Core runtime version is not sufficient, must be v{}.{}.{} or higher".format(*runtime_version)
    coreclr_path = os.path.join(runtime_path, get_library_name("coreclr"))
    assert os.path.isfile(coreclr_path), "Core CLR library is missing ({})".format(coreclr_path)
    _CLRLIB = LoadLibrary(coreclr_path)
    assert _CLRLIB is not None, "Failed to load Core CLR library"

    properties = {
        "TRUSTED_PLATFORM_ASSEMBLIES": os.pathsep.join(
            glob.glob(os.path.join(runtime_path, "*.dll")) +
            glob.glob(os.path.join(os.path.dirname(assembly_path), "*.dll"))
        )
    }
    PropType = c_char_p * len(properties)
    _CLRLIB.coreclr_initialize.restype = c_uint32
    _CLRLIB.coreclr_initialize.argtypes = [
        c_char_p,
        c_char_p,
        c_int32,
        POINTER(PropType),
        POINTER(PropType),
        POINTER(c_void_p),
        POINTER(c_uint32)
    ]
    _CLR_handle = c_void_p()
    _CLR_domain = c_uint32()
    property_keys = [k.encode("utf-8") for k in properties.keys()]
    property_values = [v.encode("utf-8") for v in properties.values()]
    err_code = _CLRLIB.coreclr_initialize(
        c_char_p(sys.executable.encode("utf-8")),
        c_char_p("DefaultDomain".encode("utf-8")),
        c_int32(len(properties)),
        PropType(*property_keys),
        PropType(*property_values),
        byref(_CLR_handle),
        byref(_CLR_domain)
    )
    assert err_code == 0, "Core CLR initialization failed (code={})".format(err_code)

    _CLRLIB.coreclr_create_delegate.restype = c_uint32
    _CLRLIB.coreclr_create_delegate.argtypes = [
        c_void_p,
        c_uint32,
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p)
    ]

    def GetManagedFunctionPointer(type_name: str, method_name: str, _assembly_name: Optional[str] = None) -> c_void_p:
        assert _CLRLIB is not None, "CLR state is garbage. CLR got shutdown?"
        func_ptr = c_void_p()
        error_code = _CLRLIB.coreclr_create_delegate(
            _CLR_handle.value,
            _CLR_domain.value,
            (_assembly_name or assembly_name).encode("utf-8"),
            type_name.encode("utf-8"),
            method_name.encode("utf-8"),
            byref(func_ptr)
        )
        assert error_code == 0 and func_ptr.value is not None, \
            "Failed to create {}.{} delegate (code={})".format(type_name, method_name, error_code)
        return func_ptr

    on_load_func_ptr = GetManagedFunctionPointer(class_name, load_name)
    on_unload = CFUNCTYPE(None)(GetManagedFunctionPointer(class_name, unload_name).value)

    def exit_handler(*args, **kwargs):
        nonlocal _CLRLIB
        if _CLRLIB is None:
            return
        try:
            on_unload()
        finally:
            _CLRLIB.coreclr_shutdown.restype = c_int32
            _CLRLIB.coreclr_shutdown.argtypes = [
                c_void_p,
                c_uint32
            ]
            nonlocal _CLR_handle, _CLR_domain
            err_code = _CLRLIB.coreclr_shutdown(_CLR_handle.value, _CLR_domain.value)
            if err_code != 0:
                print("Core CLR shutdown (code={})".format(err_code))
            del _CLRLIB, _CLR_handle, _CLR_domain

    atexit.register(exit_handler)
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    jsonData = json.dumps(dotnet_const.BINDINGS_JSON, separators=(',', ':'))
    CFUNCTYPE(None, c_char_p)(on_load_func_ptr.value)(c_char_p(jsonData.encode("utf-8")))

    return GetManagedFunctionPointer


def apply_script(protocol, connection, config):
    dotnet_const.PROTOCOL = protocol
    dotnet_const.CONNECTION = connection
    dotnet_const.CONFIG = config
    exec("import dotnet_bindings")  # This import is required (in order to load any bindings at all). (exec is used to prevent PyCharm from yelling at me.)
    for fid, ft in dotnet_const.FUNCTIONS.items():
        func = ft[0]
        ftypes = ft[1:]
        # print(func, *ftypes)
        ff = CFUNCTYPE(*ftypes)(func)
        dotnet_const.BINDINGS[fid] = ff
        fptr = cast(ff, c_void_p).value
        dotnet_const.BINDINGS_JSON[fid] = fptr
    bootstrapper_path = os.path.join(dotnet_const.CURDIR, "dotnet", "net5.0", "Spadecs.Boot.dll")
    assert os.path.isfile(bootstrapper_path), "Bootstrapper library is missing ({})".format(bootstrapper_path)
    LoadCoreCLR(bootstrapper_path, "Spadecs.Boot, Version=1.0.0.0", "Spadecs.Bootstrapper", runtime_version=(5, 0, 0))
    return protocol, connection


print("[dotnet] Running Python {} ({}-bit) on {}.".format("3" if dotnet_const.PYTHON_3 else "2", "64" if dotnet_const.X64 else "32",
                                                          get_platform_name()))
if __name__ == "__main__":
    apply_script(None, None, None)
