UCS 5 Layout
============

The [old UCS 4 layout](layout4.md) is still used for **components**, but the main release uses the `pool/` and `dists/` layout:

Assumptions
-----------
* each minor / patch-level release is self-coontained and references files from the shared `pool/`
* the errata suite associated with each release gets incremental updates and is merged into the next release

Layout
------

	##### Paths in Packages file are relative to here #####
	dists/
		ucs500/
		errata500/
			main/
				binary-amd64/
				debian-installer/binary-amd64/
					Packages
					Packages.xz
					Release  # required for PXE
					by-hash/
						MD5Sum/
						SHA256/
				source/
					Sources
					Sources.xz
					Release  # required for PXE
					by-hash/
						MD5Sum/
						SHA256/
			InRelease
			Release
			Release.gpg
			preup.sh
			preup.sh.gpg
			post.sh
			post.sh.gpg
	pool/
		main/
			?/
			lib?/
				*/
					*_all.deb
					*_amd64.deb
					*.dsc
					*.tar.*z*
					*.diff.*z*
