; Inno Setup : fabrique PedaFiche-Installation-x.y.z.exe à partir de dist\PedaFiche
; Compiler depuis la racine du projet :  iscc /DVersion=2.4.0 packaging\windows\pedafiche.iss
#ifndef Version
  #define Version "2.4.0"
#endif
[Setup]
AppId={{5C1E8B34-7A2D-4F69-9E0B-3D6A1C4F8E27}
AppName=pédafiche
AppVersion={#Version}
AppPublisher=Maître Aimé FACHOLA
DefaultDirName={autopf}\PedaFiche
DefaultGroupName=pédafiche
OutputDir=..\..\dist
OutputBaseFilename=PedaFiche-Installation-{#Version}
SetupIconFile=..\..\pedafiche\web\static\icons\pedafiche.ico
UninstallDisplayIcon={app}\PedaFiche.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "bureau"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "..\..\dist\PedaFiche\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\pédafiche"; Filename: "{app}\PedaFiche.exe"
Name: "{autodesktop}\pédafiche"; Filename: "{app}\PedaFiche.exe"; Tasks: bureau

[Run]
Filename: "{app}\PedaFiche.exe"; Description: "Lancer pédafiche maintenant"; Flags: nowait postinstall skipifsilent
