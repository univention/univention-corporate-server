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

/*
decode all the funky URB_Xxx functions into a basic 8 byte SetupPacket
*/
ULONG
XenUsb_DecodeControlUrb(PURB urb, urb_decode_t *decode_data)
{
  ULONG retval;
  
  //FUNCTION_ENTER();
  switch(urb->UrbHeader.Function)
  {
  case URB_FUNCTION_SELECT_CONFIGURATION:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_SELECT_CONFIGURATION\n"));
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = BMREQUEST_STANDARD;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bRequest = USB_REQUEST_SET_CONFIGURATION;
    decode_data->setup_packet.default_pipe_setup_packet.wLength = 0;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.W = urb->UrbSelectConfiguration.ConfigurationDescriptor->bConfigurationValue;
    decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = 0;
    decode_data->buffer = NULL;
    retval = URB_DECODE_INCOMPLETE;
    break;
  case URB_FUNCTION_SELECT_INTERFACE:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_SELECT_INTERFACE\n"));
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = BMREQUEST_TO_INTERFACE;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = BMREQUEST_STANDARD;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bRequest = USB_REQUEST_SET_INTERFACE;
    decode_data->setup_packet.default_pipe_setup_packet.wLength = 0;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.W = urb->UrbSelectInterface.Interface.AlternateSetting;
    decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = urb->UrbSelectInterface.Interface.InterfaceNumber;
    decode_data->buffer = NULL;
    retval = URB_DECODE_INCOMPLETE;
    break;
  case URB_FUNCTION_GET_DESCRIPTOR_FROM_DEVICE:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_GET_DESCRIPTOR_FROM_DEVICE\n"));
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = BMREQUEST_STANDARD;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = BMREQUEST_DEVICE_TO_HOST;
    decode_data->setup_packet.default_pipe_setup_packet.bRequest = USB_REQUEST_GET_DESCRIPTOR;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.LowByte = urb->UrbControlDescriptorRequest.Index;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.HiByte = urb->UrbControlDescriptorRequest.DescriptorType;
    switch(urb->UrbControlDescriptorRequest.DescriptorType)
    {
    case USB_STRING_DESCRIPTOR_TYPE:
      decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = urb->UrbControlDescriptorRequest.LanguageId;
      break;
    default:
      decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = 0;
      break;
    }
    decode_data->setup_packet.default_pipe_setup_packet.wLength = (USHORT)urb->UrbControlDescriptorRequest.TransferBufferLength;
    decode_data->buffer = urb->UrbControlTransfer.TransferBuffer;
    decode_data->length = &urb->UrbControlTransfer.TransferBufferLength;
    retval = URB_DECODE_COMPLETE;
    break;
  case URB_FUNCTION_CLASS_DEVICE: /* CONTROL_TRANSFER has same underlying format as FUNCTION_CLASS_XXX */
FUNCTION_MSG("Function = %04x, RequestTypeReservedBits = %02x\n", urb->UrbHeader.Function, urb->UrbControlVendorClassRequest.RequestTypeReservedBits);
  case URB_FUNCTION_CLASS_OTHER:
  //case URB_FUNCTION_GET_STATUS_FROM_DEVICE: // seems to be missing fields...
  case URB_FUNCTION_CONTROL_TRANSFER:
#if (NTDDI_VERSION >= NTDDI_VISTA)  
  case URB_FUNCTION_CONTROL_TRANSFER_EX:
#endif

    //KdPrint((__DRIVER_NAME "     URB_FUNCTION_CONTROL_TRANSFER\n"));
    decode_data->buffer = urb->UrbControlTransfer.TransferBuffer;
    decode_data->length = &urb->UrbControlTransfer.TransferBufferLength;
    memcpy(decode_data->setup_packet.raw, urb->UrbControlTransfer.SetupPacket, sizeof(decode_data->setup_packet.raw));
    retval = URB_DECODE_COMPLETE;
    break;
  case URB_FUNCTION_GET_STATUS_FROM_DEVICE:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_GET_STATUS_FROM_DEVICE\n"));
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = BMREQUEST_STANDARD;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = BMREQUEST_DEVICE_TO_HOST;
    decode_data->setup_packet.default_pipe_setup_packet.bRequest = USB_REQUEST_GET_STATUS;
    decode_data->setup_packet.default_pipe_setup_packet.wLength = 0;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.W = 0;
    decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = urb->UrbControlGetStatusRequest.Index;
    decode_data->buffer = urb->UrbControlTransfer.TransferBuffer;
    decode_data->length = &urb->UrbControlTransfer.TransferBufferLength;
    retval = URB_DECODE_COMPLETE;
    break;
#if 0
  case URB_FUNCTION_GET_STATUS_FROM_DEVICE:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_GET_STATUS_FROM_DEVICE\n"));
    KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlGetStatusRequest.TransferBufferLength));
    KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlGetStatusRequest.TransferBuffer));
    KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlGetStatusRequest.TransferBufferMDL));
    KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlGetStatusRequest.Index));
    if (urb->UrbControlGetStatusRequest.Index == 0)
    {
      urb->UrbControlGetStatusRequest.TransferBufferLength = 2;
      *(PUSHORT)urb->UrbControlGetStatusRequest.TransferBuffer = 0x0003;
      urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
      WdfRequestComplete(request, STATUS_SUCCESS);
    }
    else
    {
      KdPrint((__DRIVER_NAME "     Unknown Index\n"));
      urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
      WdfRequestComplete(request, STATUS_UNSUCCESSFUL); //STATUS_UNSUCCESSFUL);
    }    
    break;
  case URB_FUNCTION_CLASS_DEVICE:
