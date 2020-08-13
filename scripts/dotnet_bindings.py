from dotnet_const import csig
from ctypes import *


@csig(c_int32, c_char_p)
def my_pythonic_function(value: bytes) -> int:
    print(value.decode("utf-8"))
    return 123
