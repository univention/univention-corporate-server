/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2007 James Harper

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#if !defined(_XEN_PUBLIC_H_)
#define _XEN_PUBLIC_H_

// {5C568AC5-9DDF-4FA5-A94A-39D67077819C}
DEFINE_GUID(GUID_XEN_IFACE, 0x5C568AC5, 0x9DDF, 0x4FA5, 0xA9, 0x4A, 0x39, 0xD6, 0x70, 0x77, 0x81, 0x9C);

// {14CE175A-3EE2-4fae-9252-00DBD84F018E}
DEFINE_GUID(GUID_DEVINTERFACE_XENBUS, 0x14ce175a, 0x3ee2, 0x4fae, 0x92, 0x52, 0x00, 0xdb, 0xd8, 0x4f, 0x01, 0x8e);

// {CC8B3D31-0D8C-474c-94D4-8D5F76FF9727}
DEFINE_GUID(GUID_DEVINTERFACE_EVTCHN, 0xcc8b3d31, 0x0d8c, 0x474c, 0x94, 0xd4, 0x8d, 0x5f, 0x76, 0xff, 0x97, 0x27);

// {0B66CEF6-7B6B-4324-BF31-D0F57EA22D30}
DEFINE_GUID(GUID_DEVINTERFACE_GNTDEV, 0x0b66cef6, 0x7b6b, 0x4324, 0xbf, 0x31, 0xd0, 0xf5, 0x7e, 0xa2, 0x2d, 0x30);


#endif
