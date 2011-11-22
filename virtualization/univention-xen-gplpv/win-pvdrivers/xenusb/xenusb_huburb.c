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

VOID
XenUsb_EvtIoInternalDeviceControl_ROOTHUB_SUBMIT_URB(
  WDFQUEUE queue,
  WDFREQUEST request,
  size_t output_buffer_length,
  size_t input_buffer_length,
  ULONG io_control_code)
{
  //NTSTATUS status;
  WDFDEVICE device = WdfIoQueueGetDevice(queue);
  PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(device);
  PXENUSB_DEVICE_DATA xudd = GetXudd(xupdd->wdf_device_bus_fdo);
  WDF_REQUEST_PARAMETERS wrp;
  PURB urb;
  PUSBD_INTERFACE_INFORMATION interface_information;
  ULONG i, j;
  xenusb_device_t *usb_device;
  xenusb_endpoint_t *endpoint;
  //USB_DEFAULT_PIPE_SETUP_PACKET setup_packet;
  urb_decode_t decode_data;
  ULONG decode_retval;

  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);
  UNREFERENCED_PARAMETER(io_control_code);

  //FUNCTION_ENTER();

  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  WdfRequestGetParameters(request, &wrp);

  urb = (PURB)wrp.Parameters.Others.Arg1;
  ASSERT(urb);
#if 0
  KdPrint((__DRIVER_NAME "     urb = %p\n", urb));
  KdPrint((__DRIVER_NAME "      Length = %d\n", urb->UrbHeader.Length));
  KdPrint((__DRIVER_NAME "      Function = %d\n", urb->UrbHeader.Function));
  KdPrint((__DRIVER_NAME "      Status = %d\n", urb->UrbHeader.Status));
  KdPrint((__DRIVER_NAME "      UsbdDeviceHandle = %p\n", urb->UrbHeader.UsbdDeviceHandle));
  KdPrint((__DRIVER_NAME "      UsbdFlags = %08x\n", urb->UrbHeader.UsbdFlags));
