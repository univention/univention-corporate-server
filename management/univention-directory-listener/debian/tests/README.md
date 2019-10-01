autokpgtest
===========

changes:
* dialog -> whiptail
* debian-archive-keyring -> univention-archive-key-v4
* Drop `SECURITY_MIRROR`
* Explicitly use debootstrap sid script

Create LXC
----------
See `/usr/share/lxc/templates/lxc-debian`

	sudo lxc-create \
	    -B dir \
	    -n autopkgtest-ucs442-amd64 \
	    -t ./lxc-ucs \
	    -- \
	    --mirror http://univention-repository.knut.univention.de/4.4/maintained/4.4-2

Run LXC
-------

	autopkgtest \
	    --set-lang C.UTF-8 \
	    --debug \
	    --shell-fail \
	    --apt-upgrade \
	    --setup-commands ./add-source.sh \
	    ./ \
	    -- \
	    autopkgtest-virt-lxc \
	    --ephemeral \
	    --sudo \
	    autopkgtest-ucs442-amd64
