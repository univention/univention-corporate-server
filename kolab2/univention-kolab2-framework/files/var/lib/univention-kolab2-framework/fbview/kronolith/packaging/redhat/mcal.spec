#
# $Horde: kronolith/packaging/redhat/mcal.spec,v 1.7 2004/01/01 15:15:47 jan Exp $
#
# Copyright 2003-2004 Brent J. Nordquist <bjn@horde.org>
#
# See the enclosed file COPYING for license information (GPL). If you
# did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
#
# This is the SPEC file for the MCAL Red Hat RPMs/SRPM.
#

Name: mcal
Version: 0.7
Summary: A Calendaring library, and drivers
Epoch: 1
Release: 0horde2
Group: System Environment/Libraries
Vendor: The Horde Project
URL: http://www.horde.org/
Packager: Brent J. Nordquist <bjn@horde.org>
Source0: libmcal-%{version}.tar.gz
Source1: mcaldrivers-0.9.tar.gz
License: GPL and partial BSD-Like with an advertising clause for mstore driver (driver is included)
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
The mcal library and the mcal drivers implement a simple calendaring server
and (currently) two calendaring storage adapators, one each for the icap
protocol and local files system.

%package devel
Summary: Files needed for developing applications which use the mcal
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description devel
The mcal library and the mcal drivers implement a simple calendaring
server and (currently) two calendaring storage adapators, one each for
the icap protocol and local files system. The mcal-devel package contains
header files necessary to compile other packages to use the mcal library
and its drivers.


%prep

# The libmcal package and drivers are packaged separately but integrated,
# you have to integrate by hand
rm -rf $RPM_BUILD_DIR/libmcal
tar -zxvf $RPM_SOURCE_DIR/libmcal-%{version}.tar.gz
tar -zxvf $RPM_SOURCE_DIR/mcaldrivers-0.9.tar.gz
mv $RPM_BUILD_DIR/mcal-drivers/icap $RPM_BUILD_DIR/libmcal
mv $RPM_BUILD_DIR/mcal-drivers/mstore $RPM_BUILD_DIR/libmcal


%build
CFLAGS="$RPM_OPT_FLAGS -fPIC" ; export CFLAGS

# We have to build the mstore and icap drivers by hand since they're
# not automated
cd $RPM_BUILD_DIR/libmcal/mstore
make
cd ../icap
make
cd ..

# libmcal's configure script isn't executable out of the box
chmod 755 ./configure

# The prefix here is because libmcal's installation is a bit weird
%configure --prefix=$RPM_BUILD_ROOT/usr --with-mstore --with-icap
make

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

# This is an artifict of libmcal not being "standard" and exploding
# into libmcal-%{version}
cd $RPM_BUILD_DIR/libmcal
%makeinstall
mv -f mstore/Changelog mstore/Changelog.mstore
mv -f mstore/README mstore/README.mstore
mv -f icap/Changelog icap/Changelog.icap
install -d -m 1777 $RPM_BUILD_ROOT%{_var}/calendar

# This is because libmcal doesn't version its libraries in its default
# build
pushd $RPM_BUILD_ROOT/usr/lib
ln -s libmcal.so libmcal.so.0.7
ln -s libmcal.so libmcal.so.0
popd

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/ldconfig
if (test ! -f /etc/mpasswd); then
  touch /etc/mpasswd;
  chown root:apache /etc/mpasswd;
  chmod 640 /etc/mpasswd
fi
grep "^mcaluser:" /etc/mpasswd >/dev/null
if (test $? -eq 1); then
  mcalpass=`openssl rand 8 -base64 | cut -c1-8`
  if (test -z "$mcalpass"); then
    mcalpass=mcalpass
  fi
  htpasswd -bc /etc/mpasswd mcaluser "$mcalpass"
  echo mcaluser password is $mcalpass
fi

%postun -p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc libmcal/LICENSE libmcal/CHANGELOG libmcal/FEATURE-IMPLEMENTATION 
%doc libmcal/FUNCTION-REF.html libmcal/*-MCAL libmcal/README
%doc libmcal/icap/Changelog.icap
%doc libmcal/mstore/README.mstore libmcal/mstore/Changelog.mstore
%attr(0755,root,root) %{_libdir}/*.so*
%attr(1777,root,root) %{_var}/calendar

%files devel
%defattr(644,root,root,755)
%{_includedir}/*
%{_libdir}/*.a

%changelog
* Sat Feb 15 2003 Brent J. Nordquist <bjn@horde.org> 0.7-0horde2
- better way of packaging /var/calendar (idea from the Arvin RPM)
- cleanup of %doc files (idea from the Arvin RPM)

* Thu Feb 13 2003 Brent J. Nordquist <bjn@horde.org> 0.7-0horde1
- libmcal-0.7 and mcaldrivers-0.9 final

* Fri Dec 14 2001 Brent J. Nordquist <bjn@horde.org>
- randomize password during installation (avoid default password)

* Mon Dec 03 2001 Mike Hardy <mike@h3c.org>
- adding in calendar directory and password creation to post install screen

* Sun Dec 02 2001 Mike Hardy <mike@h3c.org>
- initial package
