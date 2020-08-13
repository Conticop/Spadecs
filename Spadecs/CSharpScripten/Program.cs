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
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Linq.Expressions;
using System.Net;
using System.Net.Http;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Threading;
using System.Xml;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Scripting;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;
using Microsoft.CodeAnalysis.Scripting;
using Microsoft.CodeAnalysis.Text;
using Spadecs;

internal static class Program
{
    private static async Task Main()
    {
        foreach (var fileName in Directory.EnumerateFiles(AppContext.BaseDirectory, "*.csx", SearchOption.TopDirectoryOnly))
        {
            await ReloadFile(fileName);
        }
        // TODO: Swap out this shitbug FSW API.
        var fileSystemWatcher = new FileSystemWatcher(AppContext.BaseDirectory, "*.csx")
        {
            IncludeSubdirectories = false,
            NotifyFilter = NotifyFilters.LastWrite,
            EnableRaisingEvents = true
        };
        fileSystemWatcher.Changed += OnScriptFileChanged;
        await Task.Delay(Timeout.Infinite);
    }

    private static async void OnScriptFileChanged(object sender, FileSystemEventArgs e)
    {
        await ReloadFile(e.FullPath);
    }

    private static async Task<Compilation> ReloadFile(string fileName)
    {
        Console.Out.WriteLine("Reloading script: {0}", fileName);
        CompilationCache.TryGetValue(fileName, out var compilation);
        try
        {
            return compilation = await ReloadCode(await ReadFile(fileName).ConfigureAwait(false), compilation, fileName);
        }
        finally
        {
            if (compilation != null)
            {
                CompilationCache[fileName] = compilation;
            }
        }
    }

