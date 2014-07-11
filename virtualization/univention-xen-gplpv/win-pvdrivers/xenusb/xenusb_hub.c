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

#include "xenusb.h"
#include <stdlib.h>
#include <usbioctl.h>

typedef struct _USB_START_FAILDATA {
  ULONG LengthInBytes;
  NTSTATUS NtStatus;
  USBD_STATUS UsbdStatus;
  ULONG ConnectStatus;
  UCHAR DriverData[4];
} USB_START_FAILDATA, *PUSB_START_FAILDATA;

#pragma warning(disable: 4127) // conditional expression is constant

static EVT_WDF_DEVICE_D0_ENTRY XenUsbHub_EvtDeviceD0Entry;
static EVT_WDF_DEVICE_D0_EXIT XenUsbHub_EvtDeviceD0Exit;
static EVT_WDF_DEVICE_PREPARE_HARDWARE XenUsbHub_EvtDevicePrepareHardware;
static EVT_WDF_DEVICE_RELEASE_HARDWARE XenUsbHub_EvtDeviceReleaseHardware;
static EVT_WDF_DEVICE_USAGE_NOTIFICATION XenUsbHub_EvtDeviceUsageNotification;
static EVT_WDF_TIMER XenUsbHub_HubInterruptTimer;
static EVT_WDF_IO_QUEUE_IO_INTERNAL_DEVICE_CONTROL XenUsbHub_EvtIoInternalDeviceControl;
static EVT_WDF_IO_QUEUE_IO_DEVICE_CONTROL XenUsbHub_EvtIoDeviceControl;
static EVT_WDF_IO_QUEUE_IO_DEFAULT XenUsbHub_EvtIoDefault;
static EVT_WDFDEVICE_WDM_IRP_PREPROCESS XenUsbHub_EvtDeviceWdmIrpPreprocessQUERY_INTERFACE;

static USB_BUSIFFN_CREATE_USB_DEVICE XenUsbHub_UBIH_CreateUsbDevice;
static USB_BUSIFFN_CREATE_USB_DEVICE_EX XenUsbHub_UBIH_CreateUsbDeviceEx;
static USB_BUSIFFN_CREATE_USB_DEVICE_V7 XenUsbHub_UBIH_CreateUsbDeviceV7;
static USB_BUSIFFN_INITIALIZE_USB_DEVICE XenUsbHub_UBIH_InitializeUsbDevice;
static USB_BUSIFFN_GET_USB_DESCRIPTORS XenUsbHub_UBIH_GetUsbDescriptors;
static USB_BUSIFFN_REMOVE_USB_DEVICE XenUsbHub_UBIH_RemoveUsbDevice;
static USB_BUSIFFN_RESTORE_DEVICE XenUsbHub_UBIH_RestoreUsbDevice;
static USB_BUSIFFN_GET_POTRTHACK_FLAGS XenUsbHub_UBIH_GetPortHackFlags;
static USB_BUSIFFN_GET_DEVICE_INFORMATION XenUsbHub_UBIH_QueryDeviceInformation;
static USB_BUSIFFN_GET_CONTROLLER_INFORMATION XenUsbHub_UBIH_GetControllerInformation;
static USB_BUSIFFN_CONTROLLER_SELECTIVE_SUSPEND XenUsbHub_UBIH_ControllerSelectiveSuspend;
static USB_BUSIFFN_GET_EXTENDED_HUB_INFO XenUsbHub_UBIH_GetExtendedHubInformation;
static USB_BUSIFFN_GET_ROOTHUB_SYM_NAME XenUsbHub_UBIH_GetRootHubSymbolicName;
static USB_BUSIFFN_GET_DEVICE_BUSCONTEXT XenUsbHub_UBIH_GetDeviceBusContext;
static USB_BUSIFFN_INITIALIZE_20HUB XenUsbHub_UBIH_Initialize20Hub;
static USB_BUSIFFN_ROOTHUB_INIT_NOTIFY XenUsbHub_UBIH_RootHubInitNotification;
static USB_BUSIFFN_FLUSH_TRANSFERS XenUsbHub_UBIH_FlushTransfers;
static USB_BUSIFFN_SET_DEVHANDLE_DATA XenUsbHub_UBIH_SetDeviceHandleData;
static USB_BUSIFFN_INITIALIZE_USB_DEVICE_EX XenUsbHub_UBIH_InitializeUsbDeviceEx;
static USB_BUSIFFN_IS_ROOT XenUsbHub_UBIH_HubIsRoot;
static USB_BUSIFFN_TEST_POINT XenUsbHub_UBIH_HubTestPoint;
static USB_BUSIFFN_GET_DEVICE_PERFORMANCE_INFO XenUsbHub_UBIH_GetDevicePerformanceInfo;
static USB_BUSIFFN_WAIT_ASYNC_POWERUP XenUsbHub_UBIH_WaitAsyncPowerUp;
static USB_BUSIFFN_GET_DEVICE_ADDRESS XenUsbHub_UBIH_GetDeviceAddress;
static USB_BUSIFFN_REF_DEVICE_HANDLE XenUsbHub_UBIH_RefDeviceHandle;
static USB_BUSIFFN_DEREF_DEVICE_HANDLE XenUsbHub_UBIH_DerefDeviceHandle;
static USB_BUSIFFN_SET_DEVICE_HANDLE_IDLE_READY_STATE XenUsbHub_UBIH_SetDeviceHandleIdleReadyState;
static USB_BUSIFFN_GET_CONTAINER_ID_FOR_PORT XenUsbHub_UBIH_GetContainerIdForPort;
static USB_BUSIFFN_SET_CONTAINER_ID_FOR_PORT XenUsbHub_UBIH_SetContainerIdForPort;
static USB_BUSIFFN_ABORT_ALL_DEVICE_PIPES XenUsbHub_UBIH_AbortAllDevicePipes;
static USB_BUSIFFN_SET_DEVICE_ERRATA_FLAG XenUsbHub_UBIH_SetDeviceErrataFlag;
static USB_BUSIFFN_ACQUIRE_SEMAPHORE XenUsbHub_UBIH_AcquireBusSemaphore;
static USB_BUSIFFN_RELEASE_SEMAPHORE XenUsbHub_UBIH_ReleaseBusSemaphore;
static USB_BUSIFFN_CALC_PIPE_BANDWIDTH XenUsbHub_UBIH_CaculatePipeBandwidth;
static USB_BUSIFFN_SET_BUS_WAKE_MODE XenUsbHub_UBIH_SetBusSystemWakeMode;
static USB_BUSIFFN_SET_DEVICE_FLAG XenUsbHub_UBIH_SetDeviceFlag;





static VOID
XenUsbHub_EvtIoDefault(
  WDFQUEUE queue,
  WDFREQUEST request)
{
  NTSTATUS status;
  WDF_REQUEST_PARAMETERS parameters;

  FUNCTION_ENTER();

  UNREFERENCED_PARAMETER(queue);

  status = STATUS_UNSUCCESSFUL;

  WDF_REQUEST_PARAMETERS_INIT(&parameters);
  WdfRequestGetParameters(request, &parameters);

  switch (parameters.Type)
  {
  case WdfRequestTypeCreate:
    FUNCTION_MSG("WdfRequestTypeCreate\n");
    break;
  case WdfRequestTypeClose:
    FUNCTION_MSG("WdfRequestTypeClose\n");
    break;
  case WdfRequestTypeRead:
    FUNCTION_MSG("WdfRequestTypeRead\n");
    break;
  case WdfRequestTypeWrite:
    FUNCTION_MSG("WdfRequestTypeWrite\n");
    break;
  case WdfRequestTypeDeviceControl:
    FUNCTION_MSG("WdfRequestTypeDeviceControl\n");
    
    break;
  case WdfRequestTypeDeviceControlInternal:
    FUNCTION_MSG("WdfRequestTypeDeviceControlInternal\n");
    break;
  default:
    FUNCTION_MSG("Unknown type %x\n", parameters.Type);
    break;
  }
  FUNCTION_MSG("Calling WdfRequestComplete with status = %08x\n");
  WdfRequestComplete(request, status);  

  FUNCTION_EXIT();
}

static NTSTATUS
XenUsbHub_BusIrpCompletionRoutine(
  PDEVICE_OBJECT device_object,
  PIRP irp,
  PVOID context)
{
  WDFREQUEST request = context;

  UNREFERENCED_PARAMETER(device_object);

  FUNCTION_ENTER();

  FUNCTION_MSG("Calling WdfRequestComplete with status = %08x\n");
  WdfRequestCompleteWithInformation(request, irp->IoStatus.Status, irp->IoStatus.Information);
  IoFreeIrp(irp);

  FUNCTION_EXIT();

  return STATUS_MORE_PROCESSING_REQUIRED;
}

static VOID
XenUsbHub_EvtIoDeviceControl(
  WDFQUEUE queue,
  WDFREQUEST request,
  size_t output_buffer_length,
  size_t input_buffer_length,
  ULONG io_control_code)
{
  NTSTATUS status;
  //WDFDEVICE device = WdfIoQueueGetDevice(queue);
  //PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  //WDF_REQUEST_PARAMETERS wrp;
  //PURB urb;
  //xenusb_device_t *usb_device;

  UNREFERENCED_PARAMETER(queue);
  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);

  FUNCTION_ENTER();

  status = STATUS_UNSUCCESSFUL;

  //WDF_REQUEST_PARAMETERS_INIT(&wrp);
  //WdfRequestGetParameters(request, &wrp);

  // these are in api\usbioctl.h
  switch(io_control_code)
  {
  case IOCTL_USB_GET_NODE_INFORMATION:
    FUNCTION_MSG("IOCTL_USB_GET_NODE_INFORMATION\n");
    break;
  case IOCTL_USB_GET_NODE_CONNECTION_INFORMATION:
    FUNCTION_MSG("IOCTL_USB_GET_NODE_CONNECTION_INFORMATION\n");
    break;
  case IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION:
    FUNCTION_MSG("IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION\n");
    break;
  case IOCTL_USB_GET_NODE_CONNECTION_NAME:
    FUNCTION_MSG("IOCTL_USB_GET_NODE_CONNECTION_NAME\n");
    break;
  case IOCTL_USB_DIAG_IGNORE_HUBS_ON:
    FUNCTION_MSG("IOCTL_USB_DIAG_IGNORE_HUBS_ON\n");
    break;
  case IOCTL_USB_DIAG_IGNORE_HUBS_OFF:
    FUNCTION_MSG("IOCTL_USB_DIAG_IGNORE_HUBS_OFF\n");
    break;
  case IOCTL_USB_GET_NODE_CONNECTION_DRIVERKEY_NAME:
    FUNCTION_MSG("IOCTL_USB_GET_NODE_CONNECTION_DRIVERKEY_NAME\n");
    break;
  case IOCTL_USB_GET_HUB_CAPABILITIES:
    FUNCTION_MSG("IOCTL_USB_GET_HUB_CAPABILITIES\n");
    break;
  case IOCTL_USB_HUB_CYCLE_PORT:
    FUNCTION_MSG("IOCTL_USB_HUB_CYCLE_PORT\n");
    break;
  case IOCTL_USB_GET_NODE_CONNECTION_ATTRIBUTES:
    FUNCTION_MSG("IOCTL_USB_GET_NODE_CONNECTION_ATTRIBUTES\n");
    break;
  case IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX:
    FUNCTION_MSG("IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX\n");
    break;
  case IOCTL_GET_HCD_DRIVERKEY_NAME:
    FUNCTION_MSG("IOCTL_GET_HCD_DRIVERKEY_NAME (***)\n");
    break;
  default:
    FUNCTION_MSG("Unknown IOCTL %08x\n", io_control_code);
    break;
  }
  FUNCTION_MSG("Calling WdfRequestComplete with status = %08x\n");
  WdfRequestComplete(request, status);

  FUNCTION_EXIT();
}

