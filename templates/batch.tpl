@echo off
start /b ${poshCmd}
(goto) 2>nul & del "%~f0"