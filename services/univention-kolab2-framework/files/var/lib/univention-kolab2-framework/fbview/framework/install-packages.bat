@echo off
:: ----------------------------------------------------------------------
:: Copyright (c) 2003 Peter Magnusson (kmpm@telia.com)
:: ----------------------------------------------------------------------
::  Author: Peter Magnusson (kmpm@telia.com)
:: ----------------------------------------------------------------------
::
:: You must have PHP PEAR installed to successfully use this script.
:: Please check that you have the environment variables
:: PHP_PEAR_BIN_DIR and PHP_PEAR_PHP_BIN set to the correct paths.
:: 

:: Uncomment and modify the lines below to match your PHP installation
:: Check environment variables
:: if "%PHP_CLI_BIN%"=="" set PHP_PEAR_PHP_BIN=C:\php\cli\php.exe
:: if "%PHP_PEAR_BIN_DIR%"=="" set PHP_PEAR_BIN_DIR=C:\PHP
 
:: Check that the files and folders exist
if not exist "%PHP_PEAR_BIN_DIR%" GOTO DIR_ERROR
if not exist "%PHP_PEAR_PHP_BIN%" GOTO BIN_ERROR

:: launch Horde install-packages.php
goto INSTALL

:DIR_ERROR
	echo PHP_PEAR_BIN_DIR is not set correctly.
	echo The current value is:%PHP_PEAR_BIN_DIR%
	goto END

:BIN_ERROR
	echo PHP_PEAR_PHP_BIN is not set correctly.
	echo The current value is:%PHP_PEAR_PHP_BIN%
	goto END

:INSTALL
	::Save the current path so that we can modify it and restore it later
	set OLD_PATH=%PATH%
	::Set the new path with PHP_PEAR_BIN_DIR included
	set PATH=%PATH%;%PHP_PEAR_BIN_DIR%
	"%PHP_PEAR_PHP_BIN%" -C -d output_buffering=1 -d include_path="%PHP_PEAR_BIN_DIR%" -f "install-packages.php"
	::Restore the path to the previous 
	set PATH=%OLD_PATH%
:END
	::Pause to display information
	pause
