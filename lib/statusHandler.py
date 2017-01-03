# -*- coding: utf8 -*-
import config as cfg
from datetime import *

#****************************************************************************************
# Class storing various informational status
#****************************************************************************************
class StatusHandler:
	""" This class stores various information about agents, tasks, assemblies etc,
		as well as functions to handle them
	"""
	#------------------------------------------------------------------------------------
	def __init__(self, masterKey):
		self.agentList = {}
		self.pendingTaskList = []
		self.publishedStageList = {}
		self.publishedModuleList = {}
		self.masterKey = masterKey
		self.pollingPeriod = cfg.defaultPollingPeriod

	#------------------------------------------------------------------------------------
	def createTask(self, agentID, cmd, args = []):
		taskID = self.agentList[agentID]['lastTaskID'] + 1
		task = {
			'agentID': agentID,
			'id': taskID,
			'fileName': agentID + "." + str(taskID),
			'cmd': cmd,
			'args': args
		}
		return task

	#------------------------------------------------------------------------------------
	def commitTask(self, task):
		self.pendingTaskList.append(task)
		self.agentList[task['agentID']]['lastTaskID'] =  task['id']
		self.agentList[task['agentID']]['pendingTaskID'] =  task['id']

	#------------------------------------------------------------------------------------
	def removeTask(self, task):
		self.agentList[task['agentID']]['pendingTaskID'] = 0
		self.pendingTaskList.remove(task)

	#------------------------------------------------------------------------------------
	def createAgent(self, agentID, agentLastBeacon, agentStatusFile):
		self.agentList[agentID] = {}
		self.agentList[agentID]['status'] = "UNKNOWN"
		self.agentList[agentID]['lastBeacon'] = agentLastBeacon
		self.agentList[agentID]['statusFile'] = agentStatusFile
		self.agentList[agentID]['commandFile'] = agentStatusFile[0:-7] + ".cmd"
		self.agentList[agentID]['wakeUpTime'] = "N/A"
		self.agentList[agentID]['lastTaskID'] = 0
		self.agentList[agentID]['pendingTaskID'] = 0

	#------------------------------------------------------------------------------------
	def agentIsKnown(self, agentID):
		return (agentID in self.agentList)

	#------------------------------------------------------------------------------------
	def agentIsAlive(self, agentID):
		return (self.agentList[agentID]['status'] == "ALIVE")

	#------------------------------------------------------------------------------------
	def agentIsSleeping(self, agentID):
		return (self.agentList[agentID]['status'] == "SLEEPING") 

	#------------------------------------------------------------------------------------
	def agentIsNew(self, agentID):
		return (self.agentList[agentID]['status'] == "UNKNOWN") 

	#------------------------------------------------------------------------------------
	def agentIsDead(self, agentID):
		return (self.agentList[agentID]['status'] == "DEAD")

	#------------------------------------------------------------------------------------
	def getAgentAttribute(self, agentID, attribute):
		return self.agentList[agentID][attribute]

	#------------------------------------------------------------------------------------
	def getAgentWakeUpTimeUTC(self, agentID):
		return datetime.strptime(self.agentList[agentID]['wakeUpTime'], "%Y-%m-%dT%H:%M:%SZ")

	#------------------------------------------------------------------------------------
	def setAgentAttribute(self, agentID, attribute, value):
		self.agentList[agentID][attribute] = value
		return

	#------------------------------------------------------------------------------------
	def agentCanBeTasked(self, agentID):
		return (self.agentList[agentID]['pendingTaskID'] == 0) and self.agentList[agentID]['status'] != "DEAD"

	#------------------------------------------------------------------------------------
	def addStage(self, stageName, stageLink):
		self.publishedStageList[stageName] = stageLink

	#------------------------------------------------------------------------------------
	def removeStage(self, stageName):
		del self.publishedStageList[stageName]

	#------------------------------------------------------------------------------------
	def isValidStage(self, stageName):
		return (stageName in self.publishedStageList and self.publishedStageList[stageName] != "NONE")
		
	#------------------------------------------------------------------------------------
	def addModule(self, moduleName, moduleLink):
		self.publishedModuleList[moduleName] = moduleLink

	#------------------------------------------------------------------------------------
	def removeModule(self, moduleName):
		del self.publishedModuleList[moduleName]

	#------------------------------------------------------------------------------------
	def isValidModule(self, moduleName):
		return (moduleName in self.publishedModuleList and self.publishedModuleList[moduleName] != "NONE")
