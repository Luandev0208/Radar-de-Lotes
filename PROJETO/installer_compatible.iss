#include "build_version.iss"

[Setup]
AppId={{669D506A-855C-49B4-AE51-57A7F798270B}
AppName=Radar de Lotes
AppVersion={#AppVersion}
DefaultDirName={autopf}\Radar de Lotes
DefaultGroupName=Radar de Lotes
OutputBaseFilename=Setup
UseSetupLdr=no
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
OutputDir=installer_compatible_output
CloseApplications=yes
RestartApplications=no
Uninstallable=yes

[Files]
Source: "dist\Radar de Lotes.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_tasks.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "uninstall_tasks.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Radar de Lotes"; Filename: "{app}\Radar de Lotes.exe"
Name: "{autodesktop}\Radar de Lotes"; Filename: "{app}\Radar de Lotes.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: checkedonce

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install_tasks.ps1"" -Executable ""{app}\Radar de Lotes.exe"""; Flags: runhidden waituntilterminated
Filename: "{app}\Radar de Lotes.exe"; Parameters: "--updated"; Flags: nowait

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\uninstall_tasks.ps1"""; Flags: runhidden waituntilterminated; RunOnceId: "RemoveRadarTasks"
