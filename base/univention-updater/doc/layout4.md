UCS 2-4 Layout
==============

[UCS 5](layout5.md) uses a new layout.

* [SDB 91](https://docs.software-univention.de/manual-5.0.html#computers::softwaremanagement::installsoftware)
* [SDB 135](https://docs.software-univention.de/manual-5.0.html#software::configrepo)

Assumptions
-----------
* A minor or patch-level version depends on all previous versions of the same major version
* The next patch-level update incorporated all previous errata updates

With arch/
----------

This is the default layout with `repository/online/component/$comp/layout=arch`:

	1.3/
		##### ????? #####
	2.0/
	2.1/
	2.2/
	2.3/
		maintained/
		unmaintained/
			##### Paths in Packages file are relative to here #####
			2.3-X/
				dists/
					ucs/
						main/
							binary-amd64/
							binary-i386/
								Packages
								Packages.gz
				...
	2.4/
		maintained/
		unmaintained/
			hotfixes/	##### Deprecated since 3.0 #####
			secX/	##### Deprecated since 3.0 #####
			2.4-X/
				all/
					*_all.deb
					Packages
					Packages.gz
				i386/
					*_i386.deb
					Packages
					Packages.gz
				amd64/
					*_amd64.deb
					Packages
					Packages.gz
				extern/	##### Deprecated since 3.0 #####
					*.deb
					Packages
					Packages.gz
				source/	##### Only in unmaintained #####
					*.dsc
					*.tar.gz
					*.diff.gz
					*.changes
					Sources
					Sources.gz
				##### No dists/ here any more #####
			component/
				COMP/
					all/...
					i386/...
					amd64/...
					extern/...	##### Deprecated since 3.0 #####
	3.0/
		maintained/
		unmaintained/
			3.0-X/
				all/...
				i386/...
				amd64/...
				sources/...	##### Only in unmaintained #####
			errataX/	###### Deprecated since 3.1 #####
				all/...
				i386/...
				amd64/...
			component/
				COMP/
					all/...
					i386/...
					amd64/...
				COMP-errataX/	###### Deprecated since 3.1 #####
					all/...
					i386/...
					amd64/...
			##### No hotfixes/ and secX/ here any more #####
	3.1/
		maintained/
		unmaintained/
			3.1-X/
				all/...
				i386/...
				amd64/...
				sources/...	##### Only in unmaintained #####
			component/
				3.1-1-errata/
					all/...
					i386/...
					amd64/...
				COMP/
					all/...
					i386/...
					amd64/...
	3.2/
	3.3/
	4.0/
		maintained/
			4.0-0/
				all/...
				i386/...
				amd64/...
				sources/...	##### Only in unmaintained #####
				dists/
					ucs400/
						main/
							binary-amd64/
							binary-i386/
								Packages	##### Merged Packages file containing only *.deb for debootstrap #####
								Packages.gz
							debian-installer/
								binary-amd64/
								binary-i386/
									Packages	##### Merged Packages file containing only *.udeb for Debian-Installer #####
									Packages.gz
						contrib/	##### Unused #####
						non-free/	##### Unused #####
	4.1/
	4.2/
	4.3/
	4.4/

Without arch/
-------------

This is an alternative layout with `repository/online/component/$comp/layout=flat`:

	2.4/maintained/component/COMP/
		##### Paths in Packages file are relative to here #####
		*_all.deb
		*_i386.deb
		*_amd64.deb
		Packages
		Packages.gz
