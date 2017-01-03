function Say ([string] $sentence)
{
	(New-Object -com SAPI.SpVoice).Speak($sentence) | Out-Null
}