static VOID
XenUsbHub_EvtIoInternalDeviceControl(
  WDFQUEUE queue,
  WDFREQUEST request,
  size_t output_buffer_length,
  size_t input_buffer_length,
  ULONG io_control_code)
{
  NTSTATUS status;
  WDFDEVICE device = WdfIoQueueGetDevice(queue);
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  WDF_REQUEST_PARAMETERS wrp;
  PURB urb;
#if (NTDDI_VERSION >= NTDDI_VISTA)
  PUSB_START_FAILDATA usfd;
  PHUB_DEVICE_CONFIG_INFO hdci;
  PUSB_TOPOLOGY_ADDRESS uta;
  PUSB_HUB_NAME uhn;
  size_t length;
#endif
  xenusb_device_t *usb_device;

  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);

  //FUNCTION_ENTER();

  status = STATUS_UNSUCCESSFUL;

  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  WdfRequestGetParameters(request, &wrp);

  // these are in api\usbioctl.h
  switch(io_control_code)
  {
  case IOCTL_INTERNAL_USB_CYCLE_PORT:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_CYCLE_PORT\n");
    break;
  case IOCTL_INTERNAL_USB_ENABLE_PORT:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_ENABLE_PORT\n");
    break;
  case IOCTL_INTERNAL_USB_GET_BUS_INFO:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_BUS_INFO\n");
    break;
  case IOCTL_INTERNAL_USB_GET_CONTROLLER_NAME:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_CONTROLLER_NAME\n");
    break;
  case IOCTL_INTERNAL_USB_GET_HUB_COUNT:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_HUB_COUNT\n");
    FUNCTION_MSG("Count before increment = %p\n", *(PULONG)wrp.Parameters.Others.Arg1);
    (*(PULONG)wrp.Parameters.Others.Arg1)++;
    status = STATUS_SUCCESS;
    break;
#if (NTDDI_VERSION >= NTDDI_VISTA)
  case IOCTL_INTERNAL_USB_GET_HUB_NAME:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_HUB_NAME (hub)\n");
    status = WdfRequestRetrieveOutputBuffer(request, FIELD_OFFSET(USB_HUB_NAME, HubName) + 18, (PVOID *)&uhn, &length);
    if (NT_SUCCESS(status))
    {
      /* not sure this is correct... it's not the full symbolic name */
      uhn->ActualLength = sizeof(USB_HUB_NAME);
      RtlStringCbCopyW(uhn->HubName, length - FIELD_OFFSET(USB_HUB_NAME, HubName), L"ROOT_HUB");
      status = STATUS_SUCCESS;
    }
    break;
#endif
  case IOCTL_INTERNAL_USB_GET_PORT_STATUS:
    //FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_PORT_STATUS\n");
    *(PULONG)wrp.Parameters.Others.Arg1 = USBD_PORT_ENABLED | USBD_PORT_CONNECTED; /* enabled and connected */
    status = STATUS_SUCCESS;
    break;
  case IOCTL_INTERNAL_USB_GET_ROOTHUB_PDO:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_ROOTHUB_PDO\n");
    FUNCTION_MSG("WdfDeviceWdmGetPhysicalDevice(device) = %p\n", WdfDeviceWdmGetPhysicalDevice(device));
    //FUNCTION_MSG("IoGetAttachedDevice(WdfDeviceWdmGetDeviceObject(device)) = %p\n", IoGetAttachedDevice(WdfDeviceWdmGetDeviceObject(device));
    *(PVOID *)wrp.Parameters.Others.Arg1 = WdfDeviceWdmGetPhysicalDevice(device);
    //*(PVOID *)wrp.Parameters.Others.Arg2 = IoGetAttachedDevice(WdfDeviceWdmGetDeviceObject(device));
    *(PVOID *)wrp.Parameters.Others.Arg2 = IoGetAttachedDevice(WdfDeviceWdmGetDeviceObject(xupdd->wdf_device_bus_fdo));
    status = STATUS_SUCCESS;
    break;
  case IOCTL_INTERNAL_USB_RESET_PORT:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_RESET_PORT\n");
    break;
  case IOCTL_INTERNAL_USB_SUBMIT_IDLE_NOTIFICATION:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_SUBMIT_IDLE_NOTIFICATION\n");
    break;
  case IOCTL_INTERNAL_USB_SUBMIT_URB:
    //FUNCTION_MSG("IOCTL_INTERNAL_USB_SUBMIT_URB\n");
    urb = (PURB)wrp.Parameters.Others.Arg1;
    ASSERT(urb);
    usb_device = urb->UrbHeader.UsbdDeviceHandle;
    if (!usb_device)
      usb_device = xupdd->usb_device;
    WdfRequestForwardToIoQueue(request, usb_device->urb_queue);
    return;
  case IOCTL_INTERNAL_USB_GET_DEVICE_HANDLE:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_DEVICE_HANDLE (returning %p)\n", xupdd->usb_device);
    *(PVOID *)wrp.Parameters.Others.Arg1 = xupdd->usb_device;
    status = STATUS_SUCCESS;
    break;
#if (NTDDI_VERSION >= NTDDI_VISTA)
  case IOCTL_INTERNAL_USB_GET_DEVICE_HANDLE_EX: /* incomplete probably */
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_DEVICE_HANDLE_EX (returning %p)\n", xupdd->usb_device);
    *(PVOID *)wrp.Parameters.Others.Arg1 = xupdd->usb_device;
    *(ULONG_PTR *)wrp.Parameters.Others.Arg2 = (ULONG_PTR)0x12345678;
    status = STATUS_SUCCESS;
    break;
  case IOCTL_INTERNAL_USB_GET_TOPOLOGY_ADDRESS:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_TOPOLOGY_ADDRESS\n");
    uta = (PUSB_TOPOLOGY_ADDRESS)wrp.Parameters.Others.Arg1;
    uta->PciBusNumber = 0;
    uta->PciDeviceNumber = 0;
    uta->PciFunctionNumber = 0;
    uta->RootHubPortNumber = 0;
    uta->HubPortNumber[1] = 0;
    uta->HubPortNumber[2] = 0;
    uta->HubPortNumber[3] = 0;
    uta->HubPortNumber[4] = 0;
    status = STATUS_SUCCESS;
    break;
  case IOCTL_INTERNAL_USB_GET_DEVICE_CONFIG_INFO:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_GET_DEVICE_CONFIG_INFO\n");
    hdci = (PHUB_DEVICE_CONFIG_INFO)wrp.Parameters.Others.Arg1;
    hdci->Version = 1;
    hdci->Length = 192;
    hdci->HubFlags.ul = 0;
    hdci->HubFlags.HubIsHighSpeedCapable = 1;
    hdci->HubFlags.HubIsHighSpeed = 1;
    hdci->HubFlags.HubIsMultiTtCapable = 0;
    hdci->HubFlags.HubIsMultiTt = 0;
    hdci->HubFlags.HubIsRoot = 1;
    hdci->HubFlags.HubIsArmedWakeOnConnect = 1;
    hdci->HubFlags.HubIsBusPowered = 1;
    //hdci->HardwareIds = ?;
    //hdci->CompatibleIds = ?;
    //hdci->DeviceDescription = ?;
    status = STATUS_SUCCESS;
    break;
  case IOCTL_INTERNAL_USB_RECORD_FAILURE:
    FUNCTION_MSG("IOCTL_INTERNAL_USB_RECORD_FAILURE\n");
    usfd = (PUSB_START_FAILDATA)wrp.Parameters.Others.Arg1;
    FUNCTION_MSG(" LengthInBytes = %d\n", usfd->LengthInBytes);
    FUNCTION_MSG(" NtStatus = %08x\n", usfd->NtStatus);
    FUNCTION_MSG(" UsbdStatus = %08x\n", usfd->UsbdStatus);
    FUNCTION_MSG(" ConnectStatus = %08x\n", usfd->ConnectStatus);
    status = STATUS_SUCCESS;
    break;  
#endif
  default:
    FUNCTION_MSG("Unknown IOCTL %08x\n", io_control_code);
    break;
  }  

  if (status != STATUS_SUCCESS)
    FUNCTION_MSG("Calling WdfRequestComplete with status = %08x\n", status);
  WdfRequestComplete(request, status);

  //FUNCTION_EXIT();
}

static NTSTATUS
XenUsbHub_EvtDeviceD0Entry(WDFDEVICE device, WDF_POWER_DEVICE_STATE previous_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  DECLARE_CONST_UNICODE_STRING(symbolicname_name, L"SymbolicName");
  WDFSTRING symbolicname_value_wdfstring;
  WDFKEY device_key;
  UNICODE_STRING symbolicname_value;
  
  UNREFERENCED_PARAMETER(device);

  FUNCTION_ENTER();

  switch (previous_state)
  {
  case WdfPowerDeviceD0:
    FUNCTION_MSG("WdfPowerDeviceD1\n");
    break;
  case WdfPowerDeviceD1:
    FUNCTION_MSG("WdfPowerDeviceD1\n");
    break;
  case WdfPowerDeviceD2:
    FUNCTION_MSG("WdfPowerDeviceD2\n");
    break;
  case WdfPowerDeviceD3:
    FUNCTION_MSG("WdfPowerDeviceD3\n");
    break;
  case WdfPowerDeviceD3Final:
    FUNCTION_MSG("WdfPowerDeviceD3Final\n");
    break;
  case WdfPowerDevicePrepareForHibernation:
    FUNCTION_MSG("WdfPowerDevicePrepareForHibernation\n");
    break;  
  default:
    FUNCTION_MSG("Unknown WdfPowerDevice state %d\n", previous_state);
    break;  
  }

  /* USB likes to have a registry key with the symbolic link name in it. Have to wait until D0Entry as this is the PDO */
  status = WdfStringCreate(NULL, WDF_NO_OBJECT_ATTRIBUTES, &symbolicname_value_wdfstring);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfStringCreate = %08x\n", status);
    return status;
  }
  status = WdfDeviceRetrieveDeviceInterfaceString(device, &GUID_DEVINTERFACE_USB_HUB, NULL, symbolicname_value_wdfstring);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDeviceREtrieveDeviceInterfaceString = %08x\n", status);
    return status;
  }
  WdfStringGetUnicodeString(symbolicname_value_wdfstring, &symbolicname_value);
  FUNCTION_MSG("ROOT_HUB SymbolicName = %S\n", symbolicname_value.Buffer);
  status = WdfDeviceOpenRegistryKey(device, PLUGPLAY_REGKEY_DEVICE, KEY_SET_VALUE, WDF_NO_OBJECT_ATTRIBUTES, &device_key);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDeviceOpenRegistryKey = %08x\n", status);
    return status;
  }
  status = WdfRegistryAssignUnicodeString(device_key, &symbolicname_name, &symbolicname_value);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDeviceOpenRegistryKey = %08x\n", status);
    return status;
  }
  WdfRegistryClose(device_key);
  FUNCTION_EXIT();
  
  return status;
}

static NTSTATUS
XenUsbHub_EvtDeviceD0Exit(WDFDEVICE device, WDF_POWER_DEVICE_STATE target_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  //PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  //PXENUSB_DEVICE_DATA xudd = GetXudd(xupdd->wdf_device_bus_fdo);

  UNREFERENCED_PARAMETER(device);
  
  FUNCTION_ENTER();
  
  switch (target_state)
  {
  case WdfPowerDeviceD0:
    FUNCTION_MSG("WdfPowerDeviceD1\n");
    break;
  case WdfPowerDeviceD1:
    FUNCTION_MSG("WdfPowerDeviceD1\n");
    break;
  case WdfPowerDeviceD2:
    FUNCTION_MSG("WdfPowerDeviceD2\n");
    break;
  case WdfPowerDeviceD3:
    FUNCTION_MSG("WdfPowerDeviceD3\n");
    break;
  case WdfPowerDeviceD3Final:
    FUNCTION_MSG("WdfPowerDeviceD3Final\n");
    break;
  case WdfPowerDevicePrepareForHibernation:
    FUNCTION_MSG("WdfPowerDevicePrepareForHibernation\n");
    break;  
  default:
    FUNCTION_MSG("Unknown WdfPowerDevice state %d\n", target_state);
    break;  
  }
  
  FUNCTION_EXIT();
  
  return status;
}

static NTSTATUS
XenUsbHub_EvtDevicePrepareHardware(WDFDEVICE device, WDFCMRESLIST resources_raw, WDFCMRESLIST resources_translated)
{
  NTSTATUS status = STATUS_SUCCESS;

  UNREFERENCED_PARAMETER(device);
  UNREFERENCED_PARAMETER(resources_raw);
  UNREFERENCED_PARAMETER(resources_translated);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  
  return status;
}

static NTSTATUS
XenUsbHub_EvtDeviceReleaseHardware(WDFDEVICE device, WDFCMRESLIST resources_translated)
{
  NTSTATUS status = STATUS_SUCCESS;
  
  UNREFERENCED_PARAMETER(device);
  UNREFERENCED_PARAMETER(resources_translated);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  
  return status;
}

