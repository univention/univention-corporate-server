@ECHO OFF

SET SEVENZIP="%PROGRAMFILES%\7-Zip\7z.exe"
IF NOT EXIST %SEVENZIP% GOTO :end

IF %_BUILDARCH%==x86 (SET BUILDDIR=obj%BUILD_ALT_DIR%\i386) ELSE (SET BUILDDIR=obj%BUILD_ALT_DIR%\amd64)

SET SYMFILES=xenpci\%BUILDDIR%\xen*.sys xenpci\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xennet\%BUILDDIR%\xen*.sys xennet\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xenvbd_scsiport\%BUILDDIR%\xenvbd_scsiport*.sys xenvbd_scsiport\%BUILDDIR%\xen*.pdb
SET SYMFILES=%SYMFILES% xenvbd_filter\%BUILDDIR%\xenvbd_filter*.sys xenvbd_filter\%BUILDDIR%\xen*.pdb

IF %DDK_TARGET_OS%==Win2K GOTO symfiles_done

SET SYMFILES=%SYMFILES% xenusb\%BUILDDIR%\xen*.sys xenusb\%BUILDDIR%\xen*.pdb

IF %DDK_TARGET_OS%==WinXP GOTO symfiles_done

SET SYMFILES=%SYMFILES% xenvbd_storport\%BUILDDIR%\xen*.sys xenvbd_storport\%BUILDDIR%\xen*.pdb


:symfiles_done

%SEVENZIP% a -y symbols_%BUILD_ALT_DIR%_%GPLPV_VERSION%.zip %SYMFILES%

:end