#endif
  usb_device = urb->UrbHeader.UsbdDeviceHandle;

  if (!usb_device)
    usb_device = xupdd->usb_device;

  decode_retval = XenUsb_DecodeControlUrb(urb, &decode_data);
  if (decode_retval == URB_DECODE_UNKNOWN)
  {
    FUNCTION_MSG("Calling WdfRequestCompletestatus with status = %08x\n", STATUS_UNSUCCESSFUL); //STATUS_UNSUCCESSFUL));
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
    return;
  }

  urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
  
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
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_SELECT_CONFIGURATION\n"));
    KdPrint((__DRIVER_NAME "      ConfigurationDescriptor = %p\n", urb->UrbSelectConfiguration.ConfigurationDescriptor));
    if (urb->UrbSelectConfiguration.ConfigurationDescriptor)
    {
      KdPrint((__DRIVER_NAME "       bLength = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bLength));
      KdPrint((__DRIVER_NAME "       bDescriptorType = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bDescriptorType));
      KdPrint((__DRIVER_NAME "       wTotalLength = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->wTotalLength));
      KdPrint((__DRIVER_NAME "       bNumInterfaces = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bNumInterfaces));
      KdPrint((__DRIVER_NAME "       bConfigurationValue = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bConfigurationValue));
      KdPrint((__DRIVER_NAME "       iConfiguration = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->iConfiguration));
      KdPrint((__DRIVER_NAME "       bmAttributes = %04x\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->bmAttributes));
      KdPrint((__DRIVER_NAME "       MaxPower = %d\n", urb->UrbSelectConfiguration.ConfigurationDescriptor->MaxPower));
    }
    KdPrint((__DRIVER_NAME "      ConfigurationHandle = %p\n", urb->UrbSelectConfiguration.ConfigurationHandle));
    if (urb->UrbSelectConfiguration.ConfigurationDescriptor)
    {
      urb->UrbSelectConfiguration.ConfigurationHandle = xupdd->usb_device->configs[0];
      interface_information = &urb->UrbSelectConfiguration.Interface;
      for (i = 0; i < urb->UrbSelectConfiguration.ConfigurationDescriptor->bNumInterfaces; i++)
      {
        KdPrint((__DRIVER_NAME "     InterfaceInformation[%d]\n", i));
        KdPrint((__DRIVER_NAME "      Length = %d\n", interface_information->Length));
        KdPrint((__DRIVER_NAME "      InterfaceNumber = %d\n", interface_information->InterfaceNumber));
        KdPrint((__DRIVER_NAME "      AlternateSetting = %d\n", interface_information->AlternateSetting));
        KdPrint((__DRIVER_NAME "      Class = %02x\n", (ULONG)interface_information->Class));
        KdPrint((__DRIVER_NAME "      SubClass = %02x\n", (ULONG)interface_information->SubClass));
        KdPrint((__DRIVER_NAME "      Protocol = %02x\n", (ULONG)interface_information->Protocol));
        KdPrint((__DRIVER_NAME "      Reserved = %02x\n", (ULONG)interface_information->Reserved));
        KdPrint((__DRIVER_NAME "      InterfaceHandle = %p\n", interface_information->InterfaceHandle));
        KdPrint((__DRIVER_NAME "      NumberOfPipes = %d\n", interface_information->NumberOfPipes));
        interface_information->InterfaceHandle = xupdd->usb_device->configs[0]->interfaces[0];
        interface_information->Class = 0x09;
        interface_information->SubClass = 0x00;
        interface_information->SubClass = 0x00;
        for (j = 0; j < interface_information->NumberOfPipes; j++)
        {
          KdPrint((__DRIVER_NAME "      Pipe[%d]\n", i));
          KdPrint((__DRIVER_NAME "       MaximumPacketSize = %d\n", interface_information->Pipes[j].MaximumPacketSize));
          KdPrint((__DRIVER_NAME "       EndpointAddress = %d\n", interface_information->Pipes[j].EndpointAddress));
          KdPrint((__DRIVER_NAME "       Interval = %d\n", interface_information->Pipes[j].Interval));
          KdPrint((__DRIVER_NAME "       PipeType = %d\n", interface_information->Pipes[j].PipeType));
          KdPrint((__DRIVER_NAME "       PipeHandle = %d\n", interface_information->Pipes[j].PipeHandle));
          KdPrint((__DRIVER_NAME "       MaximumTransferSize = %d\n", interface_information->Pipes[j].MaximumTransferSize));
          KdPrint((__DRIVER_NAME "       PipeFlags = %08x\n", interface_information->Pipes[j].PipeFlags));
          interface_information->Pipes[j].MaximumPacketSize = 2;
          interface_information->Pipes[j].EndpointAddress = 0x81;
          interface_information->Pipes[j].Interval = 12;
          interface_information->Pipes[j].PipeType = UsbdPipeTypeInterrupt;
          interface_information->Pipes[j].PipeHandle = xupdd->usb_device->configs[0]->interfaces[0]->endpoints[j];
          interface_information->Pipes[j].MaximumTransferSize = 4096; /* made up number - possibly not used */
          // this is input actually interface_information->Pipes[j].PipeFlags = 0;
        }
        interface_information = (PUSBD_INTERFACE_INFORMATION)((PUCHAR)interface_information + interface_information->Length);
      }
    }
    urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
    break;
  case URB_FUNCTION_SELECT_INTERFACE:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_SELECT_INTERFACE\n"));
    interface_information = &urb->UrbSelectInterface.Interface;
    KdPrint((__DRIVER_NAME "     InterfaceInformation\n"));
    KdPrint((__DRIVER_NAME "      Length = %d\n", interface_information->Length));
    KdPrint((__DRIVER_NAME "      InterfaceNumber = %d\n", interface_information->InterfaceNumber));
    KdPrint((__DRIVER_NAME "      AlternateSetting = %d\n", interface_information->AlternateSetting));
    KdPrint((__DRIVER_NAME "      Class = %02x\n", (ULONG)interface_information->Class));
    KdPrint((__DRIVER_NAME "      SubClass = %02x\n", (ULONG)interface_information->SubClass));
    KdPrint((__DRIVER_NAME "      Protocol = %02x\n", (ULONG)interface_information->Protocol));
    KdPrint((__DRIVER_NAME "      Reserved = %02x\n", (ULONG)interface_information->Reserved));
    KdPrint((__DRIVER_NAME "      InterfaceHandle = %p\n", interface_information->InterfaceHandle));
    KdPrint((__DRIVER_NAME "      NumberOfPipes = %d\n", interface_information->NumberOfPipes));
    for (i = 0; i < interface_information->NumberOfPipes; i++)
    {
      KdPrint((__DRIVER_NAME "      Pipe[%d]\n", i));
      KdPrint((__DRIVER_NAME "       MaximumPacketSize = %d\n", interface_information->Pipes[i].MaximumPacketSize));
      KdPrint((__DRIVER_NAME "       EndpointAddress = %d\n", interface_information->Pipes[i].EndpointAddress));
      KdPrint((__DRIVER_NAME "       Interval = %d\n", interface_information->Pipes[i].Interval));
      KdPrint((__DRIVER_NAME "       PipeType = %d\n", interface_information->Pipes[i].PipeType));
      KdPrint((__DRIVER_NAME "       PipeHandle = %d\n", interface_information->Pipes[i].PipeHandle));
      KdPrint((__DRIVER_NAME "       MaximumTransferSize = %d\n", interface_information->Pipes[i].MaximumTransferSize));
      KdPrint((__DRIVER_NAME "       PipeFlags = %08x\n", interface_information->Pipes[i].PipeFlags));
    }
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    break;
#if (NTDDI_VERSION >= NTDDI_VISTA)  
  case URB_FUNCTION_CONTROL_TRANSFER_EX:
#endif
  case URB_FUNCTION_CONTROL_TRANSFER:
  case URB_FUNCTION_CLASS_DEVICE:
  case URB_FUNCTION_CLASS_OTHER:
  case URB_FUNCTION_GET_DESCRIPTOR_FROM_DEVICE:
  case URB_FUNCTION_GET_STATUS_FROM_DEVICE:
    switch(decode_data.setup_packet.default_pipe_setup_packet.bRequest)
    {
    case USB_REQUEST_GET_STATUS:
      // switch device, interface, endpoint
      switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type)
      {
      case BMREQUEST_STANDARD:
        FUNCTION_MSG(" USB_REQUEST_GET_STATUS\n");
        FUNCTION_MSG(" Type=Standard\n");
        switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient)
        {
        case BMREQUEST_TO_DEVICE:
          KdPrint((__DRIVER_NAME "       Recipient=Device\n"));
          ((PUSHORT)decode_data.buffer)[0] = 0x0001; /* self powered */
          urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
          break;
        default:
          FUNCTION_MSG(" Recipient=%d\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient);
          break;
        }
        break;
      case BMREQUEST_CLASS:
        switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient)
        {
        case BMREQUEST_TO_DEVICE:
          ((PUSHORT)decode_data.buffer)[0] = 0x0000;
          ((PUSHORT)decode_data.buffer)[1] = 0x0000;
          urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
          break;
        case BMREQUEST_TO_OTHER:
          FUNCTION_MSG(" USB_REQUEST_GET_STATUS\n");
          FUNCTION_MSG(" Type=Class\n");
          KdPrint((__DRIVER_NAME "       Recipient=Other (port = %d)\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte));
          ((PUSHORT)decode_data.buffer)[0] = xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status;
          ((PUSHORT)decode_data.buffer)[1] = xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_change;
          urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
          FUNCTION_MSG(" status = %04x, change = %04x\n",
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status,
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_change);
          break;
        default:
          FUNCTION_MSG(" USB_REQUEST_GET_STATUS\n");
          FUNCTION_MSG(" Type=Class\n");
          FUNCTION_MSG(" Recipient=%d\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient);
          break;
        }
        break;
      default:
        FUNCTION_MSG(" USB_REQUEST_GET_STATUS\n");
        FUNCTION_MSG(" Type=%d\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type);
        break;
      }
      break;      
    case USB_REQUEST_GET_DESCRIPTOR:
      FUNCTION_MSG(" USB_REQUEST_GET_DESCRIPTOR\n");
      // should separate into Standard and Class
      switch (decode_data.setup_packet.default_pipe_setup_packet.wValue.HiByte)
      {
      case USB_DEVICE_DESCRIPTOR_TYPE:
        FUNCTION_MSG(" USB_DEVICE_DESCRIPTOR_TYPE\n");
        FUNCTION_MSG(" length = %d\n", *decode_data.length);
        memcpy(decode_data.buffer, &usb_device->device_descriptor, sizeof(USB_DEVICE_DESCRIPTOR));
        *decode_data.length = sizeof(USB_DEVICE_DESCRIPTOR);
        urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
        break;
      case USB_CONFIGURATION_DESCRIPTOR_TYPE:
      {
        xenusb_config_t *usb_config;
        PUCHAR ptr;

        FUNCTION_MSG(" USB_CONFIGURATION_DESCRIPTOR_TYPE\n");
        FUNCTION_MSG(" length = %d\n", *decode_data.length);
        usb_config = usb_device->active_config;
        ptr = (PUCHAR)decode_data.buffer;
        memcpy(ptr, &usb_config->config_descriptor, sizeof(USB_CONFIGURATION_DESCRIPTOR));
        ptr += sizeof(USB_CONFIGURATION_DESCRIPTOR);
        ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength = sizeof(USB_CONFIGURATION_DESCRIPTOR);
        if (*decode_data.length > 9)
        {
          for (i = 0; i < usb_config->config_descriptor.bNumInterfaces; i++)
          {
            memcpy(ptr, &usb_config->interfaces[i]->interface_descriptor, sizeof(USB_INTERFACE_DESCRIPTOR));
            ptr += sizeof(USB_INTERFACE_DESCRIPTOR);
            ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength += sizeof(USB_INTERFACE_DESCRIPTOR);
            for (j = 0; j < usb_config->interfaces[i]->interface_descriptor.bNumEndpoints; j++)
            {
              memcpy(ptr, &usb_config->interfaces[i]->endpoints[j]->endpoint_descriptor, sizeof(USB_ENDPOINT_DESCRIPTOR));
              ptr += sizeof(USB_ENDPOINT_DESCRIPTOR);
              ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength += sizeof(USB_ENDPOINT_DESCRIPTOR);
            }
          }
        }
        *decode_data.length = ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength;
        //if (urb->UrbControlDescriptorRequest.TransferBufferLength == 9)
        //  ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength = 32;
        urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
        break;
      } 
      case 0x00: // unknown... doing the same as 0x29 seems to work
        FUNCTION_MSG(" USB_00_DESCRIPTOR_TYPE (doesn't exist)\n");
        urb->UrbHeader.Status = USBD_STATUS_BAD_DESCRIPTOR;
        break;
      case 0x29: // Hub Descriptor
      {
        PUSB_HUB_DESCRIPTOR uhd;
        
        FUNCTION_MSG(" USB_HUB_DESCRIPTOR_TYPE\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.HiByte);
        FUNCTION_MSG(" length = %d\n", *decode_data.length);
        uhd = decode_data.buffer;
        // TODO adjust for real number of ports
        *decode_data.length = FIELD_OFFSET(USB_HUB_DESCRIPTOR, bRemoveAndPowerMask[0]) + 2 + 1;
        uhd->bDescriptorLength = (UCHAR)*decode_data.length;
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
        break;
      }
      default:
        FUNCTION_MSG(" USB_%02x_DESCRIPTOR_TYPE\n", (ULONG)decode_data.setup_packet.default_pipe_setup_packet.wValue.HiByte);
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
        break;
      }
      break;
    case USB_REQUEST_CLEAR_FEATURE:
      FUNCTION_MSG(" USB_REQUEST_CLEAR_FEATURE\n");
      switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type)
      {
      case BMREQUEST_STANDARD: /* Standard */
        KdPrint((__DRIVER_NAME "       Type=Standard (unsupported)\n"));
        break;
      case BMREQUEST_CLASS: /* Class */
        KdPrint((__DRIVER_NAME "       Type=Class\n"));
        switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient)
        {
        case BMREQUEST_TO_OTHER:
          KdPrint((__DRIVER_NAME "       Recipient=Other (port = %d)\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte));
          switch (urb->UrbControlVendorClassRequest.Value)
          {
          case PORT_ENABLE:
            KdPrint((__DRIVER_NAME "        PORT_ENABLE\n"));
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status &= ~(1 << PORT_ENABLE);
            urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
            break;
          case C_PORT_CONNECTION:
            KdPrint((__DRIVER_NAME "        C_PORT_CONNECTION\n"));
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_change &= ~(1 << PORT_CONNECTION);
            urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
            break;
          case C_PORT_RESET:
            KdPrint((__DRIVER_NAME "        C_PORT_RESET\n"));
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_change &= ~(1 << PORT_RESET);
            urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
            break;
          default:
            KdPrint((__DRIVER_NAME "        Unknown Value %04X\n", urb->UrbControlVendorClassRequest.Value));
            break;
          }
          KdPrint((__DRIVER_NAME "        status = %04x, change = %04x\n",
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status,
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_change));
          break;
        default:
          FUNCTION_MSG(" Recipient=%d\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient);
          break;
        }
        break;
      default:
        KdPrint((__DRIVER_NAME "       Type=%d\n", decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type));
        break;
      }
      break;
    case USB_REQUEST_SET_FEATURE:
      KdPrint((__DRIVER_NAME "      USB_REQUEST_SET_FEATURE\n"));
      KdPrint((__DRIVER_NAME "       SetPortFeature\n"));
      switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Type)
      {
      case 0: /* Standard */
        KdPrint((__DRIVER_NAME "       Type=Standard (unsupported)\n"));
        break;
      case 1: /* Class */
        KdPrint((__DRIVER_NAME "       Type=Class\n"));
        switch (decode_data.setup_packet.default_pipe_setup_packet.bmRequestType.Recipient)
        {
        case BMREQUEST_TO_OTHER:
          KdPrint((__DRIVER_NAME "       Recipient=Other (port = %d)\n", decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte));
          switch (decode_data.setup_packet.default_pipe_setup_packet.wValue.W)
          {
          case PORT_ENABLE:
            KdPrint((__DRIVER_NAME "        PORT_ENABLE (NOOP)\n"));
            /* do something here */
            urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
            break;
          case PORT_RESET:
            KdPrint((__DRIVER_NAME "        PORT_RESET\n"));
            /* just fake the reset by setting the status bit to indicate that the reset is complete*/
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status |= (1 << PORT_RESET);
            //xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].reset_counter = 10;
            // TODO: maybe fake a 10ms time here...
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status &= ~(1 << PORT_RESET);
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status |= (1 << PORT_ENABLE);
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_change |= (1 << PORT_RESET);
            urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
            endpoint = xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0];
            XenUsbHub_ProcessHubInterruptEvent(endpoint);
            break;
          case PORT_POWER:
            KdPrint((__DRIVER_NAME "        PORT_POWER\n"));
            xudd->ports[decode_data.setup_packet.default_pipe_setup_packet.wIndex.LowByte - 1].port_status |= (1 << PORT_POWER);
            urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
            break;
          default:
            KdPrint((__DRIVER_NAME "        PORT_%04X\n", decode_data.setup_packet.default_pipe_setup_packet.wValue.W));
            break;
          }
          KdPrint((__DRIVER_NAME "        status = %04x, change = %04x\n",
            xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_status,
            xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change));
          break;
        }
        break;
      }
      break;
    default:
      FUNCTION_MSG(" USB_REQUEST_%02x\n", (ULONG)decode_data.setup_packet.default_pipe_setup_packet.bRequest);
      KdPrint((__DRIVER_NAME "      TransferBufferLength returned = %d\n", urb->UrbControlDescriptorRequest.TransferBufferLength));
      break;
    }
    break;
  case URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL\n"));
    KdPrint((__DRIVER_NAME "      PipeHandle = %p\n", urb->UrbPipeRequest.PipeHandle));
    urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
    break;
  case URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER: /* 11.12.4 */
#if 0
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER\n"));
    KdPrint((__DRIVER_NAME "      PipeHandle = %p\n", urb->UrbBulkOrInterruptTransfer.PipeHandle));
    KdPrint((__DRIVER_NAME "      TransferFlags = %08x\n", urb->UrbBulkOrInterruptTransfer.TransferFlags));
    KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbBulkOrInterruptTransfer.TransferBufferLength));
    KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbBulkOrInterruptTransfer.TransferBuffer));
    KdPrint((__DRIVER_NAME "      TransferBufferMdl = %p\n", urb->UrbBulkOrInterruptTransfer.TransferBufferMDL));
#endif
    endpoint = urb->UrbBulkOrInterruptTransfer.PipeHandle;
    //WdfSpinLockAcquire(endpoint->lock);
    WdfRequestForwardToIoQueue(request, endpoint->queue);
    XenUsbHub_ProcessHubInterruptEvent(endpoint);
    //WdfSpinLockRelease(endpoint->lock);
    //FUNCTION_EXIT();
    return;
    
#if 0 // not using this bit
  case URB_FUNCTION_GET_DESCRIPTOR_FROM_DEVICE:
  //case URB_FUNCTION_GET_DESCRIPTOR_FROM_ENDPOINT:
  //case URB_FUNCTION_GET_DESCRIPTOR_FROM_INTERFACE:
    KdPrint((__DRIVER_NAME "     URB_FUNCTION_GET_DESCRIPTOR_FROM_XXX\n"));
    KdPrint((__DRIVER_NAME "      Reserved = %p\n", urb->UrbControlDescriptorRequest.Reserved));
    KdPrint((__DRIVER_NAME "      Reserved0 = %08X\n", urb->UrbControlDescriptorRequest.Reserved0));
    KdPrint((__DRIVER_NAME "      TransferBufferLength = %d\n", urb->UrbControlDescriptorRequest.TransferBufferLength));
    KdPrint((__DRIVER_NAME "      TransferBuffer = %p\n", urb->UrbControlDescriptorRequest.TransferBuffer));
    KdPrint((__DRIVER_NAME "      TransferBufferMDL = %p\n", urb->UrbControlDescriptorRequest.TransferBufferMDL));
    KdPrint((__DRIVER_NAME "      UrbLink = %p\n", urb->UrbControlDescriptorRequest.UrbLink));
    KdPrint((__DRIVER_NAME "      Index = %d\n", (int)urb->UrbControlDescriptorRequest.Index));
    KdPrint((__DRIVER_NAME "      DescriptorType = %d\n", (int)urb->UrbControlDescriptorRequest.DescriptorType));
    KdPrint((__DRIVER_NAME "      LanguageId = %04x\n", urb->UrbControlDescriptorRequest.LanguageId));
    KdPrint((__DRIVER_NAME "      Reserved2 = %04X\n", urb->UrbControlDescriptorRequest.Reserved2));
    switch (urb->UrbControlDescriptorRequest.DescriptorType)
    {
    case USB_DEVICE_DESCRIPTOR_TYPE:
      KdPrint((__DRIVER_NAME "      USB_DEVICE_DESCRIPTOR_TYPE\n"));
      memcpy(urb->UrbControlDescriptorRequest.TransferBuffer, &usb_device->device_descriptor, sizeof(USB_DEVICE_DESCRIPTOR));
      urb->UrbControlDescriptorRequest.TransferBufferLength = sizeof(USB_DEVICE_DESCRIPTOR);
      KdPrint((__DRIVER_NAME "      TransferBufferLength returned = %d\n", urb->UrbControlDescriptorRequest.TransferBufferLength));
      break;
    case USB_CONFIGURATION_DESCRIPTOR_TYPE:
    {
      xenusb_config_t *usb_config;
      PUCHAR ptr;

      KdPrint((__DRIVER_NAME "      USB_CONFIGURATION_DESCRIPTOR_TYPE\n"));
      usb_config = usb_device->active_config;
      ptr = (PUCHAR)decode_data.buffer;
      memcpy(ptr, &usb_config->config_descriptor, sizeof(USB_CONFIGURATION_DESCRIPTOR));
      ptr += sizeof(USB_CONFIGURATION_DESCRIPTOR);
      ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength = sizeof(USB_CONFIGURATION_DESCRIPTOR);
      if (urb->UrbControlDescriptorRequest.TransferBufferLength > 9)
      {
        for (i = 0; i < usb_config->config_descriptor.bNumInterfaces; i++)
        {
          memcpy(ptr, &usb_config->interfaces[i]->interface_descriptor, sizeof(USB_INTERFACE_DESCRIPTOR));
          KdPrint((__DRIVER_NAME "      bInterfaceClass = %02x\n", ((PUSB_INTERFACE_DESCRIPTOR)ptr)->bInterfaceClass));
          ptr += sizeof(USB_INTERFACE_DESCRIPTOR);
          ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength += sizeof(USB_INTERFACE_DESCRIPTOR);
          for (j = 0; j < usb_config->interfaces[i]->interface_descriptor.bNumEndpoints; j++)
          {
            memcpy(ptr, &usb_config->interfaces[i]->endpoints[j]->endpoint_descriptor, sizeof(USB_ENDPOINT_DESCRIPTOR));
            ptr += sizeof(USB_ENDPOINT_DESCRIPTOR);
            ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength += sizeof(USB_ENDPOINT_DESCRIPTOR);
          }
        }
      }
      *decode_data.length = ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength;
      if (*decode_data.length == 9)
        ((PUSB_CONFIGURATION_DESCRIPTOR)decode_data.buffer)->wTotalLength = 32;
      KdPrint((__DRIVER_NAME "      TransferBufferLength returned = %d\n", urb->UrbControlDescriptorRequest.TransferBufferLength));
      break;
    } 
    default:
      KdPrint((__DRIVER_NAME "      UNKNOWN_DESCRIPTOR_TYPE\n"));
      break;
    }
    urb->UrbHeader.Status = USBD_STATUS_SUCCESS;
    break;
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
    }
    else
    {
      KdPrint((__DRIVER_NAME "     Unknown Index\n"));
      urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
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
        break;
      default:
        KdPrint((__DRIVER_NAME "       Unknown Value %02x\n", urb->UrbControlVendorClassRequest.Value >> 8));
        urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
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
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change |= (1 << PORT_RESET);
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
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change &= ~(1 << PORT_CONNECTION);
        break;
      case C_PORT_RESET:
        KdPrint((__DRIVER_NAME "        C_PORT_RESET\n"));
        xudd->ports[urb->UrbControlVendorClassRequest.Index - 1].port_change &= ~(1 << PORT_RESET);
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
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    break;
#endif
  default:
    FUNCTION_MSG("URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
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
    urb->UrbHeader.Status = USBD_STATUS_INVALID_URB_FUNCTION;
    break;
  }
  if (urb->UrbHeader.Status == USBD_STATUS_SUCCESS)
  {
    //FUNCTION_MSG("Calling WdfRequestCompletestatus with status = %08x\n", STATUS_SUCCESS);
    WdfRequestComplete(request, STATUS_SUCCESS);
  }
  else
  {
    FUNCTION_MSG("Calling WdfRequestCompletestatus with status = %08x\n", STATUS_UNSUCCESSFUL);
    WdfRequestComplete(request, STATUS_UNSUCCESSFUL);
  }

  //FUNCTION_EXIT();
  return;
}

