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
import os
import re
import shutil
import sys
from collections import namedtuple
from subprocess import check_output
from ctypes import *

PLATFORM = sys.platform
X64 = sys.maxsize > 2 ** 32
PYTHON_3 = hasattr(os, "readlink")
ENVIRON = os.environ
__DIR__ = os.path.dirname(os.path.abspath(__file__))
Runtime = namedtuple("Runtime", "name version path")
_CLRLIB, _CLR_handle, _CLR_domain = None, None, None

# Monkey-patch for Python 2, implementing "shutil.which" function.
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

        path = (path or ENVIRON.get("PATH", os.defpath)).split(os.pathsep)

        if sys.platform == "win32":
            # The current directory takes precedence on Windows.
            curdir = os.curdir
            if curdir not in path:
                path.insert(0, curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = ENVIRON.get("PATHEXT", "").split(os.pathsep)
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
        for dir in path:
            normdir = os.path.normcase(dir)
            if normdir not in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None


    shutil.which = shutil_which


def get_platform_name():
    if PLATFORM == "win32":
        return "Windows"
    if PLATFORM == "darwin":
        return "Mac"
    return "Linux"


def get_exe_name(name):
    if PLATFORM == "win32":
        return "{}.exe".format(name)
    return name


def get_library_name(name):
    if PLATFORM == "win32":
        return "{}.dll".format(name)
    if PLATFORM == "darwin":
        return "lib{}.dylib".format(name)
    return "lib{}.so".format(name)


def LoadLibrary(name):
    if PLATFORM == "win32":
        return WinDLL(name)
    return CDLL(name)


# Retrieve .NET Core installation directory.
def get_dotnet_dir():
    tmp = "DOTNETHOME_X{}".format("64" if X64 else "86")
    if tmp in ENVIRON:
        tmp = ENVIRON[tmp]
        if os.path.isdir(tmp):
            return tmp
    if "DOTNETHOME" in ENVIRON:
        tmp = ENVIRON["DOTNETHOME"]
        if os.path.isdir(tmp):
            return tmp
    if "DOTNET_ROOT" in ENVIRON:
        tmp = ENVIRON["DOTNET_ROOT"]
        if os.path.isdir(tmp):
            return tmp
    tmp = shutil.which(get_exe_name("dotnet"))
    if tmp:
        try:
            tmp2 = os.readlink(tmp) if PYTHON_3 else tmp
            tmp = tmp2 if os.path.isabs(tmp2) else os.path.abspath(os.path.join(os.path.dirname(tmp), tmp2))
        except OSError:
            pass
        tmp = os.path.dirname(tmp)
        if os.path.isdir(tmp):
            return tmp
    return None


# Fetch a list of all installed .NET Core runtimes.
def get_dotnet_runtimes():
    runtimes = []
    for line in check_output([get_exe_name("dotnet"), "--list-runtimes"]).decode("utf8").splitlines():
        name, version, path = line.split(" ", 2)
        path = os.path.join(path[1:-1], version)
        runtimes.append(Runtime(name=name, version=version, path=path))
    return runtimes


# Search and select the latest installed .NET Core runtime directory.
def get_latest_runtime(dotnet_dir=None, runtime_version_major=3, runtime_version_minor=0, runtime_version_build=0):
    dotnet_dir = dotnet_dir or get_dotnet_dir()
    if not dotnet_dir:
        return None
    if "DOTNETRUNTIMEVERSION" in ENVIRON:
        tmp = os.path.join(dotnet_dir, "shared", "Microsoft.NETCore.App", ENVIRON["DOTNETRUNTIMEVERSION"])
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
                if tmp_major > runtime_version_major:
                    runtime_version_major = tmp_major
                    runtime_version_minor = tmp_minor
                    runtime_version_build = tmp_build
                    runtime = r
                    continue
                if runtime_version_major == tmp_major:
                    if tmp_minor > runtime_version_minor:
                        runtime_version_minor = tmp_minor
                        runtime_version_build = tmp_build
                        runtime = r
                        continue
                    if runtime_version_minor == tmp_minor and tmp_build > runtime_version_build:
                        runtime_version_build = tmp_build
                        runtime = r
                        continue
    tmp = os.path.join(dotnet_dir, "shared", "Microsoft.NETCore.App", runtime.version)
    return tmp if os.path.isdir(tmp) else None
    # return runtime.path


def apply_script(protocol, connection, config):
    global _CLRLIB, _CLR_handle, _CLR_domain
    if _CLRLIB is not None:
        return protocol, connection

    bootstrapper_path = os.path.join(__DIR__, "dotnet", "netstandard2.1", "_boot.dll")
    assert os.path.isfile(bootstrapper_path), "Bootstrapper library is missing ({})".format(bootstrapper_path)
    dotnet_dir = get_dotnet_dir()
    assert dotnet_dir is not None, ".NET Core is not installed"
    runtime_path = get_latest_runtime(dotnet_dir)
    assert runtime_path is not None, ".NET Core runtime version is not sufficient, must be v3.0 or higher"
    coreclr_path = os.path.join(runtime_path, get_library_name("coreclr"))
    assert os.path.isfile(coreclr_path), "Core CLR library is missing ({})".format(coreclr_path)
    _CLRLIB = LoadLibrary(coreclr_path)
    assert _CLRLIB is not None, "Failed to load Core CLR library"

    properties = {
        "TRUSTED_PLATFORM_ASSEMBLIES": os.pathsep.join(
            glob.glob(os.path.join(runtime_path, "*.dll")) + [bootstrapper_path]
        )
    }
    PropType = c_char_p * len(properties)
    _CLRLIB.coreclr_initialize.restype = c_uint
    _CLRLIB.coreclr_initialize.argtypes = [
        c_char_p,
        c_char_p,
        c_int,
        POINTER(PropType),
        POINTER(PropType),
        POINTER(c_void_p),
        POINTER(c_uint)
    ]
    _CLR_handle = c_void_p()
    _CLR_domain = c_uint()
    property_keys = []
    for k in properties.keys():
        property_keys.append(k.encode("utf8"))
    property_values = []
    for v in properties.values():
        property_values.append(v.encode("utf8"))
    err_code = _CLRLIB.coreclr_initialize(
        c_char_p(sys.executable.encode("utf8")),
        c_char_p("mydotnetcore".encode("utf8")),
        c_int(len(properties)),
        PropType(*property_keys),
        PropType(*property_values),
        byref(_CLR_handle),
        byref(_CLR_domain)
    )
    assert err_code == 0, "Core CLR initialization failed (code={})".format(err_code)

    _CLRLIB.coreclr_create_delegate.restype = c_uint
    _CLRLIB.coreclr_create_delegate.argtypes = [
        c_void_p,
        c_uint,
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p)
    ]
    func_ptr = c_void_p()
    err_code = _CLRLIB.coreclr_create_delegate(
        _CLR_handle.value,
        _CLR_domain.value,
        "_boot, Version=1.0.0.0".encode("utf8"),
        "_Internal.Bootstrapper".encode("utf8"),
        "OnLoad".encode("utf8"),
        byref(func_ptr)
    )
    assert err_code == 0, "Failed to create OnLoad delegate (code={})".format(err_code)

    def exit_handler():
        func_ptr = c_void_p()
        err_code = _CLRLIB.coreclr_create_delegate(
            _CLR_handle.value,
            _CLR_domain.value,
            "_boot, Version=1.0.0.0".encode("utf8"),
            "_Internal.Bootstrapper".encode("utf8"),
            "OnUnload".encode("utf8"),
            byref(func_ptr)
        )
        if err_code == 0:
            try:
                CFUNCTYPE(None)(func_ptr.value)()
            except:
                pass
        _CLRLIB.coreclr_shutdown.restype = c_int
        _CLRLIB.coreclr_shutdown.argtypes = [
            c_void_p,
            c_uint
        ]
        err_code = _CLRLIB.coreclr_shutdown(_CLR_handle.value, _CLR_domain.value)
        print("Core CLR shutdown (code={})".format(err_code))

    atexit.register(exit_handler)

    CFUNCTYPE(None)(func_ptr.value)()

    return protocol, connection


print("[dotnet] Running Python {} ({}-bit) on {}.".format("3" if PYTHON_3 else "2", "64" if X64 else "32", get_platform_name()))
if __name__ == "__main__":
    apply_script(None, None, None)
