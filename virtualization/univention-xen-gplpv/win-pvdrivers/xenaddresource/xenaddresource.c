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

#include "xenaddresource.h"
#include <stdlib.h>

DRIVER_INITIALIZE DriverEntry;
static NTSTATUS
XenAddResource_AddDevice(WDFDRIVER Driver, PWDFDEVICE_INIT DeviceInit);
static NTSTATUS
XenAddResource_PreprocessWdmIrpPNP(WDFDEVICE Device, PIRP Irp);
//static VOID
//XenAddResource_IoInternalDeviceControl(WDFQUEUE Queue, WDFREQUEST Request, size_t OutputBufferLength, size_t InputBufferLength, ULONG IoControlCode);
static NTSTATUS
XenAddResource_EvtDeviceFilterAddResourceRequirements(WDFDEVICE Device, WDFIORESREQLIST IoResourceRequirementsList);

#ifdef ALLOC_PRAGMA
#pragma alloc_text (INIT, DriverEntry)
#pragma alloc_text (PAGE, XenAddResource_AddDevice)
#endif

static BOOLEAN AutoEnumerate;

static WDFDEVICE Device;

NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
  WDF_DRIVER_CONFIG config;
  NTSTATUS status;

  KdPrint((__DRIVER_NAME " --> DriverEntry\n"));

  WDF_DRIVER_CONFIG_INIT(&config, XenAddResource_AddDevice);
  status = WdfDriverCreate(
                      DriverObject,
                      RegistryPath,
                      WDF_NO_OBJECT_ATTRIBUTES,
                      &config,
                      WDF_NO_HANDLE);
  if(!NT_SUCCESS(status))
  {
    KdPrint((__DRIVER_NAME " WdfDriverCreate failed with status 0x%08x\n", status));
  }

  KdPrint((__DRIVER_NAME " <-- DriverEntry\n"));

  return status;
}

static NTSTATUS
XenAddResource_AddDevice(WDFDRIVER Driver, PWDFDEVICE_INIT DeviceInit)
{
  NTSTATUS Status;
  WDF_OBJECT_ATTRIBUTES attributes;
  UCHAR PnpMinors[2] = { IRP_MN_START_DEVICE, IRP_MN_STOP_DEVICE };

  UNREFERENCED_PARAMETER(Driver);

  KdPrint((__DRIVER_NAME " --> DeviceAdd\n"));

  WdfFdoInitSetFilter(DeviceInit);

  Status = WdfDeviceInitAssignWdmIrpPreprocessCallback(DeviceInit, XenAddResource_PreprocessWdmIrpPNP, IRP_MJ_PNP, PnpMinors, 2);
  if (!NT_SUCCESS(Status))
    KdPrint((__DRIVER_NAME "     WdfDeviceInitAssignWdmIrpPreprocessCallback(IRP_MJ_PNP) Status = %08X\n", Status));

  WDF_OBJECT_ATTRIBUTES_INIT(&attributes);
  Status = WdfDeviceCreate(&DeviceInit, &attributes, &Device);  
  if(!NT_SUCCESS(Status))
  {
    KdPrint((__DRIVER_NAME "     WdfDeviceCreate failed with status 0x%08x)\n", Status));
    return Status;
  }

  KdPrint((__DRIVER_NAME " <-- DeviceAdd\n"));

  return Status;
}

static NTSTATUS
XenAddResource_PreprocessWdmIrpPNP(WDFDEVICE Device, PIRP Irp)
{
  NTSTATUS Status = STATUS_SUCCESS;
  PIO_STACK_LOCATION Stack;
  PXENPCI_XEN_DEVICE_DATA XenDeviceData;
  //PXENADDRESOURCE_DEVICE_DATA XenAddResourcesDeviceData;

  KdPrint((__DRIVER_NAME " --> WdmIrpPreprocessPNP\n"));

  Stack = IoGetCurrentIrpStackLocation(Irp);

  switch (Stack->MinorFunction) {
  case IRP_MN_START_DEVICE:
    KdPrint((__DRIVER_NAME "     IRP_MN_START_DEVICE\n"));

    if (Stack->Parameters.StartDevice.AllocatedResources != NULL)
    {
      // free stuff here... or maybe just exit
    }
    if (Stack->Parameters.StartDevice.AllocatedResourcesTranslated != NULL)
    {
      // free stuff here... or maybe just exit
    }

    XenDeviceData = WdfDeviceWdmGetPhysicalDevice(Device)->DeviceExtension;
    // verify Magic here

    Stack->Parameters.StartDevice.AllocatedResources = ExAllocatePoolWithTag(NonPagedPool, sizeof(CM_RESOURCE_LIST) + sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR) * 1, XENADDRESOURCE_POOL_TAG);
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated = ExAllocatePoolWithTag(NonPagedPool, sizeof(CM_RESOURCE_LIST) + sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR) * 1, XENADDRESOURCE_POOL_TAG);

    Stack->Parameters.StartDevice.AllocatedResources->Count = 1;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].InterfaceType = Internal;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].BusNumber = 0;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.Version = 1;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.Revision = 1;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.Count = 2;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.PartialDescriptors[0].Type = CmResourceTypeMemory;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.PartialDescriptors[0].ShareDisposition = CmResourceShareDeviceExclusive;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.PartialDescriptors[0].Flags = CM_RESOURCE_MEMORY_READ_WRITE;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.PartialDescriptors[0].u.Memory.Start.QuadPart = (ULONGLONG)XenDeviceData;
    Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.PartialDescriptors[0].u.Memory.Length = sizeof(XENPCI_XEN_DEVICE_DATA);
    memcpy(&Stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList.PartialDescriptors[1], &XenDeviceData->InterruptRaw, sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR));

    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->Count = 1;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].InterfaceType = Internal;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].BusNumber = 0;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.Version = 1;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.Revision = 1;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.Count = 2;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.PartialDescriptors[0].Type = CmResourceTypeMemory;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.PartialDescriptors[0].ShareDisposition = CmResourceShareDeviceExclusive;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.PartialDescriptors[0].Flags = CM_RESOURCE_MEMORY_READ_WRITE;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.PartialDescriptors[0].u.Memory.Start.QuadPart = (ULONGLONG)XenDeviceData;
    Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.PartialDescriptors[0].u.Memory.Length = sizeof(XENPCI_XEN_DEVICE_DATA);
    memcpy(&Stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList.PartialDescriptors[1], &XenDeviceData->InterruptTranslated, sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR));

    IoSkipCurrentIrpStackLocation(Irp);
    Status = WdfDeviceWdmDispatchPreprocessedIrp(Device, Irp);
    break;
  default:
    IoSkipCurrentIrpStackLocation(Irp);
    Status = WdfDeviceWdmDispatchPreprocessedIrp(Device, Irp);
    KdPrint((__DRIVER_NAME "     Unknown Minor %d\n", Stack->MinorFunction));
    break;
  }

  KdPrint((__DRIVER_NAME " <-- WdmIrpPreprocessPNP (returning with status %08x\n", Status));

  return Status;
}
