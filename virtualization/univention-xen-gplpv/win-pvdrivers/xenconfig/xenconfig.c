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

#include "xenconfig.h"
#include <stdlib.h>

DRIVER_INITIALIZE DriverEntry;
static NTSTATUS
XenConfig_AddDevice(PDRIVER_OBJECT DriverObject, PDEVICE_OBJECT PhysicalDeviceObject);
static NTSTATUS
XenConfig_Pass(PDEVICE_OBJECT DeviceObject, PIRP Irp);
static NTSTATUS
XenConfig_Pnp(PDEVICE_OBJECT DeviceObject, PIRP Irp);
static NTSTATUS
XenConfig_AddDevice();
//static NTSTATUS
//XenConfig_Unload();

#ifdef ALLOC_PRAGMA
#pragma alloc_text (INIT, DriverEntry)
#pragma alloc_text (PAGE, XenConfig_AddDevice)
#endif

static BOOLEAN gplpv;

static NTSTATUS
XenConfig_Power(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status;
  PXENCONFIG_DEVICE_DATA xcdd = device_object->DeviceExtension;

  PoStartNextPowerIrp(irp);
  IoSkipCurrentIrpStackLocation(irp);
  status = PoCallDriver(xcdd->lower_do, irp);
  return status;
}

NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
  NTSTATUS status = STATUS_SUCCESS;
  int i;

  UNREFERENCED_PARAMETER(RegistryPath);

  KdPrint((__DRIVER_NAME " --> DriverEntry\n"));

  for (i = 0; i <= IRP_MJ_MAXIMUM_FUNCTION; i++)
    DriverObject->MajorFunction[i] = XenConfig_Pass;
  DriverObject->MajorFunction[IRP_MJ_PNP] = XenConfig_Pnp;
  DriverObject->MajorFunction[IRP_MJ_POWER] = XenConfig_Power;
  DriverObject->DriverExtension->AddDevice = XenConfig_AddDevice;

  KdPrint((__DRIVER_NAME " <-- DriverEntry\n"));

  return status;
}

static NTSTATUS
XenConfig_AddDevice(
  PDRIVER_OBJECT DriverObject,
  PDEVICE_OBJECT PhysicalDeviceObject
  )
{
  NTSTATUS status;
  PDEVICE_OBJECT device_object = NULL;
  PXENCONFIG_DEVICE_DATA xcdd;

  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  status = IoCreateDevice (DriverObject,
    sizeof(XENCONFIG_DEVICE_DATA),
    NULL,
    FILE_DEVICE_UNKNOWN,
    FILE_DEVICE_SECURE_OPEN,
    FALSE,
    &device_object);

  xcdd = (PXENCONFIG_DEVICE_DATA)device_object->DeviceExtension;

  xcdd->pdo = PhysicalDeviceObject;
  xcdd->lower_do = IoAttachDeviceToDeviceStack(
    device_object, PhysicalDeviceObject);
  device_object->Flags |= xcdd->lower_do->Flags;

  device_object->DeviceType = xcdd->lower_do->DeviceType;

  device_object->Characteristics = 
    xcdd->lower_do->Characteristics;

  xcdd->filter_do = device_object;

  device_object->Flags &= ~DO_DEVICE_INITIALIZING;

  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));

  return STATUS_SUCCESS;
}

static NTSTATUS
XenConfig_Pass(PDEVICE_OBJECT DeviceObject, PIRP Irp)
{
  PXENCONFIG_DEVICE_DATA xcdd = (PXENCONFIG_DEVICE_DATA)DeviceObject->DeviceExtension;
  NTSTATUS status;
    
  IoSkipCurrentIrpStackLocation(Irp);
  status = IoCallDriver(xcdd->lower_do, Irp);
  return status;
}

static NTSTATUS
XenConfig_Pnp_IoCompletion(PDEVICE_OBJECT device_object, PIRP irp, PVOID context)
{
  PKEVENT event = (PKEVENT)context;

  UNREFERENCED_PARAMETER(device_object);

//  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  if (irp->PendingReturned)
  {
    KeSetEvent(event, IO_NO_INCREMENT, FALSE);
  }

//  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));

  return STATUS_MORE_PROCESSING_REQUIRED;
}

