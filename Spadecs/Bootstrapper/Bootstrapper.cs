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
using System.Text.Json;
using System.Threading.Tasks;

namespace Spadecs
{
    using static PyBindings;
    using static PyRegistry;

    public static unsafe class Bootstrapper
    {
        static Bootstrapper()
        {
        }

        public static void OnLoad(string json)
        {
            PyFunctions = JsonSerializer.Deserialize<Dictionary<string, ulong>>(json);
            Console.WriteLine(".NET CLR is running!");

            // Call into Python function to print a given string
            var result = MyPythonicFunction("This string has warp'ed from .NET to Python land :)");
            Console.WriteLine(result == 123
                              ? "All good! We are ready to rule the world."
                              : "BUGCHECK: Integer is not matching!! Please report a bug.");

            // Setup some events (testing purposes)
            static void PrePlayerConnect(object sender, PreConnectEventArgs e)
            {
                Console.WriteLine("[dotnet] {0}({1})", nameof(PrePlayerConnect), e.Address);
                //e.AllowConnection = PyBool.False;
                Console.WriteLine("Pre return: {0}", e.AllowConnection);
                // Test trackable object
                DotNet_GetObjects();
                //Console.WriteLine("Objects: {0}", objectsJson);
                //var deserialized = JsonSerializer.Deserialize<Dictionary<string, string[]>>(objectsJson);
            }
            static void PostPlayerConnect(object sender, PostPlayerConnectEventArgs e)
            {
                Console.WriteLine("[dotnet] {0}({1}, #{2})", nameof(PostPlayerConnect), e.Address, e.ID);
                Console.WriteLine("Post return: {0}", e.AllowConnection);
                byte pid = e.ID;
                if (e.AllowConnection != PyBool.False)
                {
                    // NOTE: The player doesn't seem to be kickable while in Limbo-state.
                    Task.Run(() => TestClass.KickThePlayerAsync(pid));
                }
            }
            EventManager.PrePlayerConnect += PrePlayerConnect;
            EventManager.PostPlayerConnect += PostPlayerConnect;
        }

        public static void OnUnload()
        {
            Console.WriteLine(".NET CLR is unloading!");
        }
    }

    internal static class TestClass
    {
        internal static async Task KickThePlayerAsync(byte pid)
        {
            Console.WriteLine("[dotnet](test) Player #{0} will be kicked in 30s...", pid);
            await Task.Delay(TimeSpan.FromSeconds(30));
            unsafe { CPlayer_KickByID(pid); }
        }
    }
}