static VOID
XenUsbHub_EvtDeviceUsageNotification(WDFDEVICE device, WDF_SPECIAL_FILE_TYPE notification_type, BOOLEAN is_in_notification_path)
{
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);

  UNREFERENCED_PARAMETER(xupdd);
  UNREFERENCED_PARAMETER(is_in_notification_path);  

  FUNCTION_ENTER();
  
  switch (notification_type)
  {
  case WdfSpecialFilePaging:
    FUNCTION_MSG("notification_type = Paging, flag = %d\n", is_in_notification_path);
    break;
  case WdfSpecialFileHibernation:
    FUNCTION_MSG("notification_type = Hibernation, flag = %d\n", is_in_notification_path);
    break;
  case WdfSpecialFileDump:
    FUNCTION_MSG("notification_type = Dump, flag = %d\n", is_in_notification_path);
    break;
  default:
    FUNCTION_MSG("notification_type = %d, flag = %d\n", notification_type, is_in_notification_path);
    break;
  }

  FUNCTION_EXIT();  
}

static NTSTATUS
XenUsb_SubmitCompletionRoutine(
  PDEVICE_OBJECT device_object,
  PIRP irp,
  PVOID context)
{
  UNREFERENCED_PARAMETER(device_object);

  FUNCTION_ENTER();
  
  if (irp->PendingReturned)
  {
    KeSetEvent ((PKEVENT)context, IO_NO_INCREMENT, FALSE);
  }

  FUNCTION_EXIT();

  return STATUS_MORE_PROCESSING_REQUIRED;
}