    private static async Task<string> ReadFile(string fileName)
    {
        try
        {
            await using var fs = new FileStream(fileName, FileMode.Open, FileAccess.Read, FileShare.Read);
            using var sr = new StreamReader(fs, Encoding.UTF8);
            return await sr.ReadToEndAsync().ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    private static async Task<Compilation> ReloadCode(string code, Compilation compilation = null, string name = null)
    {
        if (String.IsNullOrEmpty(code)) return null;
        return await Execute(code, compilation, name).ConfigureAwait(false);
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    private static async Task<Compilation> Execute(string code, Compilation previous = null, string name = null)
    {
        //var syntaxTree = CSharpSyntaxTree.ParseText(SourceText.From(code), CSharpParseOptions.Default.WithKind(SourceCodeKind.Regular).WithLanguageVersion(LanguageVersion.Preview));
        var eval = CSharpScript.Create<(IProtocol, IConnection)>(code, Options.WithFilePath(name));
        var compilation = eval.GetCompilation();
        if (previous != null)
        {
            compilation = compilation.WithScriptCompilationInfo(compilation.ScriptCompilationInfo.WithPreviousScriptCompilation(previous));
        }

        var compileResult = compilation.GetDiagnostics();
        var compileErrors = compileResult.Where(d => d.IsWarningAsError || d.Severity == DiagnosticSeverity.Error).ToImmutableArray();
        if (compileErrors.Length > 0)
        {
            var ex = new CompilationErrorException(String.Join(Environment.NewLine, compileErrors.Select(a => a.GetMessage())), compileErrors);
            Console.Error.WriteLine(ex);
            //throw ex;
            return null;
        }

        using (var ms = new MemoryStream())
        {
            var emit = compilation.Emit(ms);
            if (!emit.Success)
            {
                var emitResult = emit.Diagnostics;
                var emitErrors = emitResult.Where(d => d.IsWarningAsError || d.Severity == DiagnosticSeverity.Error).ToImmutableArray();
                var ex = new CompilationErrorException(String.Join(Environment.NewLine, emitErrors.Select(d => d.GetMessage())), emitErrors);
                Console.Error.WriteLine(ex);
                //throw ex;
                return null;
            }

            ms.Seek(0, SeekOrigin.Begin);
            //var binary = ms.ToArray();
            //var assemblyLoadContext = new AssemblyLoadContext(null, isCollectible: true);
            //var assembly = assemblyLoadContext.LoadFromStream(ms);
            ScriptState<(IProtocol protocol, IConnection connection)> result;
            try
            {
                result = await eval.RunAsync(null, ex => true).ConfigureAwait(false);
                if (result.Exception != null)
                {
                    Console.Error.WriteLine(result.Exception);
                    //throw result.Exception;
                    return null;
                }
                var conn = result.ReturnValue.connection;
                if (conn != null)
                {
                    var ret = conn.OnPrePlayerConnect(IPAddress.Loopback);
                    var b = ret.GetValueOrDefault(true); // Simulation... Server is going to let the player enter (by default), using true therefore
                    conn.OnPostPlayerConnect(ref b, IPAddress.Loopback, (byte)(Environment.TickCount % 0x20));
                }
                return compilation;
            }
            catch (CompilationErrorException ex)
            {
                Console.Error.WriteLine(ex);
                //throw;
                return null;
            }

            //assemblyLoadContext.Unload();
        }

        //GC.Collect();
        //GC.WaitForPendingFinalizers();
        //GC.Collect();
    }

    private static readonly ScriptOptions Options;
    private static readonly Dictionary<string, Compilation> CompilationCache;

    static Program()
    {
        CompilationCache = new Dictionary<string, Compilation>();
        var thisLocation = Assembly.GetExecutingAssembly().Location;
        var locs = new HashSet<string>();
        Options = ScriptOptions.Default
                .WithLanguageVersion(LanguageVersion.Preview)
                .WithReferences(
                    new[]
                    {
                        typeof(string).GetTypeInfo().Assembly,
                        typeof(Console).GetTypeInfo().Assembly,
                        typeof(Color).GetTypeInfo().Assembly,
                        typeof(AesManaged).GetTypeInfo().Assembly,
                        typeof(File).GetTypeInfo().Assembly,
                        typeof(Enumerable).GetTypeInfo().Assembly,
                        typeof(HttpClient).GetTypeInfo().Assembly,
                        typeof(Regex).GetTypeInfo().Assembly,
                        typeof(Expression).GetTypeInfo().Assembly,
                        typeof(ConcurrentBag<>).GetTypeInfo().Assembly,
                        typeof(ImmutableHashSet).GetTypeInfo().Assembly,
                        typeof(Unsafe).GetTypeInfo().Assembly,
                        typeof(JsonSerializer).GetTypeInfo().Assembly,
                        typeof(IConnection).GetTypeInfo().Assembly
                    }.Concat(
                        from a in AppDomain.CurrentDomain.GetAssemblies()
                        let location = a.Location
                        where !a.IsDynamic && !String.IsNullOrEmpty(location) && location != thisLocation && File.Exists(location) && locs.Add(location)
                        select a
                    )
                )
                .WithImports(
                    "System",
                    "System.Collections",
                    "System.Collections.Concurrent",
                    "System.Collections.Generic",
                    "System.Collections.Immutable",
                    "System.Diagnostics",
                    "System.Drawing",
                    //"System.Dynamic",
                    "System.Globalization",
                    "System.IO",
                    "System.Linq",
                    "System.Linq.Expressions",
                    "System.Net",
                    "System.Net.Http",
                    "System.Numerics",
                    "System.Reflection",
                    "System.Reflection.Emit",
                    "System.Runtime.CompilerServices",
                    "System.Runtime.InteropServices",
                    "System.Runtime.Intrinsics",
                    "System.Runtime.Intrinsics.X86",
                    "System.Security.Cryptography",
                    "System.Text",
                    "System.Text.Json",
                    "System.Text.RegularExpressions",
                    "System.Threading",
                    "System.Threading.Tasks",
                    "Spadecs"
                )
                .WithOptimizationLevel(OptimizationLevel.Release)
                .WithEmitDebugInformation(false)
                .WithAllowUnsafe(true)
                .WithCheckOverflow(false)
                .WithSourceResolver(ScriptSourceResolver.Default.WithBaseDirectory(AppContext.BaseDirectory))
                .WithMetadataResolver(ScriptMetadataResolver.Default.WithBaseDirectory(AppContext.BaseDirectory))
            ;
    }
}