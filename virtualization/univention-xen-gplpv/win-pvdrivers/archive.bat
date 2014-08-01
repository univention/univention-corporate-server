@ECHO OFF

SET SEVENZIP="%PROGRAMFILES%\7-Zip\7z.exe"
IF NOT EXIST %SEVENZIP% GOTO :end

IF %_BUILDARCH%==x86 (SET BUILDDIR=obj%BUILD_ALT_DIR%\i386) ELSE (SET BUILDDIR=obj%BUILD_ALT_DIR%\amd64)

SET SYMFILES=xenpci\%BUILDDIR%\xen*.sys xenpci\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xennet\%BUILDDIR%\xen*.sys xennet\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xenvbd\%BUILDDIR%\xen*.sys xenvbd\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xenscsi\%BUILDDIR%\xen*.sys xenscsi\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xenusb\%BUILDDIR%\xen*.sys xenusb\%BUILDDIR%\xen*.pdb

%SEVENZIP% a -y symbols_%BUILD_ALT_DIR%_%GPLPV_VERSION%.zip %SYMFILES%

:end