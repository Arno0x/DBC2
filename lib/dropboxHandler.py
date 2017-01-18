# -*- coding: utf8 -*-
import requests
from lib import helpers

#****************************************************************************************
# Class handling raw HTTP communications with the Dropbox server
#****************************************************************************************
class DropboxHandler:
	""" This class provides wrapping methods for raw HTTP communications with the Dropbox server
	"""
	
	#-----------------------------------------------------------
	def __init__(self, token):
		self.token = token
		self.authorization = "Bearer " + token
		self.dropboxAPI = {
			'listFolder': 'https://api.dropboxapi.com/2/files/list_folder',
			'uploadFile': 'https://content.dropboxapi.com/2/files/upload',
			'downloadFile': 'https://content.dropboxapi.com/2/files/download',
			'deleteFile': 'https://api.dropboxapi.com/2/files/delete',
			'getMetaData': 'https://api.dropboxapi.com/2/files/get_metadata',
			'shareFile': 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings',
			'getSharedLink': 'https://api.dropboxapi.com/2/sharing/list_shared_links'
		}
	
	#-----------------------------------------------------------
	def sendRequest(self, url, headers, data = None, resultFormat = "text"):
		try:
			headers['Authorization'] = self.authorization
			
			# Perform the request
			r = requests.post(url,headers=headers,data=data)
			
			if r.status_code != requests.codes.ok:
				print helpers.color("[!]Wrong HTTP status code received")
				print helpers.color(r.text,"red")	
				return None
			
			if resultFormat == "text":
				return r.text
			elif resultFormat == "json":
				return r.json()
			else:
				return r.content
		except requests.RequestException as e:
			print helpers.color("[!]Error communicating with the Dropbox server")
			print helpers.color(e,"red")
			return None
		except ValueError as e:
			print helpers.color("[!]Error decoding JSON response")
			print helpers.color(e,"red")
			return None
	
	#-----------------------------------------------------------
	def deleteFile(self, path):
		# Set required headers
		headers = {
			'Content-Type': 'application/json'				
		}
		
		data = '{"path": "' + path + '"}'
		
		return self.sendRequest(self.dropboxAPI['deleteFile'], headers, data)
	
	#-----------------------------------------------------------
	def listFolder(self, path, resultFormat = "json"):
		# Set required headers
		headers = {
			'Content-Type': 'application/json'				
		}
		
		data = "{\"path\": \"" + path +"\",\"recursive\": false,\"include_media_info\": false,\"include_deleted\": false,\"include_has_explicit_shared_members\": false}"
			
		return self.sendRequest(self.dropboxAPI['listFolder'], headers, data, resultFormat=resultFormat)
	
	#-----------------------------------------------------------
	def readFile(self, path, resultFormat = "text"):
		# Set required headers
		headers = {
			'Dropbox-API-Arg': '{"path": "' + path + '"}'
		}
		
		return self.sendRequest(self.dropboxAPI['downloadFile'], headers, resultFormat=resultFormat)
	
	#-----------------------------------------------------------
	def putFile(self, path, data):
		# Set required headers
		headers = {
			'Content-Type': 'application/octet-stream',
			'Dropbox-API-Arg': '{"path": "' + path + '","mode": "overwrite","autorename": false,"mute": true}'
		}

		return self.sendRequest(self.dropboxAPI['uploadFile'], headers, data)
		
	#-----------------------------------------------------------
	def getMetaData(self, path):
		# Set required headers
		headers = {
			'Content-Type': 'application/json'
		}
		
		# Prepare request body
		data = '{"path": "' + path + '","include_media_info": false,"include_deleted": false,"include_has_explicit_shared_members": false}'
		
		return self.sendRequest(self.dropboxAPI['getMetaData'], headers, data)

	#-----------------------------------------------------------
	def shareFile(self, path):
		# Set required headers
		headers = {
			'Content-Type': 'application/json'
		}
		
		# Prepare request body
		data = '{"path": "' + path + '", "settings": { "requested_visibility": "public"}}'
		
		return self.sendRequest(self.dropboxAPI['shareFile'], headers, data, resultFormat = "json")

	#-----------------------------------------------------------
	def getSharedLink(self, path):
		# Set required headers
		headers = {
			'Content-Type': 'application/json'
		}
		
		# Prepare request body
		data = '{"path": "' + path + '"}'
		
		return self.sendRequest(self.dropboxAPI['getSharedLink'], headers, data, resultFormat = "json")
