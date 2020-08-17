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
import glob
import importlib
import json
import os
import re
import shutil
import signal
import sys
import weakref
from ctypes import *
from os.path import abspath, dirname, isdir, join
from subprocess import check_output
from typing import List, Optional, Tuple

sys.path.insert(1, abspath(dirname(__file__)))  # Fix dotnet_* imports.
import dotnet_const


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
        if isdir(tmp):
            return tmp
    if "DOTNETHOME" in dotnet_const.ENVIRON:
        tmp = dotnet_const.ENVIRON["DOTNETHOME"]
        if isdir(tmp):
            return tmp
    if "DOTNET_ROOT" in dotnet_const.ENVIRON:
        tmp = dotnet_const.ENVIRON["DOTNET_ROOT"]
        if isdir(tmp):
            return tmp
    tmp = shutil.which(get_exe_name("dotnet"))
    if tmp:
        try:
            tmp2 = os.readlink(tmp) if dotnet_const.PYTHON_3 else tmp
            tmp = tmp2 if os.path.isabs(tmp2) else abspath(join(dirname(tmp), tmp2))
        except OSError:
            pass
        tmp = dirname(tmp)
        if isdir(tmp):
            return tmp
    return None


def get_dotnet_runtimes() -> List[dotnet_const.Runtime]:
    """
    Fetch a list of all installed .NET Core runtimes.
    """
    runtimes = []
    for line in check_output([get_exe_name("dotnet"), "--list-runtimes"]).decode("utf-8").splitlines():
        name, version, path = line.split(" ", 2)
        path = join(path[1:-1], version)
        runtimes.append(dotnet_const.Runtime(name=name, version=version, path=path))
    return runtimes


def get_latest_runtime(dotnet_dir: Optional[str] = None, version_major: Optional[int] = 5,
                       version_minor: Optional[int] = 0, version_build: Optional[int] = 0) -> Optional[str]:
    """
    Search and select the latest installed .NET Core runtime directory.
    """
    dotnet_dir = dotnet_dir or get_dotnet_dir()
    if not dotnet_dir:
        return None
    if "DOTNETRUNTIMEVERSION" in dotnet_const.ENVIRON:
        tmp = join(dotnet_dir, "shared", "Microsoft.NETCore.App", dotnet_const.ENVIRON["DOTNETRUNTIMEVERSION"])
        if isdir(tmp):
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
    tmp = join(dotnet_dir, "shared", "Microsoft.NETCore.App", runtime.version)
    if isdir(tmp):
        return tmp
    tmp = join(runtime.path, runtime.version)
    if isdir(tmp):
        return tmp
    return None


