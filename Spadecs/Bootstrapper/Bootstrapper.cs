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

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text.Json;
using InlineIL;
using static InlineIL.IL;
using static InlineIL.IL.Emit;

namespace Spadecs
{
    public static class ModuleInitializer
    {
        static ModuleInitializer()
        {
            Console.WriteLine("static ModuleInitializer");
        }

        public static void Initialize()
        {
            Console.WriteLine("ModuleInitializer.Initialize");
        }
    }

    //[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    //public struct PyObject
    //{
    //}

    public unsafe struct PyBindings
    {
        public static readonly delegate* cdecl<string, int> MyPythonicFunction;

        static PyBindings()
        {
            PyBindings.MyPythonicFunction = (delegate* cdecl<string, int>)Bootstrapper.PyFunctions["my_pythonic_function"];
        }
    }

    public static unsafe class Bootstrapper
    {
        internal static Dictionary<string, ulong> PyFunctions;

        static Bootstrapper()
        {
        }

        public static void OnLoad(string json)
        {
            PyFunctions = JsonSerializer.Deserialize<Dictionary<string, ulong>>(json);
            Console.WriteLine(".NET CLR is running! {0}", TestReturnInt());
            Console.WriteLine(PyBindings.MyPythonicFunction("Hello World"));
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int TestReturnInt()
        {
            return 5;
            // Ldc_I4_5();
            // return Return<int>();
        }

        // [MethodImpl(MethodImplOptions.AggressiveInlining)]
        // public static int MyPythonicFunction(string value)
        // {
        //     Ldarg(nameof(value));
        //     Ldsfld(new FieldRef(typeof(Bootstrapper), nameof(_myPythonicFunction)));
        //     Calli(new StandAloneMethodSig(
        //         CallingConvention.Cdecl,
        //         typeof(int),
        //         typeof(string)));
        //     return Return<int>();
        // }

        public static void OnUnload()
        {
            Console.WriteLine(".NET CLR is unloading!");
        }
    }
}