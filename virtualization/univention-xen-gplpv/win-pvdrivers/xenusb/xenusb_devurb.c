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

#define EPROTO          71      /* Protocol error */

EVT_WDF_REQUEST_COMPLETION_ROUTINE XenUsb_CompletionBulkInterrupt;

static USBD_STATUS
XenUsb_GetUsbdStatusFromPvStatus(ULONG pvstatus) {
  switch (pvstatus)
  {
  case 0:
    return USBD_STATUS_SUCCESS;
  case -EPROTO: /*  -71 */
    FUNCTION_MSG("pvstatus = -EPROTO\n");
    return USBD_STATUS_CRC;
  case -EPIPE: /* see linux code - EPIPE is when the HCD returned a stall */
    FUNCTION_MSG("pvstatus = -EPIPE (USBD_STATUS_STALL_PID)\n");
    return USBD_STATUS_STALL_PID;
#if 0
  case -EOVERFLOW:
    shadow->urb->UrbHeader.Status USBD_STATUS_DATA_OVERRUN;
    break;
  case -EREMOTEIO:
    shadow->urb->UrbHeader.Status USBD_STATUS_ERROR_SHORT_TRANSFER;
    break;
#endif
  case -ESHUTDOWN: /* -108 */
    FUNCTION_MSG("pvstatus = -ESHUTDOWN (USBD_STATUS_DEVICE_GONE)\n");
    return USBD_STATUS_DEVICE_GONE;
  default:
    FUNCTION_MSG("pvstatus = %d\n", pvstatus);
    return USBD_STATUS_INTERNAL_HC_ERROR;
  }
}

VOID
XenUsb_CompletionBulkInterrupt(
  WDFREQUEST request,
  WDFIOTARGET target,
  PWDF_REQUEST_COMPLETION_PARAMS params,
  WDFCONTEXT context)
{
  PURB urb;
  pvurb_t *pvurb = context;
  WDF_REQUEST_PARAMETERS wrp;

  UNREFERENCED_PARAMETER(target);

  FUNCTION_ENTER();

  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  WdfRequestGetParameters(request, &wrp);
  urb = (PURB)wrp.Parameters.Others.Arg1;
  ASSERT(urb);
  FUNCTION_MSG("URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER\n");
  FUNCTION_MSG("rsp id = %d\n", pvurb->rsp.id);
  FUNCTION_MSG("rsp start_frame = %d\n", pvurb->rsp.start_frame);
  FUNCTION_MSG("rsp status = %d\n", pvurb->rsp.status);
  FUNCTION_MSG("rsp actual_length = %d\n", pvurb->rsp.actual_length);
  FUNCTION_MSG("rsp error_count = %d\n", pvurb->rsp.error_count);
  FUNCTION_MSG("total_length = %d\n", pvurb->total_length);
  urb->UrbHeader.Status = XenUsb_GetUsbdStatusFromPvStatus(pvurb->rsp.status);
  urb->UrbBulkOrInterruptTransfer.TransferBufferLength = (ULONG)params->IoStatus.Information;
  if (urb->UrbHeader.Status == USBD_STATUS_SUCCESS)
    WdfRequestComplete(request, STATUS_SUCCESS);
  else
    WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
  FUNCTION_EXIT();
}

VOID
XenUsb_EvtIoInternalDeviceControl_DEVICE_SUBMIT_URB(
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
  WDF_MEMORY_DESCRIPTOR pvurb_descriptor;
  WDFMEMORY pvurb_memory;
  WDF_REQUEST_SEND_OPTIONS send_options;
  PURB urb;
  pvurb_t *pvurb;
  pvurb_t local_pvurb; /* just use stack allocated space when submitting synchronously */
  PUSB_DEFAULT_PIPE_SETUP_PACKET setup_packet;
  PUSBD_INTERFACE_INFORMATION interface_information;
  ULONG i, j;
  xenusb_device_t *usb_device;
  xenusb_endpoint_t *endpoint;
  urb_decode_t decode_data;
  ULONG decode_retval;

  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);
  UNREFERENCED_PARAMETER(io_control_code);

  FUNCTION_ENTER();

  ASSERT(io_control_code == IOCTL_INTERNAL_USB_SUBMIT_URB);

  status = STATUS_UNSUCCESSFUL;

  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  WdfRequestGetParameters(request, &wrp);

  urb = (PURB)wrp.Parameters.Others.Arg1;
  ASSERT(urb);