def LoadCoreCLR(assembly_path: str, assembly_name: str, class_name: str,
                runtime_version: Optional[Tuple[int, int, int]] = None,
                load_name: Optional[str] = "OnLoad", unload_name: Optional[str] = "OnUnload"):
    assert dotnet_const.CLR_LIB is None, ".NET CLR is already loaded"
    assert os.path.isfile(assembly_path), "Target assembly is missing ({})".format(assembly_path)
    dotnet_dir = get_dotnet_dir()
    assert dotnet_dir is not None, ".NET Runtime is not installed"
    runtime_path = get_latest_runtime(dotnet_dir, *runtime_version)
    assert runtime_path is not None, \
        ".NET Runtime version is not sufficient, must be v{}.{}.{} or higher".format(*runtime_version)
    coreclr_path = join(runtime_path, get_library_name("coreclr"))
    assert os.path.isfile(coreclr_path), "Core CLR library is missing ({})".format(coreclr_path)
    _CLRLIB = LoadLibrary(coreclr_path)
    assert _CLRLIB is not None, "Failed to load .NET CLR library"

    properties = {
        "TRUSTED_PLATFORM_ASSEMBLIES": os.pathsep.join(
            glob.glob(join(runtime_path, "*.dll")) +
            glob.glob(join(dirname(assembly_path), "*.dll"))
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
    error_code = _CLRLIB.coreclr_initialize(
        c_char_p(sys.executable.encode("utf-8")),
        c_char_p("DefaultDomain".encode("utf-8")),
        c_int32(len(properties)),
        PropType(*property_keys),
        PropType(*property_values),
        byref(_CLR_handle),
        byref(_CLR_domain)
    )
    assert error_code == 0, "Core CLR initialization failed (code={})".format(error_code)
    del error_code, properties, property_keys, property_values, PropType

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
        nonlocal _CLRLIB, assembly_name
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
        del error_code
        return func_ptr

    dotnet_const.CLR_LIB = _CLRLIB
    dotnet_const.CLR_HANDLE = _CLR_handle
    dotnet_const.CLR_DOMAIN = _CLR_domain
    dotnet_const.FUNCTION_IMPORTER = GetManagedFunctionPointer

    on_load_func_ptr = GetManagedFunctionPointer(class_name, load_name)
    on_unload = CFUNCTYPE(None)(GetManagedFunctionPointer(class_name, unload_name).value)

    def exit_handler(*args, **kwargs):
        nonlocal _CLRLIB, on_unload
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
            error_code = _CLRLIB.coreclr_shutdown(_CLR_handle.value, _CLR_domain.value)
            if error_code != 0:
                print(".NET CLR shutdown (code={})".format(error_code))
            dotnet_const.CLR_LIB = None
            dotnet_const.CLR_HANDLE = None
            dotnet_const.CLR_DOMAIN = None
            dotnet_const.FUNCTION_IMPORTER = None
            dotnet_const.FUNCTIONS.clear()
            dotnet_const.BINDINGS.clear()
            dotnet_const.BINDINGS_JSON.clear()
            dotnet_const.IMPORTED_FUNCTIONS.clear()
            dotnet_const.OBJECTS.clear()
            del _CLRLIB, _CLR_handle, _CLR_domain, on_unload, error_code, \
                dotnet_const.FUNCTION_IMPORTER, dotnet_const.FUNCTIONS, \
                    dotnet_const.BINDINGS, dotnet_const.BINDINGS_JSON, \
                        dotnet_const.IMPORTED_FUNCTIONS, dotnet_const.OBJECTS

    atexit.register(exit_handler)
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    jsonData = json.dumps(dotnet_const.BINDINGS_JSON, separators=(',', ':'))
    CFUNCTYPE(None, c_char_p)(on_load_func_ptr.value)(jsonData.encode("utf-8"))
    del jsonData

    # noinspection PyUnresolvedReferences
    import dotnet_exports  # This import is required (in order to call .NET methods from Python).

    return GetManagedFunctionPointer


def apply_script(protocol, connection, config):
    dotnet_const.PROTOCOL = protocol
    dotnet_const.CONNECTION = connection
    dotnet_const.CONFIG = config
    dotnet_const.FUNCTIONS = {}
    dotnet_const.BINDINGS = {}
    dotnet_const.BINDINGS_JSON = {}
    dotnet_const.IMPORTED_FUNCTIONS = {}
    dotnet_const.OBJECTS = {}
    dotnet_const.MEMORY = weakref.WeakValueDictionary()
    import dotnet_protocol
    import dotnet_connection
    # noinspection PyUnresolvedReferences
    import dotnet_bindings  # This import is required (in order to register any bindings at all).
    for fid, ft in dotnet_const.FUNCTIONS.items():
        func = ft[0]
        ftypes = ft[1:]
        # print(func, *ftypes)
        fref = CFUNCTYPE(*ftypes)(func)
        dotnet_const.BINDINGS[fid] = fref
        fptr = cast(fref, c_void_p).value
        dotnet_const.BINDINGS_JSON[fid] = fptr
    bootstrapper_path = join(dotnet_const.CURDIR, "dotnet", "net5.0", "Spadecs.Boot.dll")
    LoadCoreCLR(bootstrapper_path, "Spadecs.Boot, Version=1.0.0.0", "Spadecs.Bootstrapper", runtime_version=(5, 0, 0))
    # noinspection PyTypeChecker
    importlib.reload(dotnet_protocol)
    # noinspection PyTypeChecker
    importlib.reload(dotnet_connection)
    import dotnet_exports
    print("(Python to .NET) {} returned: {}".format(dotnet_exports.dotnet_get_test_string.__name__,
                                                    dotnet_exports.dotnet_get_test_string()))
    return dotnet_protocol.DotNetProtocol, dotnet_connection.DotNetConnection


print("[dotnet] Running Python {} ({}-bit) on {}.".format("3" if dotnet_const.PYTHON_3 else "2",
                                                          "64" if dotnet_const.X64 else "32",
                                                          get_platform_name()))
if not dotnet_const.PYTHON_3:
    print("[dotnet] WARNING: Python 2 is no longer supported!")
if __name__ == "__main__":
    class DummyType:
        pass

    class DummyConnection:
        address = ["127.0.0.1"]

        def on_connect(self, *args, **kwargs):
            self.player_id = 0

    sys.path.insert(1, abspath(join(dirname(__file__), "..", "..")))  # Fix server imports.
    protocol, connection = apply_script(DummyType, DummyConnection, DummyType)
    protocol()
    connection()
    connection.on_connect(connection)
    print("The End.")