static NTSTATUS
XenConfig_SendAndWaitForIrp(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status;
  PXENCONFIG_DEVICE_DATA xcdd = (PXENCONFIG_DEVICE_DATA)device_object->DeviceExtension;
  KEVENT event;

  UNREFERENCED_PARAMETER(device_object);

//  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  KeInitializeEvent(&event, NotificationEvent, FALSE);

  IoCopyCurrentIrpStackLocationToNext(irp);
  IoSetCompletionRoutine(irp, XenConfig_Pnp_IoCompletion, &event, TRUE, TRUE, TRUE);

  status = IoCallDriver(xcdd->lower_do, irp);

  if (status == STATUS_PENDING)
  {
//    KdPrint((__DRIVER_NAME "     waiting ...\n"));
    KeWaitForSingleObject(&event, Executive, KernelMode, FALSE, NULL);
//    KdPrint((__DRIVER_NAME "     ... done\n"));
    status = irp->IoStatus.Status;
  }

//  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));

  return status;
}

static VOID
XenConfig_Pnp_StartDeviceCallback(PDEVICE_OBJECT device_object, PVOID context)
{
  NTSTATUS status = STATUS_SUCCESS;
  //PXENCONFIG_DEVICE_DATA xcdd = device_object->DeviceExtension;
  PIRP irp = context;
  
  UNREFERENCED_PARAMETER(device_object);

  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));
  
  irp->IoStatus.Status = status;
  
  IoCompleteRequest(irp, IO_NO_INCREMENT);

  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));
}

