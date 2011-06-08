cl ucs-ad-connector.cpp /Ic:\openssl\include /link wsock32.lib wldap32.lib advapi32.lib crypt32.lib ssleay32.lib libeay32.lib user32.lib shlwapi.lib
copy ucs-ad-connector.exe msi-package\
rem cl ucs-ad-connector.cpp /link wsock32.lib wldap32.lib advapi32.lib secur32.lib crypt32.lib

