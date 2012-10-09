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

#include "xenpci.h"

VOID
XenPci_EvtDeviceFileCreate(WDFDEVICE device, WDFREQUEST request, WDFFILEOBJECT file_object)
{
  NTSTATUS status;
  PXENPCI_DEVICE_INTERFACE_DATA xpdid = GetXpdid(file_object);
  WDF_IO_QUEUE_CONFIG queue_config;
  
  FUNCTION_ENTER();
  
  xpdid->type = DEVICE_INTERFACE_TYPE_XENBUS; //TODO: determine the actual type
  
  KeInitializeSpinLock(&xpdid->lock);
  WDF_IO_QUEUE_CONFIG_INIT(&queue_config, WdfIoQueueDispatchSequential);
  status = XenBus_DeviceFileInit(device, &queue_config, file_object); /* this completes the queue init */  
  if (!NT_SUCCESS(status)) {
      WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
  }
  status = WdfIoQueueCreate(device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, &xpdid->io_queue);
  if (!NT_SUCCESS(status)) {
      KdPrint(("Error creating queue 0x%x\n", status));
      WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
  }

  WdfRequestComplete(request, STATUS_SUCCESS);
  
  FUNCTION_EXIT();
}

VOID
XenPci_EvtFileCleanup(WDFFILEOBJECT file_object)
{
  PXENPCI_DEVICE_INTERFACE_DATA xpdid = GetXpdid(file_object);

  FUNCTION_ENTER();
  xpdid->EvtFileCleanup(file_object);
  FUNCTION_EXIT();
}

VOID
XenPci_EvtFileClose(WDFFILEOBJECT file_object)
{
  
  PXENPCI_DEVICE_INTERFACE_DATA xpdid = GetXpdid(file_object);

  FUNCTION_ENTER();
  xpdid->EvtFileClose(file_object);
  FUNCTION_EXIT();
}

VOID
XenPci_EvtIoDefault(WDFQUEUE queue, WDFREQUEST request)
{
  WDFFILEOBJECT file_object = WdfRequestGetFileObject(request);
  PXENPCI_DEVICE_INTERFACE_DATA xpdid = GetXpdid(file_object);

  UNREFERENCED_PARAMETER(queue);
  
  FUNCTION_ENTER();
  WdfRequestForwardToIoQueue(request, xpdid->io_queue);
  FUNCTION_EXIT();
}