static PMDL
XenConfig_MakeConfigPage(PDEVICE_OBJECT device_object)
{
  NTSTATUS status;
  PXENCONFIG_DEVICE_DATA xcdd = (PXENCONFIG_DEVICE_DATA)device_object->DeviceExtension;
  HANDLE hwkey_handle, xenkey_handle, confkey_handle;
  ULONG length;
  PKEY_BASIC_INFORMATION key_info;
  PKEY_VALUE_PARTIAL_INFORMATION type_info;
  PKEY_VALUE_PARTIAL_INFORMATION value_info;
  UNICODE_STRING xenkey_name, confkey_name;
  UNICODE_STRING type_name, value_name;
  UNICODE_STRING tmp_unicode_string;
  //UNICODE_STRING typekey_value, valuekey_value;
  //UNICODE_STRING value_value;
  OBJECT_ATTRIBUTES oa;
  ULONG info_length = 1000;
  PMDL mdl;
  UCHAR type;
  ANSI_STRING setting;
  ANSI_STRING value;
  PUCHAR ptr;
  int i;

  mdl = AllocateUncachedPage();
  ptr = MmGetMdlVirtualAddress(mdl);

  status = IoOpenDeviceRegistryKey(xcdd->pdo, PLUGPLAY_REGKEY_DEVICE, KEY_READ, &hwkey_handle);

  if (!NT_SUCCESS(status))
  {
    KdPrint((__DRIVER_NAME "    cannot get hardware key\n"));
    ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_END, NULL, NULL);          
    return mdl;
  }
  RtlInitUnicodeString(&xenkey_name, L"XenConfig");
  InitializeObjectAttributes(&oa, &xenkey_name, 0, hwkey_handle, NULL);
  status = ZwOpenKey(&xenkey_handle, KEY_READ, &oa);
  if (!NT_SUCCESS(status))
  {
    // close key_handle
    KdPrint((__DRIVER_NAME "    cannot get XenConfig key\n"));
    ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_END, NULL, NULL);          
    return mdl;
  }
  // XenConfig key exists, so we go ahead and make fake memory resources
  RtlInitUnicodeString(&type_name, L"type");
  RtlInitUnicodeString(&value_name, L"value");
  key_info = ExAllocatePoolWithTag(PagedPool, info_length, XENCONFIG_POOL_TAG);
  type_info = ExAllocatePoolWithTag(PagedPool, info_length, XENCONFIG_POOL_TAG);
  value_info = ExAllocatePoolWithTag(PagedPool, info_length, XENCONFIG_POOL_TAG);
  //value.Buffer = ExAllocatePoolWithTag(PagedPool, info_length, XENCONFIG_POOL_TAG);
  //value.MaximumLength = info_length;
  setting.Buffer = ExAllocatePoolWithTag(PagedPool, info_length, XENCONFIG_POOL_TAG);
  setting.MaximumLength = (USHORT)info_length;
  
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_RUN, NULL, NULL);
  for (i = 0; ZwEnumerateKey(xenkey_handle, i, KeyBasicInformation, key_info, info_length, &length) == STATUS_SUCCESS; i++)
  {
    confkey_name.Length = (USHORT)key_info->NameLength;
    confkey_name.MaximumLength = (USHORT)key_info->NameLength;
    confkey_name.Buffer = key_info->Name;
    RtlUnicodeStringToAnsiString(&setting, &confkey_name, FALSE);
    setting.Buffer[setting.Length] = 0;
    KdPrint((__DRIVER_NAME "     config key name = '%wZ'\n", &confkey_name));
    InitializeObjectAttributes(&oa, &confkey_name, 0, xenkey_handle, NULL);
    status = ZwOpenKey(&confkey_handle, KEY_READ, &oa);
    if (!NT_SUCCESS(status))
    {
      KdPrint((__DRIVER_NAME "    cannot get handle for XenConfig\\%wZ\n", &confkey_name));
      continue;
    }
    
    status = ZwQueryValueKey(confkey_handle, &type_name, KeyValuePartialInformation, type_info, info_length, &length);
    // make sure type is dword
    type = (UCHAR)*(ULONG *)type_info->Data;
    status = ZwQueryValueKey(confkey_handle, &value_name, KeyValuePartialInformation, value_info, info_length, &length);
    if (!NT_SUCCESS(status))
    {
      ADD_XEN_INIT_REQ(&ptr, type, setting.Buffer, NULL);
    }
    else
    {
      switch(value_info->Type)
      {
      case REG_DWORD:
        ADD_XEN_INIT_REQ(&ptr, type, setting.Buffer, UlongToPtr(*(PULONG)value_info->Data));
        break;
        
      case REG_SZ:
        tmp_unicode_string.Length = (USHORT)value_info->DataLength;
        tmp_unicode_string.MaximumLength = (USHORT)value_info->DataLength;
        tmp_unicode_string.Buffer = (PWCHAR)value_info->Data;
        RtlUnicodeStringToAnsiString(&value, &tmp_unicode_string, FALSE);
        value.Buffer[value.Length] = 0;
        ADD_XEN_INIT_REQ(&ptr, type, setting.Buffer, value.Buffer);
        break;
      
      default:
        // report error here
        break;
      }
    }
  }
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_END, NULL, NULL);          

  ExFreePoolWithTag(key_info, XENCONFIG_POOL_TAG);

  return mdl;
}

static NTSTATUS
XenConfig_QueueWorkItem(PDEVICE_OBJECT device_object, PIO_WORKITEM_ROUTINE routine, PVOID context)
{
  PIO_WORKITEM work_item;
  NTSTATUS status = STATUS_SUCCESS;

  work_item = IoAllocateWorkItem(device_object);
  IoQueueWorkItem(work_item, routine, DelayedWorkQueue, context);
	
  return status;
}

