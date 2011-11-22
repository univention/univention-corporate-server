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

#include "xenstub.h"
#include <stdlib.h>

DRIVER_INITIALIZE DriverEntry;

static NTSTATUS
XenStub_Pnp_IoCompletion(PDEVICE_OBJECT device_object, PIRP irp, PVOID context)
{
  PKEVENT event = (PKEVENT)context;

  UNREFERENCED_PARAMETER(device_object);

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  if (irp->PendingReturned)
  {
    KeSetEvent(event, IO_NO_INCREMENT, FALSE);
  }

  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));

  return STATUS_MORE_PROCESSING_REQUIRED;
}

#if 0
static NTSTATUS
XenStub_QueueWorkItem(PDEVICE_OBJECT device_object, PIO_WORKITEM_ROUTINE routine, PVOID context)
{
  PIO_WORKITEM work_item;
  NTSTATUS status = STATUS_SUCCESS;

  work_item = IoAllocateWorkItem(device_object);
  IoQueueWorkItem(work_item, routine, DelayedWorkQueue, context);
	
  return status;
}
#endif

static NTSTATUS
XenStub_SendAndWaitForIrp(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status;
  PXENSTUB_DEVICE_DATA xsdd = (PXENSTUB_DEVICE_DATA)device_object->DeviceExtension;
  KEVENT event;

  UNREFERENCED_PARAMETER(device_object);

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  KeInitializeEvent(&event, NotificationEvent, FALSE);

  IoCopyCurrentIrpStackLocationToNext(irp);
  IoSetCompletionRoutine(irp, XenStub_Pnp_IoCompletion, &event, TRUE, TRUE, TRUE);

  status = IoCallDriver(xsdd->lower_do, irp);

  if (status == STATUS_PENDING)
  {
    //KdPrint((__DRIVER_NAME "     waiting ...\n"));
    KeWaitForSingleObject(&event, Executive, KernelMode, FALSE, NULL);
    //KdPrint((__DRIVER_NAME "     ... done\n"));
    status = irp->IoStatus.Status;
  }

  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));

  return status;
}

NTSTATUS
XenStub_Irp_Pnp(PDEVICE_OBJECT device_object, PIRP irp)
{
  PIO_STACK_LOCATION stack;
  NTSTATUS status;
  PXENSTUB_DEVICE_DATA xsdd;

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  xsdd = (PXENSTUB_DEVICE_DATA)device_object->DeviceExtension;

  stack = IoGetCurrentIrpStackLocation(irp);

  switch (stack->MinorFunction)
  {
  case IRP_MN_START_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_START_DEVICE\n"));
    status = XenStub_SendAndWaitForIrp(device_object, irp);
    status = irp->IoStatus.Status = STATUS_SUCCESS;
    IoCompleteRequest(irp, IO_NO_INCREMENT);
    //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));
    return status;

  case IRP_MN_QUERY_STOP_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_QUERY_STOP_DEVICE\n"));
    IoSkipCurrentIrpStackLocation(irp);
    irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_STOP_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_STOP_DEVICE\n"));
    IoSkipCurrentIrpStackLocation(irp);
    irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_CANCEL_STOP_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_CANCEL_STOP_DEVICE\n"));
    IoSkipCurrentIrpStackLocation(irp);
    irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_QUERY_REMOVE_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_QUERY_REMOVE_DEVICE\n"));
    IoSkipCurrentIrpStackLocation(irp);
    irp->IoStatus.Status = STATUS_SUCCESS;
    break;
    
  case IRP_MN_REMOVE_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_REMOVE_DEVICE\n"));
    IoSkipCurrentIrpStackLocation(irp);
    irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_CANCEL_REMOVE_DEVICE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_CANCEL_REMOVE_DEVICE\n"));
    IoSkipCurrentIrpStackLocation(irp);
    //irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_SURPRISE_REMOVAL:
    //KdPrint((__DRIVER_NAME "     IRP_MN_SURPRISE_REMOVAL\n"));
    IoSkipCurrentIrpStackLocation(irp);
    //irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_DEVICE_USAGE_NOTIFICATION:
    //KdPrint((__DRIVER_NAME "     IRP_MN_DEVICE_USAGE_NOTIFICATION\n"));
    IoSkipCurrentIrpStackLocation(irp);
    irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_QUERY_DEVICE_RELATIONS:
    //KdPrint((__DRIVER_NAME "     IRP_MN_QUERY_DEVICE_RELATIONS\n"));
    IoSkipCurrentIrpStackLocation(irp);
    //irp->IoStatus.Information = 0;
    //irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_FILTER_RESOURCE_REQUIREMENTS:
    /* we actually want to do this - no need for interrupt here */
    //KdPrint((__DRIVER_NAME "     IRP_MN_FILTER_RESOURCE_REQUIREMENTS\n"));
    IoSkipCurrentIrpStackLocation(irp);
    //irp->IoStatus.Status = STATUS_SUCCESS;
    break;

  case IRP_MN_QUERY_PNP_DEVICE_STATE:
    //KdPrint((__DRIVER_NAME "     IRP_MN_QUERY_PNP_DEVICE_STATE\n"));
    status = XenStub_SendAndWaitForIrp(device_object, irp);
    irp->IoStatus.Information |= PNP_DEVICE_DONT_DISPLAY_IN_UI;
    status = irp->IoStatus.Status = STATUS_SUCCESS;
    IoCompleteRequest(irp, IO_NO_INCREMENT);
    //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));
    return status;

  default:
    //KdPrint((__DRIVER_NAME "     Unhandled Minor = %d\n", stack->MinorFunction));
    IoSkipCurrentIrpStackLocation(irp);
    break;
  }

  status = IoCallDriver(xsdd->lower_do, irp);

  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));

  return status;
}

