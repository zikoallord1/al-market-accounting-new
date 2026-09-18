#define MyAppName "نظام الماركت المحاسبي"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "المهندس زكريا الحاج"
#define MyAppExeName "نظام الماركت المحاسبي.exe"

[Setup]
AppId={{A8D7B6A4-1E3F-4E7A-9D12-6D2D7B8A4A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "dist\نظام الماركت المحاسبي.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل نظام الماركت المحاسبي"; Flags: nowait postinstall skipifsilent