static NTSTATUS
XenConfig_Pnp_StartDevice(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status;
  //PXENCONFIG_DEVICE_DATA xcdd = (PXENCONFIG_DEVICE_DATA)device_object->DeviceExtension;
  PIO_STACK_LOCATION stack;
  PMDL mdl;
  PCM_RESOURCE_LIST old_crl, new_crl;
  PCM_PARTIAL_RESOURCE_LIST prl;
  PCM_PARTIAL_RESOURCE_DESCRIPTOR prd;
  ULONG old_length, new_length;

  UNREFERENCED_PARAMETER(device_object);

  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  stack = IoGetCurrentIrpStackLocation(irp);

  if ((mdl = XenConfig_MakeConfigPage(device_object)) != NULL)
  {
    old_crl = stack->Parameters.StartDevice.AllocatedResourcesTranslated;
    old_length = FIELD_OFFSET(CM_RESOURCE_LIST, List) + 
      FIELD_OFFSET(CM_FULL_RESOURCE_DESCRIPTOR, PartialResourceList) +
      FIELD_OFFSET(CM_PARTIAL_RESOURCE_LIST, PartialDescriptors) +
      sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR) * old_crl->List[0].PartialResourceList.Count;
    new_length = old_length + sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR) * 1;
    new_crl = ExAllocatePoolWithTag(PagedPool, new_length, XENCONFIG_POOL_TAG);
    memcpy(new_crl, old_crl, old_length);
    prl = &new_crl->List[0].PartialResourceList;
    prd = &prl->PartialDescriptors[prl->Count++];
    prd->Type = CmResourceTypeMemory;
    prd->ShareDisposition = CmResourceShareDeviceExclusive;
    prd->Flags = CM_RESOURCE_MEMORY_READ_WRITE;
    KdPrint((__DRIVER_NAME "     PFN[0] = %p\n", MmGetMdlPfnArray(mdl)[0]));
    prd->u.Memory.Start.QuadPart = ((ULONGLONG)MmGetMdlPfnArray(mdl)[0]) << PAGE_SHIFT;
    prd->u.Memory.Length = PAGE_SIZE;
    KdPrint((__DRIVER_NAME "     Start = %08x:%08x, Length = %d\n", prd->u.Memory.Start.HighPart, prd->u.Memory.Start.LowPart, prd->u.Memory.Length));
    stack->Parameters.StartDevice.AllocatedResourcesTranslated = new_crl;

    old_crl = stack->Parameters.StartDevice.AllocatedResources;
    new_crl = ExAllocatePoolWithTag(PagedPool, new_length, XENCONFIG_POOL_TAG);
    memcpy(new_crl, old_crl, old_length);
    prl = &new_crl->List[0].PartialResourceList;
    prd = &prl->PartialDescriptors[prl->Count++];
    prd->Type = CmResourceTypeMemory;
    prd->ShareDisposition = CmResourceShareDeviceExclusive;
    prd->Flags = CM_RESOURCE_MEMORY_READ_WRITE;
    prd->u.Memory.Start.QuadPart = (ULONGLONG)MmGetMdlPfnArray(mdl)[0] << PAGE_SHIFT;
    prd->u.Memory.Length = PAGE_SIZE;
    stack->Parameters.StartDevice.AllocatedResources = new_crl;

    // free the original resource lists???
  }

  IoMarkIrpPending(irp);
  status = XenConfig_SendAndWaitForIrp(device_object, irp);

  XenConfig_QueueWorkItem(device_object, XenConfig_Pnp_StartDeviceCallback, irp);

  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));
  
  return STATUS_PENDING;
}

static NTSTATUS
XenConfig_Pnp(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status = STATUS_SUCCESS;
  PIO_STACK_LOCATION stack;
  PXENCONFIG_DEVICE_DATA xcdd = (PXENCONFIG_DEVICE_DATA)device_object->DeviceExtension;

//  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  stack = IoGetCurrentIrpStackLocation(irp);

  switch (stack->MinorFunction) {
#if 0
  case IRP_MN_START_DEVICE:
    return XenConfig_Pnp_StartDevice(device_object, irp);
  case IRP_MN_QUERY_CAPABILITIES:
//    KdPrint((__DRIVER_NAME "     IRP_MN_QUERY_CAPABILITIES\n"));
    stack->Parameters.DeviceCapabilities.Capabilities->NoDisplayInUI = 1;
    status = XenConfig_SendAndWaitForIrp(device_object, irp);
    status = irp->IoStatus.Status = STATUS_SUCCESS;
    IoCompleteRequest(irp, IO_NO_INCREMENT);
//    KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));
    return status;
#endif
  default:
    IoSkipCurrentIrpStackLocation(irp);
    status = IoCallDriver(xcdd->lower_do, irp);
    break;
  }

//  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ " (returning with status %08x)\n", status));

  return status;
}