static NTSTATUS
XenUsbHub_UBIH_CreateUsbDevice(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE *DeviceHandle,
  PUSB_DEVICE_HANDLE HubDeviceHandle,
  USHORT PortStatus,
  USHORT PortNumber)
{
  NTSTATUS status = STATUS_SUCCESS;
  xenusb_device_t *usb_device;
  
  UNREFERENCED_PARAMETER(BusContext);  
  UNREFERENCED_PARAMETER(HubDeviceHandle);
  UNREFERENCED_PARAMETER(PortStatus);
  
  FUNCTION_ENTER();

  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("DeviceHandle = %p\n", DeviceHandle);
  FUNCTION_MSG("*DeviceHandle = %p\n", *DeviceHandle);
  FUNCTION_MSG("HubDeviceHandle = %p\n", HubDeviceHandle);
  FUNCTION_MSG("PortStatus = %04X\n", PortStatus);
  FUNCTION_MSG("PortNumber = %d\n", PortNumber);
  usb_device = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_device_t), XENUSB_POOL_TAG);
  if (!usb_device) {
    FUNCTION_EXIT();
    return STATUS_INSUFFICIENT_RESOURCES;
  }
  usb_device->port_number = PortNumber;
  *DeviceHandle = usb_device;  

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_InitializeUsbDevice(
 PVOID BusContext,
 PUSB_DEVICE_HANDLE DeviceHandle)
{
  NTSTATUS status = STATUS_SUCCESS;
  WDFDEVICE device = BusContext;
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  //PXENUSB_DEVICE_DATA xudd = GetXudd(xupdd->wdf_device_bus_fdo);
  WDF_IO_QUEUE_CONFIG queue_config;
  xenusb_device_t *usb_device = DeviceHandle;
  PUCHAR ptr;
  PVOID buf;
  PMDL mdl;
  pvurb_t pvurb; /* this can be local because it never leaves this routine */
  PUSB_DEVICE_DESCRIPTOR device_descriptor;
  PUSB_CONFIGURATION_DESCRIPTOR config_descriptor;
  PUSB_INTERFACE_DESCRIPTOR interface_descriptor;
  PUSB_ENDPOINT_DESCRIPTOR endpoint_descriptor;
  int i, j, k;
  PUSB_DEFAULT_PIPE_SETUP_PACKET setup_packet;
  WDF_MEMORY_DESCRIPTOR pvurb_descriptor;
  WDF_REQUEST_SEND_OPTIONS send_options;
  
  FUNCTION_ENTER();

  FUNCTION_MSG("device = %p\n", device);
  FUNCTION_MSG("usb_device = %p\n", usb_device);
  usb_device->pdo_device = BusContext;
  
  // TODO: get address from freelist and assign it to the device...
  usb_device->address = (UCHAR)get_id_from_freelist(xupdd->dev_id_ss);
  // TODO: get this stuff properly ...
  xupdd->usb_device->device_speed = UsbHighSpeed;
  xupdd->usb_device->device_type = Usb20Device;

  buf = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENUSB_POOL_TAG);
  if (!buf) {
    FUNCTION_MSG("ExAllocatePoolWithTag(buf) failed\n");
    return STATUS_INSUFFICIENT_RESOURCES;
  }
  mdl = IoAllocateMdl(buf, PAGE_SIZE, FALSE, FALSE, NULL);
  if (!mdl) {
    FUNCTION_MSG("IoAllocateMdl(buf) failed\n", status);
    return STATUS_INSUFFICIENT_RESOURCES;
  }
  MmBuildMdlForNonPagedPool(mdl);

  WDF_MEMORY_DESCRIPTOR_INIT_BUFFER(&pvurb_descriptor, &pvurb, sizeof(pvurb));
  WDF_REQUEST_SEND_OPTIONS_INIT(&send_options, WDF_REQUEST_SEND_OPTION_TIMEOUT);
  WDF_REQUEST_SEND_OPTIONS_SET_TIMEOUT(&send_options, WDF_REL_TIMEOUT_IN_SEC(10));

  /* set the address */
  pvurb.req.pipe = LINUX_PIPE_TYPE_CTRL | usb_device->port_number;
  pvurb.req.transfer_flags = 0; 
  pvurb.req.buffer_length = 0;
  setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)pvurb.req.u.ctrl;
  setup_packet->bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
  setup_packet->bmRequestType.Type = BMREQUEST_STANDARD;
  setup_packet->bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
  setup_packet->bRequest = USB_REQUEST_SET_ADDRESS;
  setup_packet->wValue.W = usb_device->address;
  setup_packet->wIndex.W = 0;
  setup_packet->wLength = pvurb.req.buffer_length;
  pvurb.mdl = NULL;
  status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, NULL, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfIoTargetSendInternalIoctlOthersSynchronously(USB_REQUEST_SET_ADDRESS) = %08x\n", status);
    return status;
  }
  FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB status = %08x\n", status);
  FUNCTION_MSG("rsp start_frame = %d\n", pvurb.rsp.start_frame);
  FUNCTION_MSG("rsp status = %d\n", pvurb.rsp.status);
  FUNCTION_MSG("rsp actual_length = %d\n", pvurb.rsp.actual_length);
  FUNCTION_MSG("rsp error_count = %d\n", pvurb.rsp.error_count);

  /* get the device descriptor */
  pvurb.req.pipe = LINUX_PIPE_DIRECTION_IN | LINUX_PIPE_TYPE_CTRL | (usb_device->address << 8) | usb_device->port_number;
  pvurb.req.transfer_flags = 0; 
  pvurb.req.buffer_length = PAGE_SIZE;
  setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)pvurb.req.u.ctrl;
  setup_packet->bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
  setup_packet->bmRequestType.Type = BMREQUEST_STANDARD;
  setup_packet->bmRequestType.Dir = BMREQUEST_DEVICE_TO_HOST;
  setup_packet->bRequest = USB_REQUEST_GET_DESCRIPTOR;
  setup_packet->wValue.LowByte = 0;
  setup_packet->wValue.HiByte = USB_DEVICE_DESCRIPTOR_TYPE; //device descriptor
  setup_packet->wIndex.W = 0;
  setup_packet->wLength = pvurb.req.buffer_length;
  pvurb.mdl = mdl;
  status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, NULL, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfIoTargetSendInternalIoctlOthersSynchronously(USB_REQUEST_GET_DESCRIPTOR, USB_DEVICE_DESCRIPTOR_TYPE) = %08x\n", status);
    return status;
  }
  FUNCTION_MSG("rsp start_frame = %d\n", pvurb.rsp.start_frame);
  FUNCTION_MSG("rsp status = %d\n", pvurb.rsp.status);
  FUNCTION_MSG("rsp actual_length = %d\n", pvurb.rsp.actual_length);
  FUNCTION_MSG("rsp error_count = %d\n", pvurb.rsp.error_count);
  ptr = buf;
  device_descriptor = (PUSB_DEVICE_DESCRIPTOR)ptr;
  FUNCTION_MSG("bLength = %d\n", device_descriptor->bLength);
  FUNCTION_MSG("bNumConfigurations = %d\n", device_descriptor->bNumConfigurations);
  memcpy(&usb_device->device_descriptor, device_descriptor, device_descriptor->bLength);
  usb_device->configs = ExAllocatePoolWithTag(NonPagedPool, sizeof(PVOID) * device_descriptor->bNumConfigurations, XENUSB_POOL_TAG);
  if (!usb_device->configs) {
    FUNCTION_MSG("ExAllocatePoolWithTag(usb_device->configs) failed\n");
    return STATUS_INSUFFICIENT_RESOURCES;
  }
  FUNCTION_MSG("bLength = %d\n", device_descriptor->bLength);
  FUNCTION_MSG("bDescriptorType = %d\n", device_descriptor->bDescriptorType);
  FUNCTION_MSG("bcdUSB = %04x\n", device_descriptor->bcdUSB);
  FUNCTION_MSG("bDeviceClass = %02x\n", device_descriptor->bDeviceClass);
  FUNCTION_MSG("bDeviceSubClass = %02x\n", device_descriptor->bDeviceSubClass);
  FUNCTION_MSG("bDeviceProtocol = %02x\n", device_descriptor->bDeviceProtocol);
  FUNCTION_MSG("idVendor = %04x\n", device_descriptor->idVendor);
  FUNCTION_MSG("idProduct = %04x\n", device_descriptor->idProduct);
  FUNCTION_MSG("bcdDevice = %04x\n", device_descriptor->bcdDevice);
  FUNCTION_MSG("bNumConfigurations = %04x\n", device_descriptor->bNumConfigurations);

  /* get the config descriptor */
  for (i = 0; i < device_descriptor->bNumConfigurations; i++)
  {
    pvurb.req.pipe = LINUX_PIPE_DIRECTION_IN | LINUX_PIPE_TYPE_CTRL | (usb_device->address << 8) | usb_device->port_number;
    pvurb.req.transfer_flags = 0; 
    pvurb.req.buffer_length = PAGE_SIZE;
    setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)pvurb.req.u.ctrl;
    setup_packet->bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
    setup_packet->bmRequestType.Type = BMREQUEST_STANDARD;
    setup_packet->bmRequestType.Dir = BMREQUEST_DEVICE_TO_HOST;
    setup_packet->bRequest = USB_REQUEST_GET_DESCRIPTOR;
    setup_packet->wValue.LowByte = (UCHAR)(i + 1);
    setup_packet->wValue.HiByte = USB_CONFIGURATION_DESCRIPTOR_TYPE; //device descriptor
    setup_packet->wIndex.W = 0;
    setup_packet->wLength = pvurb.req.buffer_length;
    pvurb.mdl = mdl;
    status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, NULL, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
    if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("WdfIoTargetSendInternalIoctlOthersSynchronously(USB_REQUEST_GET_DESCRIPTOR, USB_CONFIGURATION_DESCRIPTOR_TYPE) = %08x\n", status);
      return status;
    }
    FUNCTION_MSG("rsp start_frame = %d\n", pvurb.rsp.start_frame);
    FUNCTION_MSG("rsp status = %d\n", pvurb.rsp.status);
    FUNCTION_MSG("rsp actual_length = %d\n", pvurb.rsp.actual_length);
    FUNCTION_MSG("rsp error_count = %d\n", pvurb.rsp.error_count);
    ptr = buf;
    config_descriptor = (PUSB_CONFIGURATION_DESCRIPTOR)ptr;
    FUNCTION_MSG("Config %d\n", i);
    FUNCTION_MSG(" bLength = %d\n", config_descriptor->bLength);
    FUNCTION_MSG(" bDescriptorType = %d\n", config_descriptor->bDescriptorType);
    FUNCTION_MSG(" wTotalLength = %d\n", config_descriptor->wTotalLength);
    FUNCTION_MSG(" bNumInterfaces = %d\n", config_descriptor->bNumInterfaces);
    FUNCTION_MSG(" iConfiguration = %d\n", config_descriptor->iConfiguration);
    FUNCTION_MSG(" bConfigurationValue = %d\n", config_descriptor->bConfigurationValue);
    FUNCTION_MSG(" bmAttributes = %02x\n", config_descriptor->bmAttributes);
    FUNCTION_MSG(" MaxPower = %d\n", config_descriptor->MaxPower);
    usb_device->configs[i] = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_config_t) + sizeof(PVOID) * config_descriptor->bNumInterfaces, XENUSB_POOL_TAG);
    if (!usb_device->configs) {
      FUNCTION_MSG("ExAllocatePoolWithTag(usb_device->configs[i]) failed\n");
      return STATUS_INSUFFICIENT_RESOURCES;
    }
    usb_device->configs[i]->device = usb_device;
    memcpy(&usb_device->configs[i]->config_descriptor, config_descriptor, sizeof(USB_CONFIGURATION_DESCRIPTOR));
    usb_device->configs[i]->config_descriptor_all = ExAllocatePoolWithTag(NonPagedPool, config_descriptor->wTotalLength, XENUSB_POOL_TAG);
    memcpy(usb_device->configs[i]->config_descriptor_all, config_descriptor, config_descriptor->wTotalLength);
    ptr += config_descriptor->bLength;
    j = 0;
    while (j < config_descriptor->bNumInterfaces)
    {
      interface_descriptor = (PUSB_INTERFACE_DESCRIPTOR)ptr;
      FUNCTION_MSG("  Interface %d\n", j);
      FUNCTION_MSG("   bLength = %d\n", interface_descriptor->bLength);
      FUNCTION_MSG("   bDescriptorType = %d\n", interface_descriptor->bDescriptorType);
      FUNCTION_MSG("   bInterfaceNumber = %d\n", interface_descriptor->bInterfaceNumber);
      FUNCTION_MSG("   bAlternateSetting = %d\n", interface_descriptor->bAlternateSetting);
      FUNCTION_MSG("   bNumEndpoints = %d\n", interface_descriptor->bNumEndpoints);
      FUNCTION_MSG("   bInterfaceClass = %d\n", interface_descriptor->bInterfaceClass);
      FUNCTION_MSG("   bInterfaceSubClass = %d\n", interface_descriptor->bInterfaceSubClass);
      FUNCTION_MSG("   bInterfaceProtocol = %d\n", interface_descriptor->bInterfaceProtocol);
      FUNCTION_MSG("   iInterface = %d\n", interface_descriptor->iInterface);
      ptr += interface_descriptor->bLength;
      usb_device->configs[i]->interfaces[j] = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_interface_t) + sizeof(PVOID) * interface_descriptor->bNumEndpoints, XENUSB_POOL_TAG);
      usb_device->configs[i]->interfaces[j]->config = usb_device->configs[i];
      memcpy(&usb_device->configs[i]->interfaces[j]->interface_descriptor, interface_descriptor, sizeof(USB_INTERFACE_DESCRIPTOR));
      k = 0;
      while (k < interface_descriptor->bNumEndpoints)
      {
        endpoint_descriptor = (PUSB_ENDPOINT_DESCRIPTOR)ptr;
        if (endpoint_descriptor->bDescriptorType != 5)
        {
          FUNCTION_MSG("   Unknown bDescriptorType %d found length = %d\n", endpoint_descriptor->bDescriptorType, endpoint_descriptor->bLength);
          ptr += endpoint_descriptor->bLength;
          continue;
        }

        FUNCTION_MSG("   Endpoint %d\n", k);
        FUNCTION_MSG("    bLength = %d\n", endpoint_descriptor->bLength);
        FUNCTION_MSG("    bDescriptorType = %d\n", endpoint_descriptor->bDescriptorType);
        FUNCTION_MSG("    bEndpointAddress = %02x\n", endpoint_descriptor->bEndpointAddress);
        FUNCTION_MSG("    bmAttributes = %02x\n", endpoint_descriptor->bmAttributes);
        FUNCTION_MSG("    wMaxPacketSize = %d\n", endpoint_descriptor->wMaxPacketSize);
        FUNCTION_MSG("    bInterval = %d\n", endpoint_descriptor->bInterval);
        ptr += endpoint_descriptor->bLength;
        usb_device->configs[i]->interfaces[j]->endpoints[k] = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_endpoint_t), XENUSB_POOL_TAG);
        usb_device->configs[i]->interfaces[j]->endpoints[k]->interface = usb_device->configs[i]->interfaces[j];
        usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value = (usb_device->address << 8) | usb_device->port_number;
        /* linux uses nonstandard endpoint type identifiers... */
        switch(endpoint_descriptor->bmAttributes & USB_ENDPOINT_TYPE_MASK)
        {
        case USB_ENDPOINT_TYPE_CONTROL:
          usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value |= LINUX_PIPE_TYPE_CTRL;
          break;
        case USB_ENDPOINT_TYPE_ISOCHRONOUS:
          usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value |= LINUX_PIPE_TYPE_ISOC;
          break;
        case USB_ENDPOINT_TYPE_BULK:
          usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value |= LINUX_PIPE_TYPE_BULK;
          break;
        case USB_ENDPOINT_TYPE_INTERRUPT:
          usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value |= LINUX_PIPE_TYPE_INTR;
          break;
        }
        usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value |= (endpoint_descriptor->bEndpointAddress & 0x80);
        usb_device->configs[i]->interfaces[j]->endpoints[k]->pipe_value |= (endpoint_descriptor->bEndpointAddress & 0x0F) << 15;
        memcpy(&usb_device->configs[i]->interfaces[j]->endpoints[k]->endpoint_descriptor, endpoint_descriptor, sizeof(USB_ENDPOINT_DESCRIPTOR));
        k++;
      }
      j++;
    }
  }
  ExFreePoolWithTag(buf, XENUSB_POOL_TAG);

  usb_device->active_config = usb_device->configs[0];
  usb_device->active_interface = usb_device->configs[0]->interfaces[0];

  WDF_IO_QUEUE_CONFIG_INIT(&queue_config, WdfIoQueueDispatchParallel); // should this be serial?
  queue_config.EvtIoInternalDeviceControl = XenUsb_EvtIoInternalDeviceControl_DEVICE_SUBMIT_URB;
  queue_config.PowerManaged = TRUE; /* power managed queue for SUBMIT_URB */
  status = WdfIoQueueCreate(device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, &usb_device->urb_queue);
  if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("Error creating urb_queue 0x%x\n", status);
      return status;
  }
  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_GetUsbDescriptors(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PUCHAR DeviceDescriptorBuffer,
  PULONG DeviceDescriptorBufferLength,
  PUCHAR ConfigDescriptorBuffer,
  PULONG ConfigDescriptorBufferLength
  )
{
  NTSTATUS status = STATUS_SUCCESS;
  xenusb_device_t *usb_device = DeviceHandle;
  xenusb_config_t *usb_config;
  PUCHAR ptr;

  UNREFERENCED_PARAMETER(BusContext);  

  FUNCTION_ENTER();

  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("DeviceHandle = %p\n", DeviceHandle);
  FUNCTION_MSG("DeviceDescriptorBuffer = %p\n", DeviceDescriptorBuffer);
  FUNCTION_MSG("DeviceDescriptorBufferLength = %d\n", *DeviceDescriptorBufferLength);
  FUNCTION_MSG("ConfigDescriptorBuffer = %p\n", ConfigDescriptorBuffer);
  FUNCTION_MSG("ConfigDescriptorBufferLength = %d\n", *ConfigDescriptorBufferLength);
  
  memcpy(DeviceDescriptorBuffer, &usb_device->device_descriptor, usb_device->device_descriptor.bLength);
  *DeviceDescriptorBufferLength = usb_device->device_descriptor.bLength;
  
  usb_config = usb_device->active_config;
  ptr = ConfigDescriptorBuffer;
  memcpy(ptr, usb_config->config_descriptor_all, min(usb_config->config_descriptor.wTotalLength, *ConfigDescriptorBufferLength));
  *ConfigDescriptorBufferLength = ((PUSB_CONFIGURATION_DESCRIPTOR)ConfigDescriptorBuffer)->wTotalLength;

#if 0
  ptr += sizeof(USB_CONFIGURATION_DESCRIPTOR);
  // why was this here? ((PUSB_CONFIGURATION_DESCRIPTOR)ConfigDescriptorBuffer)->wTotalLength += 1;

  for (i = 0; i < usb_config->config_descriptor.bNumInterfaces; i++)
  {
    memcpy(ptr, &usb_config->interfaces[i]->interface_descriptor, sizeof(USB_INTERFACE_DESCRIPTOR));
    ptr += sizeof(USB_INTERFACE_DESCRIPTOR);
    ((PUSB_CONFIGURATION_DESCRIPTOR)ConfigDescriptorBuffer)->wTotalLength += sizeof(USB_INTERFACE_DESCRIPTOR);
    for (j = 0; j < usb_config->interfaces[i]->interface_descriptor.bNumEndpoints; j++)
    {
      memcpy(ptr, &usb_config->interfaces[i]->endpoints[j]->endpoint_descriptor, sizeof(USB_ENDPOINT_DESCRIPTOR));
      ptr += sizeof(USB_ENDPOINT_DESCRIPTOR);
      ((PUSB_CONFIGURATION_DESCRIPTOR)ConfigDescriptorBuffer)->wTotalLength += sizeof(USB_ENDPOINT_DESCRIPTOR);
    }
  }
  *ConfigDescriptorBufferLength = ((PUSB_CONFIGURATION_DESCRIPTOR)ConfigDescriptorBuffer)->wTotalLength;
#endif

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_RemoveUsbDevice (
 PVOID BusContext,
 PUSB_DEVICE_HANDLE DeviceHandle,
 ULONG Flags)
{
  NTSTATUS status = STATUS_SUCCESS;
  WDFDEVICE device = BusContext;
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  xenusb_device_t *usb_device = DeviceHandle;
  int i, j, k;

  FUNCTION_ENTER();
  
  if (Flags & USBD_KEEP_DEVICE_DATA)
    FUNCTION_MSG("USBD_KEEP_DEVICE_DATA\n");
    
  if (Flags & USBD_MARK_DEVICE_BUSY)
    FUNCTION_MSG("USBD_MARK_DEVICE_BUSY\n");

  put_id_on_freelist(xupdd->dev_id_ss, (uint16_t)usb_device->address);
  // check if there are no pending requests
  for (i = 0; i < usb_device->device_descriptor.bNumConfigurations; i++) {
    for (j = 0; j < usb_device->configs[i]->config_descriptor.bNumInterfaces; j++) {
      for (k = 0; k < usb_device->configs[i]->interfaces[j]->interface_descriptor.bNumEndpoints; k++) {
        ExFreePoolWithTag(usb_device->configs[i]->interfaces[j]->endpoints[k], XENUSB_POOL_TAG);
      }
      ExFreePoolWithTag(usb_device->configs[i]->interfaces[j], XENUSB_POOL_TAG);
    }
    ExFreePoolWithTag(usb_device->configs[i]->config_descriptor_all, XENUSB_POOL_TAG);
    ExFreePoolWithTag(usb_device->configs[i], XENUSB_POOL_TAG);
  }
  ExFreePoolWithTag(usb_device->configs, XENUSB_POOL_TAG);
  ExFreePoolWithTag(usb_device, XENUSB_POOL_TAG);
  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_RestoreUsbDevice(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE OldDeviceHandle,
  PUSB_DEVICE_HANDLE NewDeviceHandle)
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;

  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(OldDeviceHandle);
  UNREFERENCED_PARAMETER(NewDeviceHandle);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_GetPortHackFlags(
 PVOID BusContext,
 PULONG HackFlags)
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;

  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(HackFlags);

  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_QueryDeviceInformation(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PVOID DeviceInformationBuffer,
  ULONG DeviceInformationBufferLength,
  PULONG LengthOfDataReturned)
{
  PUSB_DEVICE_INFORMATION_0 udi = DeviceInformationBuffer;
  xenusb_device_t *usb_device = DeviceHandle;
  ULONG i;
  ULONG required_size;

  UNREFERENCED_PARAMETER(BusContext);  

  FUNCTION_ENTER();

  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("DeviceHandle = %p\n", DeviceHandle);
  FUNCTION_MSG("DeviceInformationBuffer = %p\n", DeviceInformationBuffer);
  FUNCTION_MSG("DeviceInformationBufferLength = %d\n", DeviceInformationBufferLength);
  FUNCTION_MSG("->InformationLevel = %d\n", udi->InformationLevel);
  required_size = (ULONG)FIELD_OFFSET(USB_DEVICE_INFORMATION_0, PipeList[usb_device->active_interface->interface_descriptor.bNumEndpoints]);
  FUNCTION_MSG("required_size = %d\n", required_size);
  *LengthOfDataReturned = required_size;
  udi->ActualLength = required_size;
  if (DeviceInformationBufferLength < required_size)
  {
    FUNCTION_MSG("STATUS_BUFFER_TOO_SMALL\n");
    FUNCTION_EXIT();
    return STATUS_BUFFER_TOO_SMALL;
  }
  if (udi->InformationLevel != 0)
  {
    FUNCTION_MSG("STATUS_NOT_SUPPORTED\n");
    FUNCTION_EXIT();
    return STATUS_NOT_SUPPORTED;
  }
  udi->PortNumber = 1;
  memcpy(&udi->DeviceDescriptor, &usb_device->device_descriptor, sizeof(USB_DEVICE_DESCRIPTOR));
  udi->CurrentConfigurationValue = usb_device->active_config->config_descriptor.bConfigurationValue;
  udi->DeviceAddress = usb_device->address;
  udi->HubAddress = 1; // ?
  udi->DeviceSpeed = usb_device->device_speed;
  udi->DeviceType = usb_device->device_type;
  udi->NumberOfOpenPipes = usb_device->active_interface->interface_descriptor.bNumEndpoints;
  for (i = 0; i < usb_device->active_interface->interface_descriptor.bNumEndpoints; i++)
  {
    memcpy(&udi->PipeList[i].EndpointDescriptor, &usb_device->active_interface->endpoints[i]->endpoint_descriptor, sizeof(USB_ENDPOINT_DESCRIPTOR));
    udi->PipeList[0].ScheduleOffset = 0; // not necessarily right
  }
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenUsbHub_UBIH_GetControllerInformation (
  PVOID BusContext,
  PVOID ControllerInformationBuffer,
  ULONG ControllerInformationBufferLength,
  PULONG LengthOfDataReturned)
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;
  PUSB_CONTROLLER_INFORMATION_0 uci = ControllerInformationBuffer;
  //WDFDEVICE device = BusContext;
  //xenusb_device_t *usb_device = DeviceHandle;

  UNREFERENCED_PARAMETER(BusContext);  

  FUNCTION_ENTER();

  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("ControllerInformationBuffer = %p\n", ControllerInformationBuffer);
  FUNCTION_MSG("ControllerInformationBufferLength = %d\n", ControllerInformationBufferLength);
  FUNCTION_MSG("->InformationLevel = %d\n", uci->InformationLevel);
  if (ControllerInformationBufferLength < sizeof(USB_CONTROLLER_INFORMATION_0)) {
    FUNCTION_MSG("STATUS_BUFFER_TOO_SMALL\n");
    FUNCTION_EXIT();
    return STATUS_BUFFER_TOO_SMALL;
  }
  if (uci->InformationLevel != 0) {
    FUNCTION_MSG("STATUS_NOT_SUPPORTED\n");
    FUNCTION_EXIT();
    return STATUS_NOT_SUPPORTED;
  }
  
  uci->ActualLength = sizeof(USB_CONTROLLER_INFORMATION_0);
  uci->SelectiveSuspendEnabled = FALSE;
  uci->IsHighSpeedController = TRUE;
  *LengthOfDataReturned = uci->ActualLength;
  
  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_ControllerSelectiveSuspend (
  PVOID BusContext,
  BOOLEAN Enable)
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;

  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(Enable);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_GetExtendedHubInformation (
  PVOID BusContext,
  PDEVICE_OBJECT HubPhysicalDeviceObject,
  PVOID HubInformationBuffer,
  ULONG HubInformationBufferLength,
  PULONG LengthOfDataReturned)
{
  PUSB_EXTHUB_INFORMATION_0 hib = HubInformationBuffer;
  ULONG i;

  UNREFERENCED_PARAMETER(BusContext);  
  UNREFERENCED_PARAMETER(HubPhysicalDeviceObject);
  
  FUNCTION_ENTER();

  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("HubPhysicalDeviceObject = %p\n", HubPhysicalDeviceObject);
  FUNCTION_MSG("HubInformationBuffer = %p\n", HubInformationBuffer);
  FUNCTION_MSG("HubInformationBufferLength = %d\n", HubInformationBufferLength);
  FUNCTION_MSG("->InformationLevel = %d\n", hib->InformationLevel);
  if (HubInformationBufferLength < (ULONG)FIELD_OFFSET(USB_EXTHUB_INFORMATION_0, Port[8]))
  {
    FUNCTION_MSG("STATUS_BUFFER_TOO_SMALL\n");
    FUNCTION_EXIT();
    return STATUS_BUFFER_TOO_SMALL;
  }
#if 0
  if (hib->InformationLevel != 0)
  {
    FUNCTION_MSG("STATUS_NOT_SUPPORTED\n");
    FUNCTION_EXIT();
    return STATUS_NOT_SUPPORTED;
  }
#endif
  hib->InformationLevel = 0;
  hib->NumberOfPorts = 8;
  for (i = 0; i < hib->NumberOfPorts; i++)
  {
    hib->Port[i].PhysicalPortNumber = i + 1;
    hib->Port[i].PortLabelNumber = i + 1;
    hib->Port[i].VidOverride = 0;
    hib->Port[i].PidOverride = 0;
    hib->Port[i].PortAttributes = USB_PORTATTR_SHARED_USB2; // | USB_PORTATTR_NO_OVERCURRENT_UI;
  }
  *LengthOfDataReturned = FIELD_OFFSET(USB_EXTHUB_INFORMATION_0, Port[8]);
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenUsbHub_UBIH_GetRootHubSymbolicName(
  PVOID BusContext,
  PVOID HubInformationBuffer,
  ULONG HubInformationBufferLength,
  PULONG HubNameActualLength)
{
  NTSTATUS status = STATUS_SUCCESS;
  FUNCTION_ENTER();

  UNREFERENCED_PARAMETER(BusContext);
  
  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("HubInformationBuffer = %p\n", HubInformationBuffer);
  FUNCTION_MSG("HubInformationBufferLength = %d\n", HubInformationBufferLength);
  RtlStringCbCopyW(HubInformationBuffer, HubInformationBufferLength, L"ROOT_HUB");
  *HubNameActualLength = 16;

  FUNCTION_EXIT();
  return status;
}

static PVOID
XenUsbHub_UBIH_GetDeviceBusContext(
  PVOID BusContext,
  PVOID DeviceHandle)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return NULL;
}

static NTSTATUS
XenUsbHub_UBIH_Initialize20Hub (
  PVOID BusContext,
  PUSB_DEVICE_HANDLE HubDeviceHandle,
  ULONG TtCount)
{
  NTSTATUS status = STATUS_SUCCESS;
  
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(HubDeviceHandle);
  UNREFERENCED_PARAMETER(TtCount);
  
  FUNCTION_ENTER();
  FUNCTION_MSG("BusContext = %p\n", BusContext);
  FUNCTION_MSG("HubDeviceHandle = %p\n", HubDeviceHandle);
  FUNCTION_MSG("TtCount = %d\n", TtCount);
  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIH_RootHubInitNotification(
  PVOID BusContext,
  PVOID CallbackContext,
  PRH_INIT_CALLBACK CallbackFunction)
{
  NTSTATUS status = STATUS_SUCCESS;
  WDFDEVICE device = BusContext;
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  
  FUNCTION_ENTER();
  
  xupdd->BusCallbackFunction = CallbackFunction;
  xupdd->BusCallbackContext = CallbackContext;

  xupdd->BusCallbackFunction(xupdd->BusCallbackContext);
  
  FUNCTION_EXIT();
  return status;
}

/* This definition is incorrect in the docs */
static VOID
XenUsbHub_UBIH_FlushTransfers(
  PVOID BusContext,
  PVOID DeviceHandle)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
}

static VOID
XenUsbHub_UBIH_SetDeviceHandleData(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PDEVICE_OBJECT UsbDevicePdo)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(UsbDevicePdo);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
}

static NTSTATUS
XenUsbHub_UBIH_CreateUsbDeviceEx(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE *DeviceHandle,
  PUSB_DEVICE_HANDLE HubDeviceHandle,
  USHORT PortStatus,
  USHORT PortNumber,
  PUSB_CD_ERROR_INFORMATION CdErrorInfo,
  USHORT TtPortNumber)
{
  NTSTATUS status = STATUS_SUCCESS;
  
  UNREFERENCED_PARAMETER(CdErrorInfo);  
  UNREFERENCED_PARAMETER(TtPortNumber);
  
  FUNCTION_ENTER();

  status = XenUsbHub_UBIH_CreateUsbDevice(BusContext, DeviceHandle, HubDeviceHandle, PortStatus, PortNumber);
  
  FUNCTION_MSG("CdErrorInfo = %p\n", CdErrorInfo);
  FUNCTION_MSG("TtPortNumber = %d\n", TtPortNumber);
  
  FUNCTION_EXIT();
  return status;
}

#if (NTDDI_VERSION >= NTDDI_VISTA)  
static NTSTATUS
XenUsbHub_UBIH_CreateUsbDeviceV7(
    PVOID BusContext,
    PUSB_DEVICE_HANDLE *NewDeviceHandle,
    PUSB_DEVICE_HANDLE HsHubDeviceHandle,
    USHORT PortStatus,
    PUSB_PORT_PATH PortPath,
    PUSB_CD_ERROR_INFORMATION CdErrorInfo,
    USHORT TtPortNumber,
    PDEVICE_OBJECT PdoDeviceObject,
    PUNICODE_STRING PhysicalDeviceObjectName)
{
  NTSTATUS status;
  
  UNREFERENCED_PARAMETER(PdoDeviceObject);
  UNREFERENCED_PARAMETER(PhysicalDeviceObjectName);
  
  FUNCTION_ENTER();
  FUNCTION_MSG("PortPath->PortPathDepth = %d\n", PortPath->PortPathDepth);
  FUNCTION_MSG("PortPath->PortPath[%d] = %d\n", PortPath->PortPathDepth - 1);
  status = XenUsbHub_UBIH_CreateUsbDeviceEx(BusContext, NewDeviceHandle, &HsHubDeviceHandle, PortStatus, (USHORT)PortPath->PortPath[PortPath->PortPathDepth-1], CdErrorInfo, TtPortNumber);
  FUNCTION_MSG("PdoDeviceObject = %p\n", PdoDeviceObject);
  FUNCTION_MSG("PhysicalDeviceObjectName = %S\n", PhysicalDeviceObjectName->Buffer);
  FUNCTION_EXIT();
  return status;
}
#endif

static NTSTATUS
XenUsbHub_UBIH_InitializeUsbDeviceEx(
 PVOID BusContext,
 PUSB_DEVICE_HANDLE DeviceHandle,
 PUSB_ID_ERROR_INFORMATION IdErrInfo)
{
  NTSTATUS status;
  
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(IdErrInfo);
  FUNCTION_ENTER();
  FUNCTION_MSG("IdErrInfo->Version = %d\n", IdErrInfo->Version);
  FUNCTION_MSG("IdErrInfo->PathError = %d\n", IdErrInfo->PathError);
  FUNCTION_MSG("IdErrInfo->Arg1 = %08x\n", IdErrInfo->Arg1);
  FUNCTION_MSG("IdErrInfo->UsbAddress = %d\n", IdErrInfo->UsbAddress);
  FUNCTION_MSG("IdErrInfo->NtStatus = %08x\n", IdErrInfo->NtStatus);
  FUNCTION_MSG("IdErrInfo->UsbdStatus = %08x\n", IdErrInfo->UsbdStatus);
  FUNCTION_MSG("IdErrInfo->XtraInfo = %s\n", IdErrInfo->XtraInfo);
  status = XenUsbHub_UBIH_InitializeUsbDevice(BusContext, DeviceHandle);
  FUNCTION_EXIT();
  return status;
}

static BOOLEAN
XenUsbHub_UBIH_HubIsRoot(
  PVOID BusContext,
  PVOID DeviceObject)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceObject);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return TRUE;
}

