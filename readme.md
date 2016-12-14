DBC2
============

Author: Arno0x0x - [@Arno0x0x](http://twitter.com/Arno0x0x)

DBC2 (DropboxC2) is a modular post-exploitation tool, composed of an agent, a controler, running on any machine, and some modules.

This project was initially inspired by the fantastic Empire framework, but also as an objective to learn Python.

Check out this introduction and demo :
[![Demo](https://dl.dropboxusercontent.com/s/6f5713880ocz1st/dbc2.jpg?dl=0)](https://vimeo.com/195596062)

The app is distributed under the terms of the [GPLv3 licence](http://www.gnu.org/copyleft/gpl.html).

Dependencies & requirements
----------------

DBC2 requires a Dropbox application (*"App folder" only is sufficient*) to be created within your Dropbox account and an access token generated for this application, in order to be able to perform API calls.

On the controller side, DBC2 requires:
* Python 2.7 (not tested with Python 3)
* The following libraries, that can be installed using `pip install -r requirements.txt`:
  - requests
  - tabulate
  - pyscrypt
  - pycrypto

DBC2 controller has been successfully tested and used on Linux Kali and Mac OSX.

On the agent side, DBC2 requires:
* .Net framework > 4 (tested sucessfully on Windows 7 and Windows 10)


Security Aspects
-----------

DBC2 controller requires a master password to be given when it starts. This password is then derived into a 128 bits master key by the use of the PBKDF function from the pyscrypt library. The master key is then base64 encoded and can (*optionnal*) be saved in the config file.

DBC2 performs end-to-end encryption of data using the master key with AES-128/CBC mode. Data exchanged between the agent and the controller flows through the Dropbox servers so while the transfer itself is encrypted, thanks to HTTPS, it had to be end-to-end encrypted to protect the data while at rest on the Dropbox servers.

DBC2 also performs obfuscation of the stages and the modules by the use of some XOR encryption, which is dumb encryption but is enough to simply obfuscate some well known and publically available piece of codes. The key used to perform XOR encryption is a SHA256 hash of the master key.


Installation & Configuration
------------

Installation is pretty straight forward:
* Git clone this repository and jump into the DBC2 folder
* Install requirements using `pip install -r requirements.txt`
* Give the execution rights to the main script: `chmod +x dropboxC2.py`

To start the controller, simply type `./dropboxC2.py`.

Configuration is done through the `config.py` file:
* Specify your Dropbox API access token

TODO
------------

This is version alpha of this tool, and my first project developped with Python. So it is probably full of bugs, not written in the most *Pythonic* way. Bugs fixes and improvements will come over time as I'll be getting feedback on this tool.

What needs to be added:
- During file transfer (sendFile and getFile commands) handle file name with a space
- Ability to task an agent with more than one task at a time
- Provide more stager types
- Fix missing encryption on the "sendFile" function (*due to me being lazy: on the agent side I wanted to leverage the WebClient->DownloadFile function and I'm not sure how to put my decryption routine in the middle of the flow without having to rewrite this function by hand*). This is the only data that is not encrypted. Anything flowing from the agent back to the controller through the Dropbox servers is properly encrypted.