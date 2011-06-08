@echo off
@rem ***
@rem *** This batch file makes it easier to test MAKECAB.EXE in isolation (perhaps for testing the performance impact of ".DDF" changes)
@rem *** It needs to be run from the ".MM" directory!
@rem ***
@rem *** MAKECAB CMD  : "MakeCab.exe" /f "out\installscript.mm\Log\MakeCab\#02\setup.ddf" /v1
@rem *** MAKEMSI Runs : cmd.exe /c ""MakeCab.exe" /f "out\installscript.mm\Log\MakeCab\#02\setup.ddf" /v1 2>&1 | Reg4mm.exe Tee4MM.4mm  'out\installscript.mm\Log\MakeCab\#02\setup.txt' "!Throughput:""
@rem *** Runs From    : Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector
@rem ***

setlocal
cd Z:\11_wrk\svn\dev\trunk\ucs\services\univention-ad-connector\windows\ucs-ad-connector\msi-package\UCS AD Connector
"MakeCab.exe" /f "out\installscript.mm\Log\MakeCab\#02\setup.ddf" /v1
pause