static VOID
XenUsbHub_UBIH_AcquireBusSemaphore(
  PVOID BusContext)
{
  UNREFERENCED_PARAMETER(BusContext);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return;
}

static VOID
XenUsbHub_UBIH_ReleaseBusSemaphore(
  PVOID BusContext)
{
  UNREFERENCED_PARAMETER(BusContext);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return;
}

static ULONG
XenUsbHub_UBIH_CaculatePipeBandwidth(
  PVOID BusContext,
  PUSBD_PIPE_INFORMATION PipeInfo,
  USB_DEVICE_SPEED DeviceSpeed)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(PipeInfo);
  UNREFERENCED_PARAMETER(DeviceSpeed);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return (ULONG)-1;
}

static VOID
XenUsbHub_UBIH_SetBusSystemWakeMode(
  PVOID BusContext,
  ULONG Mode)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(Mode);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return;
}

static VOID
XenUsbHub_UBIH_SetDeviceFlag(
  PVOID BusContext,
  GUID *DeviceFlagGuid,
  PVOID ValueData,
  ULONG ValueLength)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceFlagGuid);
  UNREFERENCED_PARAMETER(ValueData);
  UNREFERENCED_PARAMETER(ValueLength);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return;
}

static NTSTATUS
XenUsbHub_UBIH_HubTestPoint(
  PVOID bus_context,
  PVOID device_handle,
  ULONG op_code,
  PVOID test_data)
{
  UNREFERENCED_PARAMETER(bus_context);
  UNREFERENCED_PARAMETER(device_handle);
  UNREFERENCED_PARAMETER(op_code);
  UNREFERENCED_PARAMETER(test_data);
  FUNCTION_ENTER();
  FUNCTION_MSG("device_handle = %p\n", device_handle);
  FUNCTION_MSG("op_code = %p\n", op_code);
  FUNCTION_MSG("test_data = %p\n", test_data);
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenUsbHub_UBIH_GetDevicePerformanceInfo(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PVOID DeviceInformationBuffer,
  ULONG DeviceInformationBufferLength,
  PULONG LengthOfDataCopied)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(DeviceInformationBuffer);
  UNREFERENCED_PARAMETER(DeviceInformationBufferLength);
  UNREFERENCED_PARAMETER(LengthOfDataCopied);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_UNSUCCESSFUL;
}