#if 1
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_CLASS_DEVICE\n"));
    KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlVendorClassRequest.TransferBufferLength));
    KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlVendorClassRequest.TransferBuffer));
    KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlVendorClassRequest.TransferBufferMDL));
    KdPrint((__DRIVER_NAME "      RequestTypeReservedBits = %02x\n", urb->UrbControlVendorClassRequest.RequestTypeReservedBits));
    KdPrint((__DRIVER_NAME "      Request = %02x\n", urb->UrbControlVendorClassRequest.Request));
    KdPrint((__DRIVER_NAME "      Value = %04x\n", urb->UrbControlVendorClassRequest.Value));
    KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlVendorClassRequest.Index));
#endif
    switch (urb->UrbControlVendorClassRequest.Request)
    {
    case USB_REQUEST_GET_DESCRIPTOR:
      KdPrint((__DRIVER_NAME "     URB_FUNCTION_CLASS_DEVICE\n"));
      KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlVendorClassRequest.TransferBufferLength));
      KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlVendorClassRequest.TransferBuffer));
      KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlVendorClassRequest.TransferBufferMDL));
      KdPrint((__DRIVER_NAME "      RequestTypeReservedBits = %02x\n", urb->UrbControlVendorClassRequest.RequestTypeReservedBits));
      KdPrint((__DRIVER_NAME "      Request = %02x\n", urb->UrbControlVendorClassRequest.Request));
      KdPrint((__DRIVER_NAME "      Value = %04x\n", urb->UrbControlVendorClassRequest.Value));
      KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlVendorClassRequest.Index));
      KdPrint((__DRIVER_NAME "      USB_REQUEST_GET_DESCRIPTOR\n"));
      switch (urb->UrbControlVendorClassRequest.Value >> 8)
      {
      case 0x00:
#if 0      
        memcpy(urb->UrbControlVendorClassRequest.TransferBuffer, &usb_device->device_descriptor, sizeof(USB_DEVICE_DESCRIPTOR));
        urb->UrbControlVendorClassRequest.TransferBufferLength = sizeof(USB_DEVICE_DESCRIPTOR);
        urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
        WdfRequestComplete(request, STATUS_SUCCESS);
        break;
#endif
      case 0x29: // Hub Descriptor
        KdPrint((__DRIVER_NAME "       HUB_DESCRIPTOR\n"));
        uhd = urb->UrbControlVendorClassRequest.TransferBuffer;
        urb->UrbControlVendorClassRequest.TransferBufferLength = FIELD_OFFSET(USB_HUB_DESCRIPTOR, bRemoveAndPowerMask[0]) + 2 + 1;
        uhd->bDescriptorLength = (UCHAR)urb->UrbControlVendorClassRequest.TransferBufferLength;
        uhd->bDescriptorType = 0x29;
        uhd->bNumberOfPorts = 8;
        uhd->wHubCharacteristics = 0x0012; // no power switching no overcurrent protection
        uhd->bPowerOnToPowerGood = 1; // 2ms units
        uhd->bHubControlCurrent = 0;
        // DeviceRemovable bits (includes an extra bit at the start)
        uhd->bRemoveAndPowerMask[0] = 0;
        uhd->bRemoveAndPowerMask[1] = 0;
        // PortPwrCtrlMask
        uhd->bRemoveAndPowerMask[2] = 0xFF;
        urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
        WdfRequestComplete(request, STATUS_SUCCESS);
        break;
      default:
        KdPrint((__DRIVER_NAME "       Unknown Value %02x\n", urb->UrbControlVendorClassRequest.Value >> 8));
        urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
        WdfRequestComplete(request, STATUS_UNSUCCESSFUL); //STATUS_UNSUCCESSFUL);
        break;
      }
      break;
    case USB_REQUEST_GET_STATUS:
      KdPrint((__DRIVER_NAME "      TransferFlags = %08x\n", urb->UrbControlVendorClassRequest.TransferFlags));
      KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlVendorClassRequest.TransferBufferLength));
      KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlVendorClassRequest.TransferBuffer));
      KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlVendorClassRequest.TransferBufferMDL));
      KdPrint((__DRIVER_NAME "      RequestTypeReservedBits = %02x\n", urb->UrbControlVendorClassRequest.RequestTypeReservedBits));
      KdPrint((__DRIVER_NAME "      Request = %02x\n", urb->UrbControlVendorClassRequest.Request));
      KdPrint((__DRIVER_NAME "      Value = %04x\n", urb->UrbControlVendorClassRequest.Value));
      KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlVendorClassRequest.Index));
      KdPrint((__DRIVER_NAME "      USB_REQUEST_GET_STATUS\n"));
      // Check that RequestTypeReservedBits == 0xA0
      KdPrint((__DRIVER_NAME "       GetHubStatus\n"));
      /* hub status */
      // shoud be able to get this field from somewhere else...
      ((PUSHORT)urb->UrbControlVendorClassRequest.TransferBuffer)[0] = 0x0000;
      ((PUSHORT)urb->UrbControlVendorClassRequest.TransferBuffer)[1] = 0x0000; /* no change occurred */
      urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
      WdfRequestComplete(request, STATUS_SUCCESS);
      break;
    case USB_REQUEST_CLEAR_FEATURE:
      KdPrint((__DRIVER_NAME "      TransferFlags = %08x\n", urb->UrbControlVendorClassRequest.TransferFlags));
      KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlVendorClassRequest.TransferBufferLength));
      KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlVendorClassRequest.TransferBuffer));
      KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlVendorClassRequest.TransferBufferMDL));
      KdPrint((__DRIVER_NAME "      RequestTypeReservedBits = %02x\n", urb->UrbControlVendorClassRequest.RequestTypeReservedBits));
      KdPrint((__DRIVER_NAME "      Request = %02x\n", urb->UrbControlVendorClassRequest.Request));
      KdPrint((__DRIVER_NAME "      Value = %04x\n", urb->UrbControlVendorClassRequest.Value));
      KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlVendorClassRequest.Index));
      KdPrint((__DRIVER_NAME "      USB_REQUEST_CLEAR_FEATURE\n"));
      urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
      WdfRequestComplete(request, STATUS_SUCCESS);
      break;
    default:
      KdPrint((__DRIVER_NAME "      TransferFlags = %08x\n", urb->UrbControlVendorClassRequest.TransferFlags));
      KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlVendorClassRequest.TransferBufferLength));
      KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlVendorClassRequest.TransferBuffer));
      KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlVendorClassRequest.TransferBufferMDL));
      KdPrint((__DRIVER_NAME "      RequestTypeReservedBits = %02x\n", urb->UrbControlVendorClassRequest.RequestTypeReservedBits));
      KdPrint((__DRIVER_NAME "      Request = %02x\n", urb->UrbControlVendorClassRequest.Request));
      KdPrint((__DRIVER_NAME "      Value = %04x\n", urb->UrbControlVendorClassRequest.Value));
      KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlVendorClassRequest.Index));
      KdPrint((__DRIVER_NAME "      USB_REQUEST_%02x\n", urb->UrbControlVendorClassRequest.Request));
      urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
      WdfRequestComplete(request, STATUS_UNSUCCESSFUL); //STATUS_UNSUCCESSFUL);
      break;
    }
    break;
  case URB_FUNCTION_CLASS_OTHER:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_CLASS_OTHER\n"));
    KdPrint((__DRIVER_NAME "      TransferFlags = %08x\n", urb->UrbControlVendorClassRequest.TransferFlags));
    KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlVendorClassRequest.TransferBufferLength));
    KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlVendorClassRequest.TransferBuffer));
    KdPrint((__DRIVER_NAME "      TransferBufferMdl = %p\n", urb->UrbControlVendorClassRequest.TransferBufferMDL));
    KdPrint((__DRIVER_NAME "      RequestTypeReservedBits = %02x\n", urb->UrbControlVendorClassRequest.RequestTypeReservedBits));
    KdPrint((__DRIVER_NAME "      Request = %02x\n", urb->UrbControlVendorClassRequest.Request));
    KdPrint((__DRIVER_NAME "      Value = %04x\n", urb->UrbControlVendorClassRequest.Value));
    KdPrint((__DRIVER_NAME "      Index = %04x\n", urb->UrbControlVendorClassRequest.Index));
    switch (urb->UrbControlVendorClassRequest.Request)
    {
    case USB_REQUEST_GET_STATUS:
      /* port status - 11.24.2.7.1 */
      KdPrint((__DRIVER_NAME "      USB_REQUEST_GET_STATUS\n"));
      KdPrint((__DRIVER_NAME "       GetHubStatus\n"));
      ((PUSHORT)urb->UrbControlVendorClassRequest.TransferBuffer)[0] = xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_status;
      ((PUSHORT)urb->UrbControlVendorClassRequest.TransferBuffer)[1] = xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change;
      break;
    case USB_REQUEST_SET_FEATURE:
      KdPrint((__DRIVER_NAME "      USB_REQUEST_SET_FEATURE\n"));
      KdPrint((__DRIVER_NAME "       SetPortFeature\n"));
      switch (urb->UrbControlVendorClassRequest.Value)
      {
      case PORT_ENABLE:
        KdPrint((__DRIVER_NAME "        PORT_ENABLE\n"));
        /* do something here */
        break;
      case PORT_RESET:
        KdPrint((__DRIVER_NAME "        PORT_RESET\n"));
        /* just fake the reset */
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change |= (1 << C_PORT_RESET);
        break;
      default:
        KdPrint((__DRIVER_NAME "        Unknown Value %04X\n", urb->UrbControlVendorClassRequest.Value));
        break;
      }
      KdPrint((__DRIVER_NAME "        status = %04x, change = %04x\n",
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_status,
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change));
      break;
    case USB_REQUEST_CLEAR_FEATURE:
      KdPrint((__DRIVER_NAME "      USB_REQUEST_CLEAR_FEATURE\n"));
      KdPrint((__DRIVER_NAME "       ClearPortFeature\n"));
      switch (urb->UrbControlVendorClassRequest.Value)
      {
      case C_PORT_CONNECTION:
        KdPrint((__DRIVER_NAME "        C_PORT_CONNECTION\n"));
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change &= ~(1 << C_PORT_CONNECTION);
        break;
      case C_PORT_RESET:
        KdPrint((__DRIVER_NAME "        C_PORT_RESET\n"));
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change &= ~(1 << C_PORT_RESET);
        break;
      default:
        KdPrint((__DRIVER_NAME "        Unknown Value %04X\n", urb->UrbControlVendorClassRequest.Value));
        break;
      }
      KdPrint((__DRIVER_NAME "        status = %04x, change = %04x\n",
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_status,
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change));
      break;
    default:
      KdPrint((__DRIVER_NAME "      USB_REQUEST_%02x\n", urb->UrbControlVendorClassRequest.Request));
      break;
    }
    //urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
    //WdfRequestComplete(request, STATUS_SUCCESS);
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    WdfRequestComplete(request, STATUS_UNSUCCESSFUL); //STATUS_UNSUCCESSFUL);
    break;
  case URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER: /* 11.12.4 */
