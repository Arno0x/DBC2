dbc2Loader
============
**dbc2Loader** is a small .Net assembly that acts as a lightweight and simple wrapper for the DBC2 agent, performing the following tasks:
  1. Download the DBC2 agent assembly from a remote URL (*normally a dropbox URL of the published stage obtained from the DBC2 controller*)
  2. Decrypt the DBC2 agent assembly in memory
  3. Load the DBC2 agent assembly in memory
  4. Instantiate the DBC2 agent

It is currently useful for two things:

  1/  It can be loaded through DotNetToJScript, which gives us a new JScript loader for the DBC2 agent: javascript2 stager which already contains the dbc2Loader.dll serialized object (*so you don't have to compile it on your own*).

  2/  Can be loaded through the use of a native wrapper DLL hosting the .Net CLR (*also provided in the ./nativeWrapper directory*), then this native wrapper DLL can be transformed into a position independant shellcode thanks to sRDI. This allows for injecting the DBC2 agent in virtually any process !! Be sure to check instructions in the nativeWrapper CPP file header on how to compile, transform with sRDI and use it !