static NTSTATUS
XenUsbHub_UBIH_WaitAsyncPowerUp(
  PVOID BusContext)
{
  UNREFERENCED_PARAMETER(BusContext);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_UNSUCCESSFUL;
}

static NTSTATUS
XenUsbHub_UBIH_GetDeviceAddress(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PUSHORT DeviceAddress)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(DeviceAddress);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_UNSUCCESSFUL;
}

static NTSTATUS
XenUsbHub_UBIH_RefDeviceHandle(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PVOID Object,
  ULONG Tag)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(Object);
  UNREFERENCED_PARAMETER(Tag);
  FUNCTION_ENTER();
  FUNCTION_MSG("This should do something\n");
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static VOID
XenUsbHub_UBIH_DerefDeviceHandle(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  PVOID Object,
  ULONG Tag)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(Object);
  UNREFERENCED_PARAMETER(Tag);
  FUNCTION_ENTER();
  FUNCTION_MSG("This should do something\n");
  FUNCTION_EXIT();
}

static ULONG
XenUsbHub_UBIH_SetDeviceHandleIdleReadyState(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  ULONG NewIdleReadyState)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(NewIdleReadyState);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return (ULONG)-1;
}

static NTSTATUS
XenUsbHub_UBIH_GetContainerIdForPort(
  PVOID BusContext,
  USHORT PortNumber,
  LPGUID ContainerId)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(PortNumber);
  UNREFERENCED_PARAMETER(ContainerId);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_UNSUCCESSFUL;
}

static VOID
XenUsbHub_UBIH_SetContainerIdForPort(
  PVOID BusContext,
  USHORT PortNumber,
  LPGUID ContainerId)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(PortNumber);
  UNREFERENCED_PARAMETER(ContainerId);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
}

static NTSTATUS
XenUsbHub_UBIH_AbortAllDevicePipes(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static VOID
XenUsbHub_UBIH_SetDeviceErrataFlag(
  PVOID BusContext,
  PUSB_DEVICE_HANDLE DeviceHandle,
  ULONG DeviceErrataFlag)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DeviceHandle);
  UNREFERENCED_PARAMETER(DeviceErrataFlag);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return;
}  

static NTSTATUS
XenUsbHub_UBIU_GetUSBDIVersion(
  PVOID BusContext,
  PUSBD_VERSION_INFORMATION VersionInformation,
  PULONG HcdCapabilities
  )
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;

  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(VersionInformation);
  UNREFERENCED_PARAMETER(HcdCapabilities);

  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIU_QueryBusTime(
  PVOID BusContext,
  PULONG CurrentFrame
  )
{
  NTSTATUS status = STATUS_SUCCESS;
  static ULONG frame_no = 0;
  
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(CurrentFrame);
  
  //FUNCTION_ENTER();
  *CurrentFrame = frame_no++;
  //FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIU_SubmitIsoOutUrb(
  PVOID BusContext,
  PURB Urb
  )
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;

  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(Urb);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIU_QueryBusInformation(
  PVOID BusContext,
  ULONG Level,
  PVOID BusInformationBuffer,
  PULONG BusInformationBufferLength,
  PULONG BusInformationActualLength)
{
  NTSTATUS status = STATUS_UNSUCCESSFUL;

  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(Level);
  UNREFERENCED_PARAMETER(BusInformationBuffer);
  UNREFERENCED_PARAMETER(BusInformationBufferLength);
  UNREFERENCED_PARAMETER(BusInformationActualLength);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return status;
}

static BOOLEAN
XenUsbHub_UBIU_IsDeviceHighSpeed(PVOID BusContext)
{
  UNREFERENCED_PARAMETER(BusContext);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
  return TRUE; //TODO: get port value
}

static NTSTATUS
XenUsbHub_UBIU_EnumLogEntry(
  PVOID BusContext,
  ULONG DriverTag,
  ULONG EnumTag,
  ULONG P1,
  ULONG P2
)
{
  NTSTATUS status = STATUS_SUCCESS;
  FUNCTION_ENTER();
  
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(DriverTag);
  UNREFERENCED_PARAMETER(EnumTag);
  UNREFERENCED_PARAMETER(P1);
  UNREFERENCED_PARAMETER(P2);
  
  FUNCTION_MSG("DriverTag = %08x\n", DriverTag);
  FUNCTION_MSG("EnumTag = %08x\n", EnumTag);
  FUNCTION_MSG("P1 = %08x\n", P1);
  FUNCTION_MSG("P2 = %08x\n", P2);

  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenUsbHub_UBIU_QueryBusTimeEx(
  PVOID BusContext,
  PULONG HighSpeedFrameCounter)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(HighSpeedFrameCounter);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_UNSUCCESSFUL;
}

static NTSTATUS
XenUsbHub_UBIU_QueryControllerType(
  PVOID BusContext,
  PULONG HcdiOptionFlags,
  PUSHORT PciVendorId,
  PUSHORT PciDeviceId,
  PUCHAR PciClass,
  PUCHAR PciSubClass,
  PUCHAR PciRevisionId,
  PUCHAR PciProgIf)
{
  UNREFERENCED_PARAMETER(BusContext);
  UNREFERENCED_PARAMETER(HcdiOptionFlags);
  UNREFERENCED_PARAMETER(PciVendorId);
  UNREFERENCED_PARAMETER(PciDeviceId);
  UNREFERENCED_PARAMETER(PciClass);
  UNREFERENCED_PARAMETER(PciSubClass);
  UNREFERENCED_PARAMETER(PciRevisionId);
  UNREFERENCED_PARAMETER(PciProgIf);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_UNSUCCESSFUL;
}

static NTSTATUS
XenUsbHub_UBIHSS_SuspendHub(
  PVOID BusContext)
{
  UNREFERENCED_PARAMETER(BusContext);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenUsbHub_UBIHSS_ResumeHub(
  PVOID BusContext)
{
  UNREFERENCED_PARAMETER(BusContext);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

VOID
XenUsbHub_ProcessHubInterruptEvent(xenusb_endpoint_t *endpoint)
{
  NTSTATUS status;
  WDFDEVICE pdo_device = endpoint->interface->config->device->pdo_device;
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(pdo_device);
  PXENUSB_DEVICE_DATA xudd = GetXudd(xupdd->wdf_device_bus_fdo);
  WDF_REQUEST_PARAMETERS wrp;
  WDFREQUEST request;
  PURB urb;
  ULONG i;
  BOOLEAN port_change_flag = FALSE;
  
  FUNCTION_ENTER();
  WdfSpinLockAcquire(endpoint->lock);
  status = WdfIoQueueRetrieveNextRequest(endpoint->queue, &request);
  if (status == STATUS_NO_MORE_ENTRIES)
  {
    WdfSpinLockRelease(endpoint->lock);
    FUNCTION_MSG(" No More Entries\n", status);
    FUNCTION_EXIT();
    return;
  }
  if (!NT_SUCCESS(status))
  {
    WdfSpinLockRelease(endpoint->lock);
    FUNCTION_MSG(" Failed to get request from queue %08x\n", status);
    FUNCTION_EXIT();
    return;
  }
  
  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  WdfRequestGetParameters(request, &wrp);

  urb = (PURB)wrp.Parameters.Others.Arg1;
  ASSERT(urb);
  ASSERT(urb->UrbHeader.Function == URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER);
  RtlZeroMemory(urb->UrbBulkOrInterruptTransfer.TransferBuffer, urb->UrbBulkOrInterruptTransfer.TransferBufferLength);

  for (i = 0; i < xudd->num_ports; i++)
  {
FUNCTION_MSG("port %d - status = %04x, change = %04x\n", xudd->ports[i].port_number, xudd->ports[i].port_status, xudd->ports[i].port_change);
    if (xudd->ports[i].port_change) {
      FUNCTION_MSG("Port change on port %d - status = %04x, change = %04x\n",
        xudd->ports[i].port_number, xudd->ports[i].port_status, xudd->ports[i].port_change);
      ((PUCHAR)urb->UrbBulkOrInterruptTransfer.TransferBuffer)[xudd->ports[i].port_number >> 3] |= 1 << (xudd->ports[i].port_number & 7);
      port_change_flag = TRUE;
    }
FUNCTION_MSG("port %d - status = %04x, change = %04x\n", xudd->ports[i].port_number, xudd->ports[i].port_status, xudd->ports[i].port_change);
  }
  WdfSpinLockRelease(endpoint->lock);
  if (port_change_flag)
  {
    FUNCTION_MSG("Completing request %p\n", request);
    urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
    WdfRequestComplete(request, STATUS_SUCCESS);
  }
  else
  {
    FUNCTION_MSG("Requeuing request %p\n", request);
    WdfRequestRequeue(request);
  }
  FUNCTION_EXIT();
  return;
}

static NTSTATUS
XenUsbHub_EvtDeviceWdmIrpPreprocessQUERY_INTERFACE(WDFDEVICE device, PIRP irp)
{
  PIO_STACK_LOCATION stack;
  union {
    USB_BUS_INTERFACE_HUB_V5 ubih5;
#if (NTDDI_VERSION >= NTDDI_VISTA)
    USB_BUS_INTERFACE_HUB_V7 ubih6;
    USB_BUS_INTERFACE_HUB_V7 ubih7;
#endif
  } *ubih;
  union {
    USB_BUS_INTERFACE_USBDI_V1 ubiu0;
    USB_BUS_INTERFACE_USBDI_V1 ubiu1;
    USB_BUS_INTERFACE_USBDI_V2 ubiu2;
#if (NTDDI_VERSION >= NTDDI_VISTA)
    USB_BUS_INTERFACE_USBDI_V3 ubiu3;
#endif
  } *ubiu;

  FUNCTION_ENTER();
 
  stack = IoGetCurrentIrpStackLocation(irp);

  if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &USB_BUS_INTERFACE_HUB_GUID, sizeof(GUID)) == 0)
  {
    FUNCTION_MSG("USB_BUS_INTERFACE_HUB_GUID\n");
    if ((stack->Parameters.QueryInterface.Version == USB_BUSIF_HUB_VERSION_5 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_HUB_V5))
#if (NTDDI_VERSION >= NTDDI_VISTA)  
      || (stack->Parameters.QueryInterface.Version == USB_BUSIF_HUB_VERSION_6 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_HUB_V6))
      || (stack->Parameters.QueryInterface.Version == USB_BUSIF_HUB_VERSION_7 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_HUB_V7))