#if 1
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER\n"));
    KdPrint((__DRIVER_NAME "      PipeHandle = %p\n", urb->UrbBulkOrInterruptTransfer.PipeHandle));
    KdPrint((__DRIVER_NAME "      TransferFlags = %08x\n", urb->UrbBulkOrInterruptTransfer.TransferFlags));
    KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbBulkOrInterruptTransfer.TransferBufferLength));
    KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbBulkOrInterruptTransfer.TransferBuffer));
    KdPrint((__DRIVER_NAME "      TransferBufferMdl = %p\n", urb->UrbBulkOrInterruptTransfer.TransferBufferMDL));
#endif
    endpoint = urb->UrbBulkOrInterruptTransfer.PipeHandle;
    WdfSpinLockAcquire (endpoint->interrupt_lock);
    if (WdfIoQueueGetState(endpoint->interrupt_queue, NULL, NULL) & WdfIoQueueNoRequests)
    {
      status = WdfTimerStart(endpoint->interrupt_timer, WDF_REL_TIMEOUT_IN_MS(100));
    }
    status = WdfRequestForwardToIoQueue(request, endpoint->interrupt_queue);
    WdfSpinLockRelease(endpoint->interrupt_lock);
    break;
  case URB_FUNCTION_CONTROL_TRANSFER_EX:
    setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)urb->UrbControlTransfer.SetupPacket;
