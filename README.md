# Spadecs
[![Build Status](https://github.com/Conticop/Spadecs/workflows/CI/badge.svg?branch=master)](https://github.com/Conticop/Spadecs/commits/master)  
An attempt to bring .NET scripting into classic "Ace of Spades" (0.x) servers ❤️  
The goal is to be able to use C# (or any .NET language) for scripting server-side.  

### Why?
Because we can... (and because I'm noobmen at Python 😆)  
But, mainly because I want to learn some Python. Oh, and by the way I also want to make hot-reloading possible.  
Hot-reloading means as you make changes to the server-code while it is running, you would see those changes applied immediately on the server. Wouldn't that be cool? 😎  
I will try my best to support all server implementations, and do it cross-platform and architecture independent.  
Current targets:  
- PySpades (Python 2) on Windows/Linux/Mac | x86, x64
- PySnip (Python 2) on Windows/Linux/Mac | x86, x64
- piqueserver (Python 3) on Windows/Linux/Mac | x86, x64

## Installing
**If you want to manually build Spadecs from source:**
<details>
  <summary>I can do it myself!</summary>

  ### Building
  1. Install .NET Core SDK (2.1 or higher), [using latest available is highly recommended](https://dotnet.microsoft.com/download/dotnet-core).
  2. [Download](https://github.com/Conticop/Spadecs/archive/master.zip) **or** Clone the repository (using `git clone https://github.com/Conticop/Spadecs`).
     * If you choose to download via zip: After downloading, extract the zip archive to preferable location, and open a command prompt (Terminal) inside the folder.
     * If you choose to clone: After cloning, open the folder (`cd Spadecs`).
  3. Run `dotnet build Spadecs`.

  If there are no errors, the output binaries shall be located in a new [`dotnet` folder under scripts](/scripts).  
  If you made it this far, you are ready to proceed to [Running section](#running).
</details>

**If you want to get started as soon as possible:**
<details>
  <summary>Let's go fast!</summary>

  ### Steps
  1. [Download the latest precompiled release](https://github.com/Conticop/Spadecs/releases/latest) for your system.

  Jump to [Running section](#running).
</details>

## Running
1. If you have build Spadecs from source, skip this step. Otherwise, [download and install .NET Core Runtime](https://dotnet.microsoft.com/download/dotnet-core/current/runtime).
2. Copy all contents of the `scripts` folder (`dotnet.py` file + `dotnet` folder) into your server scripts folder.
3. Modify your server configuration file to include and run `dotnet` script, it is recommended to place it first before any other scripts.
4. Launch your server.
5. ???
6. Profit.

## Troubleshooting & Notes
- You only need .NET Core Runtime unless you intent to build Spadecs from source.  
    * [.NET Core SDK is only required if you are going to build Spadecs from source](https://dotnet.microsoft.com/download).  

- Are you getting `%1 is not valid Win32 program` error upon server launch?  
    * This is a known problem when you are running 32-bit server instance on 64-bit Windows.  
    * Make sure you install 32-bit (x86) .NET Core SDK/Runtime. And also assign `DOTNETHOME_X86` (system) environment variable to point at installation folder (by default, `C:\Program Files (x86)\dotnet`):  
    ![image](https://user-images.githubusercontent.com/58798963/74741057-6dc02800-525c-11ea-9af3-b85bd5daa4ec.png)

## License
*Spadecs* is licensed under the terms of the MIT license.  
See [LICENSE](/LICENSE) file for more information.
