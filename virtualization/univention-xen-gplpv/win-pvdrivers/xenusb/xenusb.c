/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2009 James Harper

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

#define INITGUID
#include "xenusb.h"
#include <stdlib.h>

DRIVER_INITIALIZE DriverEntry;

NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) {
  NTSTATUS status = STATUS_SUCCESS;
  WDF_DRIVER_CONFIG config;
  WDFDRIVER driver;

  FUNCTION_ENTER();

  WDF_DRIVER_CONFIG_INIT(&config, XenUsb_EvtDriverDeviceAdd);
  status = WdfDriverCreate(DriverObject, RegistryPath, WDF_NO_OBJECT_ATTRIBUTES, &config, &driver);

  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDriverCreate failed with status 0x%x\n", status);
  }

  FUNCTION_EXIT();

  return status;
}
