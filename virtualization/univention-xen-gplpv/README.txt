Die gplpv Quellen werden mit einem mercurial Client runtergeladen und
kommen mit ins svn, falls die Pakete aus einer neuen Version der Quellen
gebaut werden müssen, müssen auch die Quellen im svn aktualisiert
werden.

-> hg clone -r 0.11.0.369 http://xenbits.xensource.com/ext/win-pvdrivers
-> rm -rf win-pvdrivers/.hg