#endif
    )
    {
      ubih = (PVOID)stack->Parameters.QueryInterface.Interface;
      ubih->ubih5.Size = stack->Parameters.QueryInterface.Size;
      ubih->ubih5.Version = stack->Parameters.QueryInterface.Version;
      ubih->ubih5.BusContext = device;
      ubih->ubih5.InterfaceReference = WdfDeviceInterfaceReferenceNoOp;
      ubih->ubih5.InterfaceDereference = WdfDeviceInterfaceDereferenceNoOp;
      /* these two were changed to the Ex functions in v6 so we set them here so they don't get overwritten */
      ubih->ubih5.CreateUsbDevice = XenUsbHub_UBIH_CreateUsbDevice;
      ubih->ubih5.InitializeUsbDevice = XenUsbHub_UBIH_InitializeUsbDevice;
      switch (stack->Parameters.QueryInterface.Version)
      {
#if (NTDDI_VERSION >= NTDDI_VISTA)  
      case USB_BUSIF_HUB_VERSION_7:
        ubih->ubih7.HubTestPoint = XenUsbHub_UBIH_HubTestPoint;
        ubih->ubih7.GetDevicePerformanceInfo = XenUsbHub_UBIH_GetDevicePerformanceInfo;
        ubih->ubih7.WaitAsyncPowerUp = XenUsbHub_UBIH_WaitAsyncPowerUp;
        ubih->ubih7.GetDeviceAddress = XenUsbHub_UBIH_GetDeviceAddress;
        ubih->ubih7.RefDeviceHandle = XenUsbHub_UBIH_RefDeviceHandle;
        ubih->ubih7.DerefDeviceHandle = XenUsbHub_UBIH_DerefDeviceHandle;
        ubih->ubih7.SetDeviceHandleIdleReadyState = XenUsbHub_UBIH_SetDeviceHandleIdleReadyState;
        ubih->ubih7.CreateUsbDeviceV7 = XenUsbHub_UBIH_CreateUsbDeviceV7;
        ubih->ubih7.GetContainerIdForPort = XenUsbHub_UBIH_GetContainerIdForPort;
        ubih->ubih7.SetContainerIdForPort = XenUsbHub_UBIH_SetContainerIdForPort;
        ubih->ubih7.AbortAllDevicePipes = XenUsbHub_UBIH_AbortAllDevicePipes;
        ubih->ubih7.SetDeviceErrataFlag = XenUsbHub_UBIH_SetDeviceErrataFlag;  
        /* fall through */
      case USB_BUSIF_HUB_VERSION_6:
        ubih->ubih6.CreateUsbDevice = XenUsbHub_UBIH_CreateUsbDeviceEx;
        ubih->ubih6.InitializeUsbDevice = XenUsbHub_UBIH_InitializeUsbDeviceEx;
        ubih->ubih6.HubIsRoot = XenUsbHub_UBIH_HubIsRoot;
        ubih->ubih6.AcquireBusSemaphore = XenUsbHub_UBIH_AcquireBusSemaphore;
        ubih->ubih6.ReleaseBusSemaphore = XenUsbHub_UBIH_ReleaseBusSemaphore;
        ubih->ubih6.CaculatePipeBandwidth = XenUsbHub_UBIH_CaculatePipeBandwidth;
        ubih->ubih6.SetBusSystemWakeMode = XenUsbHub_UBIH_SetBusSystemWakeMode;
        ubih->ubih6.SetDeviceFlag = XenUsbHub_UBIH_SetDeviceFlag;
        /* fall through */
#endif
      case USB_BUSIF_HUB_VERSION_5:
        ubih->ubih5.GetUsbDescriptors = XenUsbHub_UBIH_GetUsbDescriptors;
        ubih->ubih5.RemoveUsbDevice = XenUsbHub_UBIH_RemoveUsbDevice;
        ubih->ubih5.RestoreUsbDevice = XenUsbHub_UBIH_RestoreUsbDevice;
        ubih->ubih5.GetPortHackFlags = XenUsbHub_UBIH_GetPortHackFlags;
        ubih->ubih5.QueryDeviceInformation = XenUsbHub_UBIH_QueryDeviceInformation;
        ubih->ubih5.GetControllerInformation = XenUsbHub_UBIH_GetControllerInformation;
        ubih->ubih5.ControllerSelectiveSuspend = XenUsbHub_UBIH_ControllerSelectiveSuspend;
        ubih->ubih5.GetExtendedHubInformation = XenUsbHub_UBIH_GetExtendedHubInformation;
        ubih->ubih5.GetRootHubSymbolicName = XenUsbHub_UBIH_GetRootHubSymbolicName;
        ubih->ubih5.GetDeviceBusContext = XenUsbHub_UBIH_GetDeviceBusContext;
        ubih->ubih5.Initialize20Hub = XenUsbHub_UBIH_Initialize20Hub;
        ubih->ubih5.RootHubInitNotification = XenUsbHub_UBIH_RootHubInitNotification;
        ubih->ubih5.FlushTransfers = XenUsbHub_UBIH_FlushTransfers;
        ubih->ubih5.SetDeviceHandleData = XenUsbHub_UBIH_SetDeviceHandleData;
      }
      irp->IoStatus.Information = 0;
      irp->IoStatus.Status = STATUS_SUCCESS;
    }
    else
    {
      FUNCTION_MSG("size/version mismatch\n");
    }
  }
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &USB_BUS_INTERFACE_USBDI_GUID, sizeof(GUID)) == 0)
  {
    FUNCTION_MSG("USB_BUS_INTERFACE_USBDI_GUID\n");
    if ((stack->Parameters.QueryInterface.Version == USB_BUSIF_USBDI_VERSION_0 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_USBDI_V0))
      || (stack->Parameters.QueryInterface.Version == USB_BUSIF_USBDI_VERSION_1 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_USBDI_V1))
      || (stack->Parameters.QueryInterface.Version == USB_BUSIF_USBDI_VERSION_2 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_USBDI_V2))
#if (NTDDI_VERSION >= NTDDI_VISTA)  
      || (stack->Parameters.QueryInterface.Version == USB_BUSIF_USBDI_VERSION_3 && stack->Parameters.QueryInterface.Size == sizeof(USB_BUS_INTERFACE_USBDI_V3))
#endif
    )
    {
      ubiu = (PVOID)stack->Parameters.QueryInterface.Interface;
      ubiu->ubiu0.Size = stack->Parameters.QueryInterface.Size;
      ubiu->ubiu0.Version = stack->Parameters.QueryInterface.Version;
      ubiu->ubiu0.BusContext = device;
      ubiu->ubiu0.InterfaceReference = WdfDeviceInterfaceReferenceNoOp;
      ubiu->ubiu0.InterfaceDereference = WdfDeviceInterfaceDereferenceNoOp;
      switch (stack->Parameters.QueryInterface.Version)
      {
#if (NTDDI_VERSION >= NTDDI_VISTA)  
      case USB_BUSIF_USBDI_VERSION_3:
        ubiu->ubiu3.QueryBusTimeEx = XenUsbHub_UBIU_QueryBusTimeEx;
        ubiu->ubiu3.QueryControllerType = XenUsbHub_UBIU_QueryControllerType;
        /* fall through */
#endif
      case USB_BUSIF_USBDI_VERSION_2:
        ubiu->ubiu2.EnumLogEntry  = XenUsbHub_UBIU_EnumLogEntry;
        /* fall through */
      case USB_BUSIF_USBDI_VERSION_1:
        ubiu->ubiu1.IsDeviceHighSpeed = XenUsbHub_UBIU_IsDeviceHighSpeed;
        /* fall through */
      case USB_BUSIF_USBDI_VERSION_0:          
        ubiu->ubiu0.GetUSBDIVersion = XenUsbHub_UBIU_GetUSBDIVersion;
        ubiu->ubiu0.QueryBusTime = XenUsbHub_UBIU_QueryBusTime;
        ubiu->ubiu0.SubmitIsoOutUrb = XenUsbHub_UBIU_SubmitIsoOutUrb;
        ubiu->ubiu0.QueryBusInformation = XenUsbHub_UBIU_QueryBusInformation;
      }
      irp->IoStatus.Information = 0;
      irp->IoStatus.Status = STATUS_SUCCESS;
    }
    else
    {
      FUNCTION_MSG("size/version mismatch\n");
    }
  }
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &GUID_TRANSLATOR_INTERFACE_STANDARD, sizeof(GUID)) == 0)
    FUNCTION_MSG("GUID_TRANSLATOR_INTERFACE_STANDARD\n");
#if (NTDDI_VERSION >= NTDDI_VISTA)
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &GUID_PNP_LOCATION_INTERFACE, sizeof(GUID)) == 0)
    FUNCTION_MSG("GUID_PNP_LOCATION_INTERFACE\n");
#endif
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &USB_BUS_INTERFACE_HUB_MINIDUMP_GUID, sizeof(GUID)) == 0)
    FUNCTION_MSG("USB_BUS_INTERFACE_HUB_MINIDUMP_GUID\n");
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &USB_BUS_INTERFACE_HUB_SS_GUID, sizeof(GUID)) == 0)
    FUNCTION_MSG("USB_BUS_INTERFACE_HUB_SS_GUID\n");
  else
    FUNCTION_MSG("GUID = %08X-%04X-%04X-%04X-%02X%02X%02X%02X%02X%02X\n",
      stack->Parameters.QueryInterface.InterfaceType->Data1,
      stack->Parameters.QueryInterface.InterfaceType->Data2,
      stack->Parameters.QueryInterface.InterfaceType->Data3,
      (stack->Parameters.QueryInterface.InterfaceType->Data4[0] << 8) |
       stack->Parameters.QueryInterface.InterfaceType->Data4[1],
      stack->Parameters.QueryInterface.InterfaceType->Data4[2],
      stack->Parameters.QueryInterface.InterfaceType->Data4[3],
      stack->Parameters.QueryInterface.InterfaceType->Data4[4],
      stack->Parameters.QueryInterface.InterfaceType->Data4[5],
      stack->Parameters.QueryInterface.InterfaceType->Data4[6],
      stack->Parameters.QueryInterface.InterfaceType->Data4[7]);

  FUNCTION_MSG("Size = %d\n", stack->Parameters.QueryInterface.Size);
  FUNCTION_MSG("Version = %d\n", stack->Parameters.QueryInterface.Version);
  FUNCTION_MSG("Interface = %p\n", stack->Parameters.QueryInterface.Interface);

  IoSkipCurrentIrpStackLocation(irp);
  
  FUNCTION_EXIT();

  return WdfDeviceWdmDispatchPreprocessedIrp(device, irp);
}

