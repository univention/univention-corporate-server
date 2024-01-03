Radius now has TLS 1.3 enabled by default.
TLS 1.3 might cause issues with Microsoft Windows 10.
To use TLS 1.2, set the |UCSUCRV| :envvar:`freeradius/conf/tls-max-version` to the value ``1.2``.
