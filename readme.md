DBC2
============
LAST/CURRENT VERSION: 0.2.6

Author: Arno0x0x - [@Arno0x0x](http://twitter.com/Arno0x0x)

DBC2 (DropboxC2) is a modular post-exploitation tool, composed of an agent running on the victim's machine, a controler, running on any machine, powershell modules, and Dropbox servers as a means of communication.

This project was initially inspired by the fantastic Empire framework, but also as an objective to learn Python.
  
Check out this introduction and demo of basic functionnalities (v0.0.1) :
[![Demo](https://dl.dropboxusercontent.com/s/uj7joge12iu6dn6/dbc2_demo.jpg?dl=0)](https://vimeo.com/195596062)
  
New features in version 0.2.x :
[![Demo](https://dl.dropboxusercontent.com/s/flldt93uprg33cp/dbc2_v0.2.jpg?dl=0)](https://vimeo.com/197902404)

The app is distributed under the terms of the [GPLv3 licence](http://www.gnu.org/copyleft/gpl.html).

Architecture
----------------

![DBC2 Architecture](https://dl.dropboxusercontent.com/s/bwgtzt1x5e3zpxe/dbc2_architecture.jpg?dl=0 "DBC2 Architecture")


Features
----------------

DBC2 main features:
  - Various stager (Powershell one liner, batch file, MS-Office macro, javascript, DotNetToJScript, msbuild file, SCT file, ducky, more to come...)
  - Single CLI commands (*one at a time, no environment persistency*)
  - Pseudo-interactive shell (*environment persistency*) - based on an idea from *0xDEADBEEF00 [at] gmail.com*
  - Send file to the agent
  - Retrieve file from the agent
  - Launch processes on the agent
  - Keylogger
  - Clipboard logger (*clipboard recording/spying*)
  - Screenshot capture
  - Run and interact with PowerShell modules (*Endless capabilities: PowerSploit, Inveigh, Nishang, Empire modules, Powercat, etc.*)
  - Send key strokes to any process
  - Set persistency through scheduled task and single instance through Mutex
  - Can run within `(w|c)script.exe` thanks to the DotNetToJScript stager (*javascript2*)
  - Can be **injected into any process** thanks to the nativeWrapper and its corresponding position independant shellcode !
  
Dependencies & requirements
----------------

DBC2 requires a Dropbox application (*"App folder" only is sufficient*) to be created within your Dropbox account and an access token generated for this application, in order to be able to perform API calls. Look at the intoduction video on how to do this if you're unsure.

On the controller side, DBC2 requires:
* Python 2.7 (not tested with Python 3)
* The following libraries, that can be installed using `pip install -r requirements.txt`:
  - requests>=2.11
  - tabulate
  - pyscrypt
  - pycrypto

DBC2 controller has been successfully tested and used on Linux Kali and Mac OSX.

On the agent side, DBC2 requires:
* .Net framework >= 4.5 (tested sucessfully on Windows 7 and Windows 10)

Security Aspects
-----------

DBC2 controller asks for a master password when it starts. This password is then derived into a 128 bits master key by the use of the PBKDF function from the pyscrypt library. The master key is then base64 encoded and can (*optionnally*) be saved in the config file.

DBC2 performs end-to-end encryption of data using the master key with AES-128/CBC mode. Data exchanged between the agent and the controller flows through the Dropbox servers so while the transfer itself is encrypted, thanks to HTTPS, data has to be end-to-end encrypted to protect the data while at rest on the Dropbox servers.

DBC2 also performs obfuscation of the stages and the modules by the use of XOR encryption, which is dumb encryption but is enough to simply obfuscate some well known and publically available piece of codes. The key used to perform XOR encryption is a SHA256 hash of the master key.


Installation & Configuration
------------

Installation is pretty straight forward:
* Git clone this repository: `git clone https://github.com/Arno0x/DBC2 dbc2`
* cd into the DBC2 folder: `cd dbc2`
* Install requirements using `pip install -r requirements.txt`
* Give the execution rights to the main script: `chmod +x dropboxC2.py`

To start the controller, simply type `./dropboxC2.py`.

Configuration is done through the `config.py` file:
* You can optionnally specify your Dropbox API access token and base64 encoded master key. If you do so, the controller won't ask you for these when it starts.

DBC2 is also available as a Docker container so it's:
Check [DBC2 on Docker hub](https://hub.docker.com/r/arno0x0x/dbc2/).
Or simply do: `docker pull arno0x0x/dbc2`

Compiling your own agent stage
------------

You can very easily compile your own executables of the agent stage, from the source code provided. You don't need Visual Studio installed.

* Copy the agent/source folder on a Windows machine with the .Net framework installed
* CD into the source directory
* Use the .Net command line C# compiler:
  - To get the standard agent executable: `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:dbc2_agent.exe *.cs`
  - To get the debug version: `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /define:DEBUG /out:dbc2_agent_debug.exe *.cs`

DISCLAIMER
----------------
This tool is intended to be used in a legal and legitimate way only:
  - either on your own systems as a means of learning, of demonstrating what can be done and how, or testing your defense and detection mechanisms
  - on systems you've been officially and legitimately entitled to perform some security assessments (pentest, security audits)

Quoting Empire's authors:
*There is no way to build offensive tools useful to the legitimate infosec industry while simultaneously preventing malicious actors from abusing them.*

Author
----------------
Arno0x0x - You can contact me on my twitter page (@Arno0x0x).

TODO
------------

This is still version beta of this tool, and my first project developped with Python and C#. So it is probably full of bugs, not written in the most *Pythonic* of CSharp'ish way. Bugs fixes and improvements will come over time as I'll be getting feedback on this tool.

To be added in the next releases:
- Gather basic system information for each agent at startup
- Create some basic event at the agent side and event subscription and automatic action on controller side (*ex: "machine locked or screensaver started" would allow for some activity that is visible like sending keystrokes to some processes, or "a given process or connection has been established")
- Add option for the stage to auto persist at first startup
- Possibility to task an agent with more than one task at a time

To be fixed:
- Fix missing encryption on the "sendFile" function (*due to me being lazy: on the agent side I wanted to leverage the WebClient->DownloadFile function and I'm not sure how to put my decryption routine in the middle of the flow without having to rewrite this function by hand*). This is the only data that is not encrypted. Anything flowing from the agent back to the controller through the Dropbox servers is properly encrypted.