NTSTATUS
XenStub_Irp_Power(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status;
  PXENSTUB_DEVICE_DATA xsdd = device_object->DeviceExtension;

  UNREFERENCED_PARAMETER(device_object);
  
  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  PoStartNextPowerIrp(irp);
  IoSkipCurrentIrpStackLocation(irp);

  status =  PoCallDriver (xsdd->lower_do, irp);
  
  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));

  return status;
}

static NTSTATUS
XenStub_AddDevice(PDRIVER_OBJECT DriverObject, PDEVICE_OBJECT PhysicalDeviceObject)
{
  NTSTATUS status;
  PDEVICE_OBJECT fdo = NULL;
  PXENSTUB_DEVICE_DATA xsdd;

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  status = IoCreateDevice(DriverObject,
    sizeof(XENSTUB_DEVICE_DATA),
    NULL,
    FILE_DEVICE_NULL,
    FILE_DEVICE_SECURE_OPEN,
    FALSE,
    &fdo);

  if (!NT_SUCCESS(status))
  {
    //KdPrint((__DRIVER_NAME "     IoCreateDevice failed 0x%08x\n", status));
    return status;
  }

  xsdd = (PXENSTUB_DEVICE_DATA)fdo->DeviceExtension;

  RtlZeroMemory(xsdd, sizeof(XENSTUB_DEVICE_DATA));

  xsdd->fdo = fdo;
  xsdd->pdo = PhysicalDeviceObject;
  xsdd->lower_do = IoAttachDeviceToDeviceStack(fdo, PhysicalDeviceObject);
  if(xsdd->lower_do == NULL) {
    IoDeleteDevice(fdo);
    return STATUS_NO_SUCH_DEVICE;
  }
  
  fdo->Flags &= ~DO_DEVICE_INITIALIZING;

  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__"\n"));
  return status;
}

NTSTATUS
XenStub_Pass(PDEVICE_OBJECT device_object, PIRP irp)
{
  NTSTATUS status;
  PIO_STACK_LOCATION stack;
  PXENSTUB_DEVICE_DATA xsdd = device_object->DeviceExtension;
  
  FUNCTION_ENTER();

  UNREFERENCED_PARAMETER(device_object);

  stack = IoGetCurrentIrpStackLocation(irp);
  //KdPrint((__DRIVER_NAME "     Minor = %d\n", stack->MinorFunction));
  IoSkipCurrentIrpStackLocation(irp);
  status = IoCallDriver(xsdd->lower_do, irp);

  FUNCTION_EXIT();
  
  return status;
}


NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
  NTSTATUS status = STATUS_SUCCESS;

  UNREFERENCED_PARAMETER(RegistryPath);

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  DriverObject->DriverExtension->AddDevice = XenStub_AddDevice;
  DriverObject->MajorFunction[IRP_MJ_PNP] = XenStub_Irp_Pnp;
  DriverObject->MajorFunction[IRP_MJ_POWER] = XenStub_Irp_Power;
  DriverObject->MajorFunction[IRP_MJ_CREATE] = XenStub_Pass;
  DriverObject->MajorFunction[IRP_MJ_CLOSE] = XenStub_Pass;
  DriverObject->MajorFunction[IRP_MJ_CLEANUP] = XenStub_Pass;
  DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = XenStub_Pass;
  DriverObject->MajorFunction[IRP_MJ_READ] = XenStub_Pass;
  DriverObject->MajorFunction[IRP_MJ_WRITE] = XenStub_Pass;
  DriverObject->MajorFunction[IRP_MJ_SYSTEM_CONTROL] = XenStub_Pass;

  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));

  return status;
}