#if 0
  FUNCTION_MSG("urb = %p\n", urb);
  FUNCTION_MSG(" Length = %d\n", urb->UrbHeader.Length);
  FUNCTION_MSG(" Function = %d\n", urb->UrbHeader.Function);
  FUNCTION_MSG(" Status = %d\n", urb->UrbHeader.Status);
  FUNCTION_MSG(" UsbdDeviceHandle = %p\n", urb->UrbHeader.UsbdDeviceHandle);
  FUNCTION_MSG(" UsbdFlags = %08x\n", urb->UrbHeader.UsbdFlags);
#endif
  usb_device = urb->UrbHeader.UsbdDeviceHandle;

  ASSERT(usb_device);

  decode_retval = XenUsb_DecodeControlUrb(urb, &decode_data);
  if (decode_retval == URB_DECODE_UNKNOWN)
  {
    FUNCTION_MSG("Calling WdfRequestCompletestatus with status = %08x\n", STATUS_UNSUCCESSFUL);
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
    return;
  }

#if 0
  if (decode_retval != URB_DECODE_NOT_CONTROL)
  {
    FUNCTION_MSG("bmRequestType = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.B);
    FUNCTION_MSG(" Recipient = %x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient);
    FUNCTION_MSG(" Type = %x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type);
    FUNCTION_MSG(" Dir = %x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Dir);
    FUNCTION_MSG("bRequest = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.bRequest);
    FUNCTION_MSG("wValue = %04x\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.W);
    FUNCTION_MSG(" Low = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.LowByte);
    FUNCTION_MSG(" High = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.HiByte);
    FUNCTION_MSG("wIndex = %04x\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex);
    FUNCTION_MSG(" Low = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte);
    FUNCTION_MSG(" High = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.HiByte);
    FUNCTION_MSG("wLength = %04x\n", decode_data.setup_packet.default_pipe_setup_packet.wLength);
  }
#endif
  
  switch(urb->UrbHeader.Function)
  {
  case URB_FUNCTION_SELECT_CONFIGURATION:
    FUNCTION_MSG("URB_FUNCTION_SELECT_CONFIGURATION\n");
    FUNCTION_MSG(" ConfigurationDescriptor = %p\n", urb->UrbSelectConfiguration.ConfigurationDescriptor);
    if (urb->UrbSelectConfiguration.ConfigurationDescriptor)
    {
      FUNCTION_MSG("  bLength = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bLength);
      FUNCTION_MSG("  bDescriptorType = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bDescriptorType);
      FUNCTION_MSG("  wTotalLength = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->wTotalLength);
      FUNCTION_MSG("  bNumInterfaces = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bNumInterfaces);
      FUNCTION_MSG("  bConfigurationValue = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bConfigurationValue);
      FUNCTION_MSG("  iConfiguration = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->iConfiguration);
      FUNCTION_MSG("  bmAttributes = %04x\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bmAttributes);
      FUNCTION_MSG("  MaxPower = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->MaxPower);
    }
    if (urb->UrbSelectConfiguration.ConfigurationDescriptor)
    {
      xenusb_config_t *usb_config = NULL;
      for (i = 0; i < usb_device->device_descriptor.bNumConfigurations; i++)
      {
        if (usb_device->configs[i]->config_descriptor.bConfigurationValue == urb->UrbSelectConfiguration.ConfigurationDescriptor->bConfigurationValue)
          usb_config = usb_device->configs[i];
      }
      urb->UrbSelectConfiguration.ConfigurationHandle = usb_config;
      interface_information = &urb->UrbSelectConfiguration.Interface;
      /* configuration is fully populated */
      for (i = 0; i < urb->UrbSelectConfiguration.ConfigurationDescriptor->bNumInterfaces; i++)
      {
        /* i think we need to pay attention to the alt setting here .. */
        xenusb_interface_t *usb_interface = usb_config->interfaces[i];
        interface_information->InterfaceNumber = usb_interface->interface_descriptor.bInterfaceNumber;
        interface_information->AlternateSetting = usb_interface->interface_descriptor.bAlternateSetting;
        interface_information->Class = usb_interface->interface_descriptor.bInterfaceClass;
        interface_information->SubClass = usb_interface->interface_descriptor.bInterfaceSubClass;
        interface_information->Protocol = usb_interface->interface_descriptor.bInterfaceProtocol;
        interface_information->InterfaceHandle = usb_interface;
        FUNCTION_MSG("InterfaceInformation[%d]\n", i);
        FUNCTION_MSG(" Length = %d\n", interface_information->Length);
        FUNCTION_MSG(" InterfaceNumber = %d\n", interface_information->InterfaceNumber);
        FUNCTION_MSG(" AlternateSetting = %d\n", interface_information->AlternateSetting);
        FUNCTION_MSG(" Class = %02x\n", (ULONG)interface_information->Class);
        FUNCTION_MSG(" SubClass = %02x\n", (ULONG)interface_information->SubClass);
        FUNCTION_MSG(" Protocol = %02x\n", (ULONG)interface_information->Protocol);
        FUNCTION_MSG(" InterfaceHandle = %p\n", interface_information->InterfaceHandle);
        FUNCTION_MSG(" NumberOfPipes = %d\n", interface_information->NumberOfPipes);
        for (j = 0; j < interface_information->NumberOfPipes; j++)
        {
          xenusb_endpoint_t *usb_endpoint = usb_interface->endpoints[j];
          FUNCTION_MSG(" Pipe[%d] (before)\n", j);
          FUNCTION_MSG("  MaximumPacketSize = %d\n", interface_information->Pipes[j].MaximumPacketSize);
          FUNCTION_MSG("  EndpointAddress = %d\n", interface_information->Pipes[j].EndpointAddress);
          FUNCTION_MSG("  Interval = %d\n", interface_information->Pipes[j].Interval);
          FUNCTION_MSG("  PipeType = %d\n", interface_information->Pipes[j].PipeType);
          FUNCTION_MSG("  PipeHandle = %p\n", interface_information->Pipes[j].PipeHandle);
          FUNCTION_MSG("  MaximumTransferSize = %d\n", interface_information->Pipes[j].MaximumTransferSize);
          FUNCTION_MSG("  PipeFlags = %08x\n", interface_information->Pipes[j].PipeFlags);
          interface_information->Pipes[j].MaximumPacketSize = usb_endpoint->endpoint_descriptor.wMaxPacketSize;
          interface_information->Pipes[j].EndpointAddress = usb_endpoint->endpoint_descriptor.bEndpointAddress;
          interface_information->Pipes[j].Interval = usb_endpoint->endpoint_descriptor.bInterval;
          switch (usb_endpoint->endpoint_descriptor.bmAttributes & USB_ENDPOINT_TYPE_MASK)
          {
          case USB_ENDPOINT_TYPE_CONTROL:
            FUNCTION_MSG("USB_ENDPOINT_TYPE_CONTROL");
            interface_information->Pipes[j].PipeType = UsbdPipeTypeControl;
            break;
          case USB_ENDPOINT_TYPE_ISOCHRONOUS:
            FUNCTION_MSG("USB_ENDPOINT_TYPE_ISOCHRONOUS");
            interface_information->Pipes[j].PipeType = UsbdPipeTypeIsochronous;
            break;
          case USB_ENDPOINT_TYPE_BULK:
            FUNCTION_MSG("USB_ENDPOINT_TYPE_BULK");
            interface_information->Pipes[j].PipeType = UsbdPipeTypeBulk;
            break;
          case USB_ENDPOINT_TYPE_INTERRUPT:
            FUNCTION_MSG("USB_ENDPOINT_TYPE_INTERRUPT");
            interface_information->Pipes[j].PipeType = UsbdPipeTypeInterrupt;
            break;
          }
          interface_information->Pipes[j].PipeHandle = usb_endpoint;
          FUNCTION_MSG(" Pipe[%d] (after)\n", j);
          FUNCTION_MSG("  MaximumPacketSize = %d\n", interface_information->Pipes[j].MaximumPacketSize);
          FUNCTION_MSG("  EndpointAddress = %d\n", interface_information->Pipes[j].EndpointAddress);
          FUNCTION_MSG("  Interval = %d\n", interface_information->Pipes[j].Interval);
          FUNCTION_MSG("  PipeType = %d\n", interface_information->Pipes[j].PipeType);
          FUNCTION_MSG("  PipeHandle = %p\n", interface_information->Pipes[j].PipeHandle);
          FUNCTION_MSG("  MaximumTransferSize = %d\n", interface_information->Pipes[j].MaximumTransferSize);
          FUNCTION_MSG("  PipeFlags = %08x\n", interface_information->Pipes[j].PipeFlags);
        }
        interface_information = (PUSBD_INTERFACE_INFORMATION)((PUCHAR)interface_information + interface_information->Length);
      }
    }
    else
    {
      // ? unconfigure device here
    }
    pvurb = &local_pvurb; //ExAllocatePoolWithTag(NonPagedPool, sizeof(*pvurb), XENUSB_POOL_TAG);
    WDF_MEMORY_DESCRIPTOR_INIT_BUFFER(&pvurb_descriptor, pvurb, sizeof(*pvurb));
    pvurb->req.pipe = LINUX_PIPE_TYPE_CTRL | (usb_device->address << 8) | usb_device->port_number;
    pvurb->req.transfer_flags = 0;
    pvurb->req.buffer_length = 0;
    setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)pvurb->req.u.ctrl;
    setup_packet->bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
    setup_packet->bmRequestType.Type = BMREQUEST_STANDARD;
    setup_packet->bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    setup_packet->bRequest = USB_REQUEST_SET_CONFIGURATION;
    setup_packet->wLength = 0;
    setup_packet->wValue.W = urb->UrbSelectConfiguration.ConfigurationDescriptor->bConfigurationValue;
    setup_packet->wIndex.W = 0;
    pvurb->mdl = NULL;
    WDF_REQUEST_SEND_OPTIONS_INIT(&send_options, WDF_REQUEST_SEND_OPTION_TIMEOUT);
    WDF_REQUEST_SEND_OPTIONS_SET_TIMEOUT(&send_options, WDF_REL_TIMEOUT_IN_SEC(10));
    status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, request, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
    FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB status = %08x\n", status);
    if (!NT_SUCCESS(status)) {
      WdfRequestComplete(request, status);
    } else {
      FUNCTION_MSG("rsp start_frame = %d\n", pvurb->rsp.start_frame);
      FUNCTION_MSG("rsp status = %d\n", pvurb->rsp.status);
      FUNCTION_MSG("rsp actual_length = %d\n", pvurb->rsp.actual_length);
      FUNCTION_MSG("rsp error_count = %d\n", pvurb->rsp.error_count);
      urb->UrbHeader.Status = XenUsb_GetUsbdStatusFromPvStatus(pvurb->rsp.status);
      WdfRequestComplete(request, pvurb->rsp.status?STATUS_UNSUCCESSFUL:STATUS_SUCCESS);
    }
    break;
  case URB_FUNCTION_SELECT_INTERFACE:
    FUNCTION_MSG("URB_FUNCTION_SELECT_INTERFACE\n");
    interface_information = &urb->UrbSelectInterface.Interface;
    FUNCTION_MSG("InterfaceInformation\n");
    FUNCTION_MSG(" Length = %d\n", interface_information->Length);
    FUNCTION_MSG(" InterfaceNumber = %d\n", interface_information->InterfaceNumber);
    FUNCTION_MSG(" AlternateSetting = %d\n", interface_information->AlternateSetting);
    FUNCTION_MSG(" Class = %02x\n", (ULONG)interface_information->Class);
    FUNCTION_MSG(" SubClass = %02x\n", (ULONG)interface_information->SubClass);
    FUNCTION_MSG(" Protocol = %02x\n", (ULONG)interface_information->Protocol);
    FUNCTION_MSG(" Reserved = %02x\n", (ULONG)interface_information->Reserved);
    FUNCTION_MSG(" InterfaceHandle = %p\n", interface_information->InterfaceHandle);
    FUNCTION_MSG(" NumberOfPipes = %d\n", interface_information->NumberOfPipes);
    for (i = 0; i < interface_information->NumberOfPipes; i++)
    {
      FUNCTION_MSG(" Pipe[%d]\n", i);
      FUNCTION_MSG("  MaximumPacketSize = %d\n", interface_information->Pipes[i].MaximumPacketSize);
      FUNCTION_MSG("  EndpointAddress = %d\n", interface_information->Pipes[i].EndpointAddress);
      FUNCTION_MSG("  Interval = %d\n", interface_information->Pipes[i].Interval);
      FUNCTION_MSG("  PipeType = %d\n", interface_information->Pipes[i].PipeType);
      FUNCTION_MSG("  PipeHandle = %p\n", interface_information->Pipes[i].PipeHandle);
      FUNCTION_MSG("  MaximumTransferSize = %d\n", interface_information->Pipes[i].MaximumTransferSize);
      FUNCTION_MSG("  PipeFlags = %08x\n", interface_information->Pipes[i].PipeFlags);
    }

    pvurb = &local_pvurb; //ExAllocatePoolWithTag(NonPagedPool, sizeof(*pvurb), XENUSB_POOL_TAG);
    WDF_MEMORY_DESCRIPTOR_INIT_BUFFER(&pvurb_descriptor, pvurb, sizeof(*pvurb));
    pvurb->req.pipe = LINUX_PIPE_TYPE_CTRL | (usb_device->address << 8) | usb_device->port_number;
    pvurb->req.transfer_flags = 0;
    pvurb->req.buffer_length = 0;
    setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)pvurb->req.u.ctrl;
    setup_packet->bmRequestType.Recipient = BMREQUEST_TO_INTERFACE;
    setup_packet->bmRequestType.Type = BMREQUEST_STANDARD;
    setup_packet->bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    setup_packet->bRequest = USB_REQUEST_SET_INTERFACE;
    setup_packet->wLength = 0;
    setup_packet->wValue.W = urb->UrbSelectInterface.Interface.AlternateSetting;
    setup_packet->wIndex.W = urb->UrbSelectInterface.Interface.InterfaceNumber;
    pvurb->mdl = NULL;
    WDF_REQUEST_SEND_OPTIONS_INIT(&send_options, WDF_REQUEST_SEND_OPTION_TIMEOUT);
    WDF_REQUEST_SEND_OPTIONS_SET_TIMEOUT(&send_options, WDF_REL_TIMEOUT_IN_SEC(10));
    status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, request, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
    FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB status = %08x\n", status);
    if (!NT_SUCCESS(status)) {
      WdfRequestComplete(request, status);
    } else {
      FUNCTION_MSG("rsp start_frame = %d\n", pvurb->rsp.start_frame);
      FUNCTION_MSG("rsp status = %d\n", pvurb->rsp.status);
      FUNCTION_MSG("rsp actual_length = %d\n", pvurb->rsp.actual_length);
      FUNCTION_MSG("rsp error_count = %d\n", pvurb->rsp.error_count);
      urb->UrbHeader.Status = XenUsb_GetUsbdStatusFromPvStatus(pvurb->rsp.status);
      WdfRequestComplete(request, pvurb->rsp.status?STATUS_UNSUCCESSFUL:STATUS_SUCCESS);
    }
    break;
#if (NTDDI_VERSION >= NTDDI_VISTA)  
  case URB_FUNCTION_CONTROL_TRANSFER_EX:
#endif
  case URB_FUNCTION_CONTROL_TRANSFER:
  case URB_FUNCTION_CLASS_DEVICE:
  case URB_FUNCTION_CLASS_INTERFACE:
  case URB_FUNCTION_CLASS_OTHER:
  case URB_FUNCTION_GET_DESCRIPTOR_FROM_DEVICE:
  case URB_FUNCTION_GET_DESCRIPTOR_FROM_INTERFACE:
  case URB_FUNCTION_GET_STATUS_FROM_DEVICE:
    FUNCTION_MSG("URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
    FUNCTION_MSG("bmRequestType = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.B);
    FUNCTION_MSG(" Recipient = %x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient);
    FUNCTION_MSG(" Type = %x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type);
    FUNCTION_MSG(" Dir = %x\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Dir);
    FUNCTION_MSG("bRequest = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.bRequest);
    FUNCTION_MSG("wValue = %04x\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.W);
    FUNCTION_MSG(" Low = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.LowByte);
    FUNCTION_MSG(" High = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.HiByte);
    FUNCTION_MSG("wIndex = %04x\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex);
    FUNCTION_MSG(" Low = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte);
    FUNCTION_MSG(" High = %02x\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.HiByte);
    FUNCTION_MSG("wLength = %04x\n", decode_data.setup_packet.default_pipe_setup_packet.wLength);
    FUNCTION_MSG("decode_data.transfer_flags = %08x\n", decode_data.transfer_flags);
    FUNCTION_MSG("*decode_data.length = %04x\n", *decode_data.length);
    pvurb = &local_pvurb;
    WDF_MEMORY_DESCRIPTOR_INIT_BUFFER(&pvurb_descriptor, pvurb, sizeof(*pvurb));
    pvurb->req.pipe = LINUX_PIPE_TYPE_CTRL | (usb_device->address << 8) | usb_device->port_number;
    pvurb->req.transfer_flags = 0; 
    if (!(decode_data.transfer_flags & USBD_SHORT_TRANSFER_OK))
      pvurb->req.transfer_flags |= LINUX_URB_SHORT_NOT_OK;
    if (decode_data.transfer_flags & (USBD_TRANSFER_DIRECTION_IN | USBD_SHORT_TRANSFER_OK))
      pvurb->req.pipe |= LINUX_PIPE_DIRECTION_IN;
    else
      pvurb->req.pipe |= LINUX_PIPE_DIRECTION_OUT;
    memcpy(pvurb->req.u.ctrl, decode_data.setup_packet.raw, 8);
    FUNCTION_MSG("req.pipe = %08x\n", pvurb->req.pipe);
    FUNCTION_MSG("req.transfer_flags = %08x\n", pvurb->req.transfer_flags);
    if (decode_data.buffer) {
      FUNCTION_MSG("decode_data.buffer = %p\n", decode_data.buffer);
      pvurb->mdl = IoAllocateMdl(decode_data.buffer, *decode_data.length, FALSE, FALSE, NULL);
      FUNCTION_MSG("pvurb->mdl = %p\n", pvurb->mdl);
      MmBuildMdlForNonPagedPool(pvurb->mdl);
    } else {
      FUNCTION_MSG("decode_data.mdl = %p\n", decode_data.mdl);
      pvurb->mdl = decode_data.mdl;
    }
    WDF_REQUEST_SEND_OPTIONS_INIT(&send_options, WDF_REQUEST_SEND_OPTION_TIMEOUT);
    WDF_REQUEST_SEND_OPTIONS_SET_TIMEOUT(&send_options, WDF_REL_TIMEOUT_IN_SEC(10));
    status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, request, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
    if (decode_data.buffer)
      IoFreeMdl(pvurb->mdl);
    FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB status = %08x\n", status);
    if (!NT_SUCCESS(status)) {
      WdfRequestComplete(request, status);
    } else {
      FUNCTION_MSG("rsp start_frame = %d\n", pvurb->rsp.start_frame);
      FUNCTION_MSG("rsp status = %d\n", pvurb->rsp.status);
      FUNCTION_MSG("rsp actual_length = %d\n", pvurb->rsp.actual_length);
      FUNCTION_MSG("rsp error_count = %d\n", pvurb->rsp.error_count);
      urb->UrbHeader.Status = XenUsb_GetUsbdStatusFromPvStatus(pvurb->rsp.status);
      WdfRequestComplete(request, pvurb->rsp.status?STATUS_UNSUCCESSFUL:STATUS_SUCCESS);
    }
    break;
  case URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER: /* 11.12.4 */
    endpoint = urb->UrbBulkOrInterruptTransfer.PipeHandle;
    FUNCTION_MSG("endpoint address = %02x\n", endpoint->endpoint_descriptor.bEndpointAddress);
    FUNCTION_MSG("endpoint interval = %02x\n", endpoint->endpoint_descriptor.bInterval);
    FUNCTION_MSG("pipe_direction_bit = %08x\n", endpoint->pipe_value & LINUX_PIPE_DIRECTION_IN);
    FUNCTION_MSG("short_ok_bit = %08x\n", urb->UrbBulkOrInterruptTransfer.TransferFlags & USBD_SHORT_TRANSFER_OK);
    FUNCTION_MSG("flags_direction_bit = %08x\n", urb->UrbBulkOrInterruptTransfer.TransferFlags & USBD_TRANSFER_DIRECTION_IN);
    FUNCTION_MSG("pipe_handle = %p\n", endpoint);
    FUNCTION_MSG("pipe_value = %08x\n", endpoint->pipe_value);
    
    pvurb = ExAllocatePoolWithTag(NonPagedPool, sizeof(*pvurb), XENUSB_POOL_TAG);
    status = WdfMemoryCreatePreallocated(WDF_NO_OBJECT_ATTRIBUTES, pvurb, sizeof(*pvurb), &pvurb_memory);
    ASSERT(NT_SUCCESS(status));
    pvurb->req.pipe = endpoint->pipe_value;
    pvurb->req.transfer_flags = 0; 
    if (!(urb->UrbBulkOrInterruptTransfer.TransferFlags & USBD_SHORT_TRANSFER_OK) && (endpoint->pipe_value & LINUX_PIPE_DIRECTION_IN))
      pvurb->req.transfer_flags |= LINUX_URB_SHORT_NOT_OK;
    pvurb->req.u.intr.interval = endpoint->endpoint_descriptor.bInterval; /* check this... maybe there is some overridden value that should be used? */
    FUNCTION_MSG("req.pipe = %08x\n", pvurb->req.pipe);
    FUNCTION_MSG("req.transfer_flags = %08x\n", pvurb->req.transfer_flags);
    switch(endpoint->endpoint_descriptor.bmAttributes & USB_ENDPOINT_TYPE_MASK)
    {
    case USB_ENDPOINT_TYPE_BULK:
      FUNCTION_MSG(" USB_ENDPOINT_TYPE_BULK\n");
      break;
    case USB_ENDPOINT_TYPE_INTERRUPT:
      FUNCTION_MSG(" USB_ENDPOINT_TYPE_INTERRUPT\n");
      break;
    default:
      FUNCTION_MSG(" USB_ENDPOINT_TYPE_%d\n", endpoint->endpoint_descriptor.bmAttributes);
      break;
    }
    if (urb->UrbBulkOrInterruptTransfer.TransferBuffer) {
      pvurb->mdl = IoAllocateMdl(urb->UrbBulkOrInterruptTransfer.TransferBuffer, urb->UrbBulkOrInterruptTransfer.TransferBufferLength, FALSE, FALSE, NULL);
      MmBuildMdlForNonPagedPool(pvurb->mdl);
    } else {
      pvurb->mdl = urb->UrbBulkOrInterruptTransfer.TransferBufferMDL;
    }
    status = WdfIoTargetFormatRequestForInternalIoctlOthers(xupdd->bus_fdo_target, request, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, pvurb_memory, NULL, NULL, NULL, NULL, NULL);
    FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB status = %08x\n", status);
    if (!NT_SUCCESS(status)) {
      if (urb->UrbBulkOrInterruptTransfer.TransferBuffer)
        IoFreeMdl(pvurb->mdl);
      WdfRequestComplete(request, status);
    }
    WdfRequestSetCompletionRoutine(request, XenUsb_CompletionBulkInterrupt, pvurb);
    if (!WdfRequestSend(request, xupdd->bus_fdo_target, NULL)) {
      FUNCTION_MSG("WdfRequestSend returned FALSE\n");
      if (urb->UrbBulkOrInterruptTransfer.TransferBuffer)
        IoFreeMdl(pvurb->mdl);
      WdfRequestComplete(request, WdfRequestGetStatus(request));
    }
    break;
  case URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL:
    FUNCTION_MSG("URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL\n");
    FUNCTION_MSG(" PipeHandle = %p\n", urb->UrbPipeRequest.PipeHandle);
    /* we only clear the stall here */
    endpoint = urb->UrbBulkOrInterruptTransfer.PipeHandle;

    pvurb = &local_pvurb; //ExAllocatePoolWithTag(NonPagedPool, sizeof(*pvurb), XENUSB_POOL_TAG);
    WDF_MEMORY_DESCRIPTOR_INIT_BUFFER(&pvurb_descriptor, pvurb, sizeof(*pvurb));
    pvurb->req.pipe = LINUX_PIPE_TYPE_CTRL | (usb_device->address << 8) | usb_device->port_number;
    pvurb->req.transfer_flags = 0;
    pvurb->req.buffer_length = 0;
    setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)pvurb->req.u.ctrl;
    setup_packet->bmRequestType.Recipient = BMREQUEST_TO_ENDPOINT;
    setup_packet->bmRequestType.Type = BMREQUEST_STANDARD;
    setup_packet->bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    setup_packet->bRequest = USB_REQUEST_CLEAR_FEATURE;
    setup_packet->wLength = 0;
    setup_packet->wValue.W = 0; /* 0 == ENDPOINT_HALT */
    setup_packet->wIndex.W = endpoint->endpoint_descriptor.bEndpointAddress;
    pvurb->mdl = NULL;
    WDF_REQUEST_SEND_OPTIONS_INIT(&send_options, WDF_REQUEST_SEND_OPTION_TIMEOUT);
    WDF_REQUEST_SEND_OPTIONS_SET_TIMEOUT(&send_options, WDF_REL_TIMEOUT_IN_SEC(10));
    status = WdfIoTargetSendInternalIoctlOthersSynchronously(xupdd->bus_fdo_target, request, IOCTL_INTERNAL_PVUSB_SUBMIT_URB, &pvurb_descriptor, NULL, NULL, &send_options, NULL);
    FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB status = %08x\n", status);
    if (!NT_SUCCESS(status)) {
      WdfRequestComplete(request, status);
    } else {
      FUNCTION_MSG("rsp start_frame = %d\n", pvurb->rsp.start_frame);
      FUNCTION_MSG("rsp status = %d\n", pvurb->rsp.status);
      FUNCTION_MSG("rsp actual_length = %d\n", pvurb->rsp.actual_length);
      FUNCTION_MSG("rsp error_count = %d\n", pvurb->rsp.error_count);
      urb->UrbHeader.Status = XenUsb_GetUsbdStatusFromPvStatus(pvurb->rsp.status);
      WdfRequestComplete(request, pvurb->rsp.status?STATUS_UNSUCCESSFUL:STATUS_SUCCESS);
    }
    break;
  case URB_FUNCTION_ABORT_PIPE:
    FUNCTION_MSG("URB_FUNCTION_ABORT_PIPE\n");
    FUNCTION_MSG(" PipeHandle = %p\n", urb->UrbPipeRequest.PipeHandle);
    /* just fake this.... i think we really need to flush any pending requests too */
    urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
    WdfRequestComplete(request, STATUS_SUCCESS);
    break;
  default:
    FUNCTION_MSG("URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
    break;
  }
  FUNCTION_EXIT();
}
