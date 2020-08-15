// This source file is part of Spadecs.
// Spadecs is available through the world-wide-web at this URL:
//   https://github.com/Conticop/Spadecs
//
// This source file is subject to the MIT license.
//
// Copyright (c) 2020
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

using System.Collections.Generic;
using System.Runtime.CompilerServices;

using c_ubyte = System.Byte;
using c_int32 = System.Int32;
using c_char_p = System.String;

[assembly: InternalsVisibleTo("Spadecs.Boot")]

namespace Spadecs
{
    using static PyRegistry;

    public unsafe struct PyBindings
    {
        public static readonly delegate* cdecl<c_char_p, c_int32> MyPythonicFunction;
        public static readonly delegate* cdecl<c_ubyte, void> CPlayer_KickByID;

        static PyBindings()
        {
            MyPythonicFunction = (delegate* cdecl<c_char_p, c_int32>)PyFunctions["my_pythonic_function"];
            CPlayer_KickByID = (delegate* cdecl<c_ubyte, void>)PyFunctions["cplayer_kick_by_id"];
        }
    }

    internal static class PyRegistry
    {
        internal static Dictionary<string, ulong> PyFunctions;

        static PyRegistry()
        {
        }
    }
}