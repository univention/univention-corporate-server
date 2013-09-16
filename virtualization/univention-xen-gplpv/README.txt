Die gplpv Quellen werden mit einem mercurial Client runtergeladen und
kommen mit ins svn, falls die Pakete aus einer neuen Version der Quellen
gebaut werden müssen, müssen auch die Quellen im svn aktualisiert
werden.

	make -f debian/rules get-orig-source
	make -C certs CA=VeriSign install
	$EDITOR win-pvdrivers/sign_config.bat