#if 1
    FUNCTION_MSG("URB_FUNCTION_CONTROL_TRANSFER_EX\n");
    FUNCTION_MSG(" PipeHandle = %p\n", urb->UrbControlTransfer.PipeHandle);
    FUNCTION_MSG(" TransferFlags = %08x\n", urb->UrbControlTransfer.TransferFlags);
    FUNCTION_MSG(" TransferBufferLength = %d\n", urb->UrbControlTransfer.TransferBufferLength);
    FUNCTION_MSG(" TransferBuffer = %p\n", urb->UrbControlTransfer.TransferBuffer);
    FUNCTION_MSG(" TransferBufferMdl = %p\n", urb->UrbControlTransfer.TransferBufferMDL);
    FUNCTION_MSG(" Timeout = %p\n", urb->UrbControlTransfer.TransferBufferMDL);
    FUNCTION_MSG(" SetupPacket.bmRequestType = %02x\n", (ULONG)setup_packet->bmRequestType.B);
    FUNCTION_MSG(" SetupPacket.bRequest = %02x\n", (ULONG)setup_packet->bRequest);
    FUNCTION_MSG(" SetupPacket.wValue.LowByte = %02x\n", (ULONG)setup_packet->wValue.LowByte);
    FUNCTION_MSG(" SetupPacket.wValue.HiByte = %02x\n", (ULONG)setup_packet->wValue.HiByte);
    FUNCTION_MSG(" SetupPacket.wIndex.LowByte = %02x\n", (ULONG)setup_packet->wIndex.LowByte);
    FUNCTION_MSG(" SetupPacket.wIndex.HiByte = %02x\n", (ULONG)setup_packet->wIndex.HiByte);
    FUNCTION_MSG(" SetupPacket.wLength = %04x\n", (ULONG)setup_packet->wLength);
