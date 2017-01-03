@echo off
start /b ${oneliner}
(goto) 2>nul & del "%~f0"