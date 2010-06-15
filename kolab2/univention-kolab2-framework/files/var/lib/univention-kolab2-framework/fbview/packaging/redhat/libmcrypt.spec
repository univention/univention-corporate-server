#
# $Horde: horde/packaging/redhat/libmcrypt.spec,v 1.3 2004/01/01 15:16:43 jan Exp $
#
# Copyright 2003-2004 Brent J. Nordquist <bjn@horde.org>
#
# See the enclosed file COPYING for license information (GPL). If you
# did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
#
# Based on libmcrypt.spec by Troels Arvin (http://rpms.arvin.dk/)
# but updated to libmcrypt 2.5.6
#

%define LIBTOOL_REQS %(rpm -q --quiet libtool-libs && echo ", libtool-libs" || echo ", libtool")

Summary:	encryption/decryption library
Summary(pl):	biblioteka z funkcjami szyfruj±cymi oraz deszyfruj±cymi
Name:		libmcrypt
Version:	2.5.6
Release:	0horde2
License:	LGPL
Vendor:		Nikos Mavroyanopoulos <nmav@hellug.gr>
Packager:	Troels Arvin <troels@arvin.dk>
Group:		Libraries
Group(de):	Libraries
Group(es):	Bibliotecas
Group(fr):	Librairies
Group(pl):	Biblioteki
Group(pt_BR):	Bibliotecas
Group(ru):	‚…¬Ã…œ‘≈À…
Group(uk):	‚¶¬Ã¶œ‘≈À…
Source0:	ftp://mcrypt.hellug.gr/pub/crypto/mcrypt/libmcrypt/%{name}-%{version}.tar.gz
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	make
BuildRequires:	rpm >= 3.0.5
BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(id -u -n)
Requires:       rpm >= 3.0.5%{LIBTOOL_REQS}

%description
A replacement for the old unix crypt(1) command. Mcrypt uses the
following encryption (block) algorithms: BLOWFISH, DES, TripleDES,
3-WAY, SAFER-SK64, SAFER-SK128, CAST-128, RC2 TEA (extended), TWOFISH,
RC6, IDEA and GOST. The unix crypt algorithm is also included, to
allow compability with the crypt(1) command.

CBC, ECB, OFB and CFB modes of encryption are supported. A library
which allows access to the above algorithms and modes is included.

%description -l pl
Zamiennik dla starej unixowej funkcji crypt(). Mcrypt uøywa
nastÍpuj±cych algorytmÛw: BLOWFISH, DES, TripleDES, 3-WAY, SAFER-SK64,
SAFER-SK128, CAST-128, RC2 TEA (rozszerzona), TWOFISH, RC6, IDEA i
GOST. Unixowy algorytm crypt takøe jest obs≥ugiwany by zachowaÊ
kompatybilno∂Ê z crypt(1).

%package devel
Summary:	Header files and development documentation for libmcrypt
Summary(pl):	Pliki nag≥Ûwkowe i dokumentacja do libmcrypt
Group:		Development/Libraries
Group(de):	Entwicklung/Libraries
Group(es):	Desarrollo/Bibliotecas
Group(fr):	Development/Librairies
Group(pl):	Programowanie/Biblioteki
Group(pt_BR):	Desenvolvimento/Bibliotecas
Group(ru):	Ú¡⁄“¡¬œ‘À¡/‚…¬Ã…œ‘≈À…
Group(uk):	Úœ⁄“œ¬À¡/‚¶¬Ã¶œ‘≈À…
Requires:	%{name} = %{version}

%description devel
Header files and development documentation for libmcrypt.

%description -l pl devel
Pliki nag≥Ûwkowe i dokumentacja do libmcrypt.

%prep
%setup -q

%build
CFLAGS="$RPM_OPT_FLAGS" CXXFLAGS="$RPM_OPT_FLAGS" ./configure \
 	--prefix=%{_prefix} \
	--exec-prefix=%{_exec_prefix} \
	--bindir=%{_bindir} \
	--sbindir=%{_sbindir} \
	--sysconfdir=%{_sysconfdir} \
	--datadir=%{_datadir} \
	--includedir=%{_includedir} \
	--libdir=%{_libdir} \
	--libexecdir=%{_libexecdir} \
	--localstatedir=%{_localstatedir} \
	--sharedstatedir=%{_sharedstatedir} \
	--mandir=%{_mandir} \
	--infodir=%{_infodir} \
	--enable-dynamic-loading \
	--enable-static \
	--enable-shared \
	--disable-libltdl
make

%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR="$RPM_BUILD_ROOT" install

%post	-p /sbin/ldconfig
%postun -p /sbin/ldconfig

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%dir %{_libdir}/libmcrypt
%attr(755,root,root) %{_libdir}/lib*.so*
%attr(755,root,root) %{_libdir}/libmcrypt/*.so
%doc AUTHORS ChangeLog COPYING.LIB INSTALL KNOWN-BUGS NEWS README THANKS TODO

%files devel
%defattr(644,root,root,755)
%doc doc/*
%attr(755,root,root) %{_bindir}/libmcrypt-config
%{_libdir}/lib*.a
%{_libdir}/libmcrypt/*.a
%attr(755,root,root) %{_libdir}/lib*.la
%attr(755,root,root) %{_libdir}/libmcrypt/*.la
%{_mandir}/man3/*
%{_includedir}/*.h
%{_datadir}/aclocal/*

%changelog
* Sun Feb 16 2003 Brent J. Nordquist <bjn@horde.org> 2.5.6-0horde2
- Reenable dynamic loading
- Move man page back to -devel RPM

* Sat Feb 15 2003 Brent J. Nordquist <bjn@horde.org> 2.5.6-0horde1
- Updated for 2.5.6 (need enable-static now)
- Disable dynamic loading (since 2.5.4, see README)
- Put man page in base RPM

* Wed Jun 19 2002 Troels Arvin <troels@arvin.dk>
  [2.5.2-1.arvin]
- New sources.
- *.la files not in -devel package, but in the main package.

* Wed Jun 19 2002 Troels Arvin <troels@arvin.dk>
  [2.5.1-3.arvin]
- Fixed spec-file's "clean"-section.
- At some point before that: Created libmcrypt 2.5.1 package
  with new sources.

* Tue Mar 5 2002 Troels Arvin <troels@arvin.dk>
  [2.4.22-2.arvin]
- Modified slightly from PLD's corresponding package.
- Added distribution tags, etc. to release-number.
- Fused -devel and -static packages to -devel package.
