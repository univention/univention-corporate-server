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

#if !defined(_XENSTUB_H_)
#define _XENSTUB_H_

#include <ntddk.h>
#include <wdm.h>
#include <initguid.h>
#include <wdmguid.h>
#include <errno.h>
#define NTSTRSAFE_LIB
#include <ntstrsafe.h>
#define __DRIVER_NAME "XenStub"
#include <xen_windows.h>

typedef struct
{
  PDEVICE_OBJECT fdo;
  PDEVICE_OBJECT pdo;
  PDEVICE_OBJECT lower_do;
} XENSTUB_DEVICE_DATA, *PXENSTUB_DEVICE_DATA;

#endif
