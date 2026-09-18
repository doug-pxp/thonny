#define AppUserModelID "ProgrammingXP.Softsembly"
#define SoftsemblyPyProgID "Softsembly.py"

[Setup]
AppId=ProgrammingXP.Softsembly
AppName=Softsembly
AppVersion={#AppVer}
AppVerName=Softsembly {#AppVer}
AppComments=Softsembly is a batteries-included Python IDE by ProgrammingXP
AppPublisher=ProgrammingXP
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog
MinVersion=10.0
ArchitecturesAllowed=x64compatible arm64
ArchitecturesInstallIn64BitMode=x64compatible arm64
DisableWelcomePage=no
DisableProgramGroupPage=auto
DefaultGroupName=Softsembly
DefaultDirName={autopf}\Softsembly
DisableDirPage=auto
DirExistsWarning=auto
UsePreviousAppDir=yes
DisableReadyPage=no
AlwaysShowDirOnReadyPage=yes
OutputDir=dist
OutputBaseFilename=Softsembly-Setup-{#AppVer}-x64
Compression=lzma2/ultra
SolidCompression=yes
LicenseFile=license-for-win-installer.txt
WizardImageFile=softsembly_wizard.bmp
WizardSmallImageFile=softsembly_small.bmp
SetupIconFile=softsembly.ico
UninstallDisplayIcon={app}\softsembly.exe
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "CreateDesktopIcon"; Description: "Create a desktop icon"; Flags: unchecked
Name: "AssociatePy"; Description: "Open Python files with Softsembly"; Flags: unchecked

[Files]
Source: "{#SourceFolder}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Softsembly"; Filename: "{app}\softsembly.exe"; IconFilename: "{app}\softsembly.exe"
Name: "{autodesktop}\Softsembly"; Filename: "{app}\softsembly.exe"; IconFilename: "{app}\softsembly.exe"; Tasks: CreateDesktopIcon

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\softsembly.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\softsembly.exe"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\softsembly.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "Softsembly"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\softsembly.exe"; ValueType: string; ValueName: "AppUserModelID"; ValueData: "{#AppUserModelID}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\softsembly.exe\SupportedTypes"; ValueType: string; ValueName: ".py"; ValueData: ""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\softsembly.exe\SupportedTypes"; ValueType: string; ValueName: ".pyw"; ValueData: ""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\softsembly.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\softsembly.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#SoftsemblyPyProgID}"; ValueType: string; ValueName: ""; ValueData: "Python File"; Flags: uninsdeletekey; Tasks: AssociatePy
Root: HKA; Subkey: "Software\Classes\{#SoftsemblyPyProgID}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\softsembly.exe,0"; Flags: uninsdeletekey; Tasks: AssociatePy
Root: HKA; Subkey: "Software\Classes\{#SoftsemblyPyProgID}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\softsembly.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: AssociatePy
Root: HKA; Subkey: "Software\Classes\.py\OpenWithProgids"; ValueType: string; ValueName: "{#SoftsemblyPyProgID}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: AssociatePy

[Run]
Filename: "{app}\softsembly.exe"; Description: "Launch Softsembly"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel1.Caption := 'Welcome to Softsembly!';
  WizardForm.WelcomeLabel2.Caption := 'This installs Softsembly and its private Python runtime. No separate Python setup is required.';
  WizardForm.LicenseAcceptedRadio.Checked := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    WizardForm.FinishedLabel.Caption := 'Softsembly is installed and ready to code.';
  end;
end;