NTSTATUS
XenUsbHub_PLI_GetLocationString(PVOID context, PWCHAR *location_strings) {
  UNREFERENCED_PARAMETER(context);
  
  FUNCTION_ENTER();
  *location_strings = L"james\0";
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

NTSTATUS
XenUsb_EvtChildListCreateDevice(WDFCHILDLIST child_list,
  PWDF_CHILD_IDENTIFICATION_DESCRIPTION_HEADER identification_header,
  PWDFDEVICE_INIT child_init)
{
  NTSTATUS status = STATUS_SUCCESS;
  WDFDEVICE bus_device = WdfChildListGetDevice(child_list);
  WDF_OBJECT_ATTRIBUTES child_attributes;
  WDFDEVICE child_device;
  PXENUSB_PDO_IDENTIFICATION_DESCRIPTION identification = (PXENUSB_PDO_IDENTIFICATION_DESCRIPTION)identification_header;
  WDF_DEVICE_PNP_CAPABILITIES child_pnp_capabilities;
  DECLARE_UNICODE_STRING_SIZE(buffer, 512);
  DECLARE_CONST_UNICODE_STRING(location, L"Xen Bus");
  PXENUSB_PDO_DEVICE_DATA xupdd;
  PXENUSB_DEVICE_DATA xudd = GetXudd(bus_device);
  WDF_PNPPOWER_EVENT_CALLBACKS child_pnp_power_callbacks;
  WDF_DEVICE_POWER_CAPABILITIES child_power_capabilities;
  WDF_IO_QUEUE_CONFIG queue_config;
  WDF_IO_TARGET_OPEN_PARAMS target_params;
#if (NTDDI_VERSION >= NTDDI_VISTA)
  WDF_QUERY_INTERFACE_CONFIG interface_config;
#if 0
  USB_BUS_INTERFACE_HUB_SELECTIVE_SUSPEND ubihss;
#endif
  PNP_LOCATION_INTERFACE pli;
#endif
  UCHAR pnp_minor_functions[] = { IRP_MN_QUERY_INTERFACE };
  int i;

  FUNCTION_ENTER();

  //FUNCTION_MSG("device = %d, port = %d, vendor_id = %04x, product_id = %04x\n",

  WdfDeviceInitSetDeviceType(child_init, FILE_DEVICE_UNKNOWN);

  status = WdfDeviceInitAssignWdmIrpPreprocessCallback(child_init, XenUsbHub_EvtDeviceWdmIrpPreprocessQUERY_INTERFACE,
    IRP_MJ_PNP, pnp_minor_functions, ARRAY_SIZE(pnp_minor_functions));
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  
  WDF_PNPPOWER_EVENT_CALLBACKS_INIT(&child_pnp_power_callbacks);
  child_pnp_power_callbacks.EvtDeviceD0Entry = XenUsbHub_EvtDeviceD0Entry;
  child_pnp_power_callbacks.EvtDeviceD0Exit = XenUsbHub_EvtDeviceD0Exit;
  child_pnp_power_callbacks.EvtDevicePrepareHardware = XenUsbHub_EvtDevicePrepareHardware;
  child_pnp_power_callbacks.EvtDeviceReleaseHardware = XenUsbHub_EvtDeviceReleaseHardware;
  child_pnp_power_callbacks.EvtDeviceUsageNotification = XenUsbHub_EvtDeviceUsageNotification;
  WdfDeviceInitSetPnpPowerEventCallbacks(child_init, &child_pnp_power_callbacks);

  RtlUnicodeStringPrintf(&buffer, L"USB\\ROOT_HUB");
  status = WdfPdoInitAssignDeviceID(child_init, &buffer);
  status = WdfPdoInitAddHardwareID(child_init, &buffer);

  RtlUnicodeStringPrintf(&buffer, L"VUSB_%d", identification->device_number);
  status = WdfPdoInitAssignInstanceID(child_init, &buffer);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  
  RtlUnicodeStringPrintf(&buffer, L"PVUSB device #%d", identification->device_number, identification);
  status = WdfPdoInitAddDeviceText(child_init, &buffer, &location, 0x0409);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  WdfPdoInitSetDefaultLocale(child_init, 0x0409);

  WdfDeviceInitSetPowerNotPageable(child_init);

  WdfDeviceInitSetIoType(child_init, WdfDeviceIoDirect);

  WdfPdoInitAllowForwardingRequestToParent(child_init);

  WDF_OBJECT_ATTRIBUTES_INIT_CONTEXT_TYPE(&child_attributes, XENUSB_PDO_DEVICE_DATA);
  status = WdfDeviceCreate(&child_init, &child_attributes, &child_device);
  if (!NT_SUCCESS(status))
  {
    return status;
  }

  xupdd = GetXupdd(child_device);

  xudd->root_hub_device = child_device;
  
  stack_new(&xupdd->dev_id_ss, DEV_ID_COUNT);
  /* 0 is invalid and 1 is the root hub */
  for (i = 2; i < DEV_ID_COUNT; i++)  {
    put_id_on_freelist(xupdd->dev_id_ss, (uint16_t)i);
  }
  
  xupdd->wdf_device = child_device;
  xupdd->wdf_device_bus_fdo = WdfChildListGetDevice(child_list);

  status = WdfIoTargetCreate(bus_device, WDF_NO_OBJECT_ATTRIBUTES, &xupdd->bus_fdo_target);
  ASSERT(NT_SUCCESS(status));
  WDF_IO_TARGET_OPEN_PARAMS_INIT_EXISTING_DEVICE(&target_params, WdfDeviceWdmGetDeviceObject(bus_device));
  status = WdfIoTargetOpen(xupdd->bus_fdo_target, &target_params);
  ASSERT(NT_SUCCESS(status));
  
  xupdd->usb_device = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_device_t), XENUSB_POOL_TAG);
  // get address from freelist...
  xupdd->usb_device->pdo_device = child_device;
  xupdd->usb_device->address = 1;
  xupdd->usb_device->device_speed = UsbHighSpeed;
  xupdd->usb_device->device_type = Usb20Device;
  xupdd->usb_device->device_descriptor.bLength = sizeof(USB_DEVICE_DESCRIPTOR);
  xupdd->usb_device->device_descriptor.bDescriptorType = USB_DEVICE_DESCRIPTOR_TYPE;
  xupdd->usb_device->device_descriptor.bcdUSB = 0x0200;
  xupdd->usb_device->device_descriptor.bDeviceClass = 9;
  xupdd->usb_device->device_descriptor.bDeviceSubClass = 0;
  xupdd->usb_device->device_descriptor.bDeviceProtocol = 1;
  xupdd->usb_device->device_descriptor.bMaxPacketSize0 = 64;
  xupdd->usb_device->device_descriptor.idVendor = 0x0000;
  xupdd->usb_device->device_descriptor.idProduct = 0x0000;
  xupdd->usb_device->device_descriptor.bcdDevice = 0x0206;
  xupdd->usb_device->device_descriptor.iManufacturer = 3;
  xupdd->usb_device->device_descriptor.iProduct = 2;
  xupdd->usb_device->device_descriptor.iSerialNumber = 1;
  xupdd->usb_device->device_descriptor.bNumConfigurations = 1;
  xupdd->usb_device->configs = ExAllocatePoolWithTag(NonPagedPool, sizeof(PVOID) * 1, XENUSB_POOL_TAG);
  xupdd->usb_device->configs[0] = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_config_t) + sizeof(PVOID) * 1, XENUSB_POOL_TAG);
  xupdd->usb_device->active_config = xupdd->usb_device->configs[0];
  xupdd->usb_device->configs[0]->device = xupdd->usb_device;
  xupdd->usb_device->configs[0]->config_descriptor.bLength = sizeof(USB_CONFIGURATION_DESCRIPTOR);
  xupdd->usb_device->configs[0]->config_descriptor.bDescriptorType = USB_CONFIGURATION_DESCRIPTOR_TYPE;
  xupdd->usb_device->configs[0]->config_descriptor.wTotalLength = sizeof(USB_CONFIGURATION_DESCRIPTOR);
  xupdd->usb_device->configs[0]->config_descriptor.bNumInterfaces = 1;
  xupdd->usb_device->configs[0]->config_descriptor.bConfigurationValue = 1;
  xupdd->usb_device->configs[0]->config_descriptor.iConfiguration = 0;
  xupdd->usb_device->configs[0]->config_descriptor.bmAttributes = 0xe0;
  xupdd->usb_device->configs[0]->config_descriptor.MaxPower = 0;
  xupdd->usb_device->configs[0]->interfaces[0] = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_interface_t) + sizeof(PVOID) * 1, XENUSB_POOL_TAG);
  xupdd->usb_device->active_interface = xupdd->usb_device->configs[0]->interfaces[0];
  xupdd->usb_device->configs[0]->interfaces[0]->config = xupdd->usb_device->configs[0];
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bLength = 9;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bDescriptorType = USB_INTERFACE_DESCRIPTOR_TYPE;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bInterfaceNumber = 0;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bAlternateSetting = 0;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bNumEndpoints = 1;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bInterfaceClass = 9;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bInterfaceSubClass = 0;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.bInterfaceProtocol = 0;
  xupdd->usb_device->configs[0]->interfaces[0]->interface_descriptor.iInterface = 0;
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0] = ExAllocatePoolWithTag(NonPagedPool, sizeof(xenusb_endpoint_t), XENUSB_POOL_TAG);
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->interface = xupdd->usb_device->configs[0]->interfaces[0];
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->pipe_value = 0;
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->endpoint_descriptor.bLength = 7;
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->endpoint_descriptor.bDescriptorType = USB_ENDPOINT_DESCRIPTOR_TYPE;
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->endpoint_descriptor.bEndpointAddress = 0x81; // EP 1 IN
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->endpoint_descriptor.bmAttributes = USB_ENDPOINT_TYPE_INTERRUPT;
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->endpoint_descriptor.wMaxPacketSize = 2;
  xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->endpoint_descriptor.bInterval = 12;
  WdfSpinLockCreate(WDF_NO_OBJECT_ATTRIBUTES, &xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->lock);

  WDF_IO_QUEUE_CONFIG_INIT(&queue_config, WdfIoQueueDispatchParallel);
  queue_config.EvtIoInternalDeviceControl = XenUsb_EvtIoInternalDeviceControl_ROOTHUB_SUBMIT_URB;
  queue_config.PowerManaged = TRUE; /* power managed queue for SUBMIT_URB */
  status = WdfIoQueueCreate(child_device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, &xupdd->usb_device->urb_queue);
  if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("Error creating urb_queue 0x%x\n", status);
      return status;
  }
  
  WDF_IO_QUEUE_CONFIG_INIT(&queue_config, WdfIoQueueDispatchManual);
  //WDF_OBJECT_ATTRIBUTES_INIT_CONTEXT_TYPE(&queue_attributes, pxenusb_endpoint_t);
  queue_config.PowerManaged = TRUE;
  //queue_config.EvtIoInternalDeviceControl = XenUsb_EvtIoInternalDeviceControl_Interrupt_SUBMIT_URB;
  status = WdfIoQueueCreate(child_device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES,
    &xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->queue);
  if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("Error creating timer io_queue 0x%x\n", status);
      return status;
  }
  //*GetEndpoint(xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]->queue) = xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0];

  WDF_IO_QUEUE_CONFIG_INIT_DEFAULT_QUEUE(&queue_config, WdfIoQueueDispatchParallel);
  queue_config.EvtIoInternalDeviceControl = XenUsbHub_EvtIoInternalDeviceControl;
  queue_config.EvtIoDeviceControl = XenUsbHub_EvtIoDeviceControl;
  queue_config.EvtIoDefault = XenUsbHub_EvtIoDefault;
  /* can't be power managed or deadlocks occur */
  queue_config.PowerManaged = FALSE;
  status = WdfIoQueueCreate(child_device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, &xupdd->io_queue);
  if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("Error creating io_queue 0x%x\n", status);
      return status;
  }

  WdfDeviceSetSpecialFileSupport(child_device, WdfSpecialFilePaging, TRUE);
  WdfDeviceSetSpecialFileSupport(child_device, WdfSpecialFileHibernation, TRUE);
  WdfDeviceSetSpecialFileSupport(child_device, WdfSpecialFileDump, TRUE);

  WDF_DEVICE_PNP_CAPABILITIES_INIT(&child_pnp_capabilities);
  child_pnp_capabilities.LockSupported = WdfFalse;
  child_pnp_capabilities.EjectSupported  = WdfTrue;
  child_pnp_capabilities.Removable  = WdfTrue;
  child_pnp_capabilities.DockDevice  = WdfFalse;
  child_pnp_capabilities.UniqueID  = WdfTrue;
  child_pnp_capabilities.SilentInstall  = WdfTrue;
  child_pnp_capabilities.SurpriseRemovalOK  = WdfTrue;
  child_pnp_capabilities.HardwareDisabled = WdfFalse;
  WdfDeviceSetPnpCapabilities(child_device, &child_pnp_capabilities);

  WDF_DEVICE_POWER_CAPABILITIES_INIT(&child_power_capabilities);
  child_power_capabilities.DeviceD1 = WdfTrue;
  child_power_capabilities.WakeFromD1 = WdfTrue;
  child_power_capabilities.DeviceWake = PowerDeviceD1;
  child_power_capabilities.DeviceState[PowerSystemWorking]   = PowerDeviceD0;
  child_power_capabilities.DeviceState[PowerSystemSleeping1] = PowerDeviceD1;
  child_power_capabilities.DeviceState[PowerSystemSleeping2] = PowerDeviceD2;
  child_power_capabilities.DeviceState[PowerSystemSleeping3] = PowerDeviceD2;
  child_power_capabilities.DeviceState[PowerSystemHibernate] = PowerDeviceD3;
  child_power_capabilities.DeviceState[PowerSystemShutdown]  = PowerDeviceD3;
  WdfDeviceSetPowerCapabilities(child_device, &child_power_capabilities);  

#if (NTDDI_VERSION >= NTDDI_VISTA)
#if 0
  ubihss.BusContext = child_device;
  ubihss.Size = sizeof(USB_BUS_INTERFACE_HUB_SELECTIVE_SUSPEND);
  ubihss.Version = USB_BUSIF_HUB_SS_VERSION_0;
  ubihss.InterfaceReference = WdfDeviceInterfaceReferenceNoOp;
  ubihss.InterfaceDereference = WdfDeviceInterfaceDereferenceNoOp;
  ubihss.SuspendHub = XenUsbHub_UBIHSS_SuspendHub;
  ubihss.ResumeHub = XenUsbHub_UBIHSS_ResumeHub;
  WDF_QUERY_INTERFACE_CONFIG_INIT(&interface_config, (PINTERFACE)&ubihss, &USB_BUS_INTERFACE_HUB_SS_GUID, NULL);
  status = WdfDeviceAddQueryInterface(child_device, &interface_config);
  if (!NT_SUCCESS(status))
    return status;
#endif
  pli.Size = sizeof(USB_BUS_INTERFACE_HUB_SELECTIVE_SUSPEND);
  pli.Version = 1;
  pli.Context = child_device;
  pli.InterfaceReference = WdfDeviceInterfaceReferenceNoOp;
  pli.InterfaceDereference = WdfDeviceInterfaceDereferenceNoOp;
  pli.GetLocationString = XenUsbHub_PLI_GetLocationString;
  WDF_QUERY_INTERFACE_CONFIG_INIT(&interface_config, (PINTERFACE)&pli, &GUID_PNP_LOCATION_INTERFACE, NULL);
  status = WdfDeviceAddQueryInterface(child_device, &interface_config);
  if (!NT_SUCCESS(status))
    return status;  
#endif

  status = WdfDeviceCreateDeviceInterface(child_device, &GUID_DEVINTERFACE_USB_HUB, NULL);
  if (!NT_SUCCESS(status))
    return status;

  FUNCTION_EXIT();
  
  return status;
}