#endif
    switch(setup_packet->bRequest)
    {
    case USB_REQUEST_GET_STATUS:
      FUNCTION_MSG(" USB_REQUEST_GET_STATUS\n");
      *(PUSHORT)urb->UrbControlDescriptorRequest.TransferBuffer = 0x0003;
      urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
      break;
    case USB_REQUEST_GET_DESCRIPTOR:
      // should be able to reuse this code...
      FUNCTION_MSG(" USB_REQUEST_GET_DESCRIPTOR\n");
      switch (setup_packet->wValue.HiByte)
      {
      case USB_DEVICE_DESCRIPTOR_TYPE:
        KdPrint((__DRIVER_NAME "      USB_DEVICE_DESCRIPTOR_TYPE\n"));
        memcpy(urb->UrbControlDescriptorRequest.TransferBuffer, &usb_device->device_descriptor, sizeof(USB_DEVICE_DESCRIPTOR));
        urb->UrbControlDescriptorRequest.TransferBufferLength = sizeof(USB_DEVICE_DESCRIPTOR);
        urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
        break;
      case USB_CONFIGURATION_DESCRIPTOR_TYPE:
      {
        xenusb_config_t *usb_config;
        PUCHAR ptr;

        KdPrint((__DRIVER_NAME "      USB_CONFIGURATION_DESCRIPTOR_TYPE\n"));
        usb_config = usb_device->active_config;
        ptr = (PUCHAR)urb->UrbControlDescriptorRequest.TransferBuffer;
        memcpy(ptr, &usb_config->config_descriptor, sizeof(USB_CONFIGURATION_DESCRIPTOR));
        ptr += sizeof(USB_CONFIGURATION_DESCRIPTOR);
        ((PUSB_CONFIGURATION_DESCRIPTOR)urb->UrbControlDescriptorRequest.TransferBuffer)->wTotalLength = sizeof(USB_CONFIGURATION_DESCRIPTOR);
        if (urb->UrbControlDescriptorRequest.TransferBufferLength > 9)
        {
          for (i = 0; i < usb_config->config_descriptor.bNumInterfaces; i++)
          {
            memcpy(ptr, &usb_config->interfaces[i]->interface_descriptor, sizeof(USB_INTERFACE_DESCRIPTOR));
            KdPrint((__DRIVER_NAME "      bInterfaceClass = %02x\n", ((PUSB_INTERFACE_DESCRIPTOR)ptr)->bInterfaceClass));
            ptr += sizeof(USB_INTERFACE_DESCRIPTOR);
            ((PUSB_CONFIGURATION_DESCRIPTOR)urb->UrbControlDescriptorRequest.TransferBuffer)->wTotalLength += sizeof(USB_INTERFACE_DESCRIPTOR);
            for (j = 0; j < usb_config->interfaces[i]->interface_descriptor.bNumEndpoints; j++)
            {
              memcpy(ptr, &usb_config->interfaces[i]->endpoints[j]->endpoint_descriptor, sizeof(USB_ENDPOINT_DESCRIPTOR));
              ptr += sizeof(USB_ENDPOINT_DESCRIPTOR);
              ((PUSB_CONFIGURATION_DESCRIPTOR)urb->UrbControlDescriptorRequest.TransferBuffer)->wTotalLength += sizeof(USB_ENDPOINT_DESCRIPTOR);
            }
          }
        }
        urb->UrbControlDescriptorRequest.TransferBufferLength = ((PUSB_CONFIGURATION_DESCRIPTOR)urb->UrbControlDescriptorRequest.TransferBuffer)->wTotalLength;
        if (urb->UrbControlDescriptorRequest.TransferBufferLength == 9)
          ((PUSB_CONFIGURATION_DESCRIPTOR)urb->UrbControlDescriptorRequest.TransferBuffer)->wTotalLength = 32;
        urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
        KdPrint((__DRIVER_NAME "      TransferBufferLength returned = %d\n", urb->UrbControlDescriptorRequest.TransferBufferLength));
        break;
      } 
      default:
        FUNCTION_MSG(" USB_%02x_DESCRIPTOR_TYPE\n", (ULONG)setup_packet->wValue.HiByte);
        break;
      }
      break;
    default:
      FUNCTION_MSG(" USB_REQUEST_%02x\n", (ULONG)setup_packet->bRequest);
      break;
    }
    KdPrint((__DRIVER_NAME "      TransferBufferLength returned = %d\n", urb->UrbControlDescriptorRequest.TransferBufferLength));
    WdfRequestComplete(request, STATUS_SUCCESS);
    break;
#endif
  case URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL:
  case URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER:
    //FUNCTION_MSG("NOT_CONTROL URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
    retval = URB_DECODE_NOT_CONTROL;
    break;
  default:
    FUNCTION_MSG("Unknown URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
    retval = URB_DECODE_UNKNOWN;
    break;
  }
  //FUNCTION_EXIT();
  return retval;
}

