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

#define DECODE_COMPUTE 0x40000000 /* calculate the value - not applicable to all fields */
#define DECODE_COPY    0x80000000 /* copy from URB */
/* otherwise literal value */

typedef struct {
  PCHAR urb_function_name;
  BOOLEAN is_simple_control;
  ULONG bmRequestTypeRecipient;
  ULONG bmRequestTypeType;
  ULONG bmRequestTypeDir;
  ULONG bRequest;
  ULONG wValueLow;
  ULONG wValueHigh;
  ULONG wIndexLow;
  ULONG wIndexHigh;
  ULONG wLength;
  ULONG transfer_flags;
} decode_t;

static decode_t decodes[] = {
  /* 0000 */
  {"URB_FUNCTION_SELECT_CONFIGURATION",             FALSE},
  {"URB_FUNCTION_SELECT_INTERFACE",                 FALSE},
  {"URB_FUNCTION_ABORT_PIPE",                       FALSE},
  {"URB_FUNCTION_TAKE_FRAME_LENGTH_CONTROL",        FALSE},
  {"URB_FUNCTION_RELEASE_FRAME_LENGTH_CONTROL",     FALSE},
  {"URB_FUNCTION_GET_FRAME_LENGTH",                 FALSE},
  {"URB_FUNCTION_SET_FRAME_LENGTH",                 FALSE},
  {"URB_FUNCTION_GET_CURRENT_FRAME_NUMBER",         FALSE},
  {"URB_FUNCTION_CONTROL_TRANSFER",                 TRUE, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER",       FALSE},
  {"URB_FUNCTION_ISOCH_TRANSFER",                   FALSE},
  {"URB_FUNCTION_GET_DESCRIPTOR_FROM_DEVICE",       TRUE, BMREQUEST_TO_DEVICE, BMREQUEST_STANDARD, BMREQUEST_DEVICE_TO_HOST, USB_REQUEST_GET_DESCRIPTOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_SET_DESCRIPTOR_TO_DEVICE",         FALSE},
  {"URB_FUNCTION_SET_FEATURE_TO_DEVICE",            FALSE},
  {"URB_FUNCTION_SET_FEATURE_TO_INTERFACE",         FALSE},
  {"URB_FUNCTION_SET_FEATURE_TO_ENDPOINT",          FALSE},
  /* 0010 */
  {"URB_FUNCTION_CLEAR_FEATURE_TO_DEVICE",          FALSE},
  {"URB_FUNCTION_CLEAR_FEATURE_TO_INTERFACE",       FALSE},
  {"URB_FUNCTION_CLEAR_FEATURE_TO_ENDPOINT",        FALSE},
  {"URB_FUNCTION_GET_STATUS_FROM_DEVICE",           FALSE},
  {"URB_FUNCTION_GET_STATUS_FROM_INTERFACE",        FALSE},
  {"URB_FUNCTION_GET_STATUS_FROM_ENDPOINT",         FALSE},
  {"URB_FUNCTION_RESERVED_0X0016",                  FALSE},
  {"URB_FUNCTION_VENDOR_DEVICE",                    TRUE, BMREQUEST_TO_DEVICE, BMREQUEST_VENDOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_VENDOR_INTERFACE",                 TRUE, BMREQUEST_TO_INTERFACE, BMREQUEST_VENDOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_VENDOR_ENDPOINT",                  TRUE, BMREQUEST_TO_ENDPOINT, BMREQUEST_VENDOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_CLASS_DEVICE",                     TRUE, BMREQUEST_TO_DEVICE, BMREQUEST_CLASS, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_CLASS_INTERFACE",                  TRUE, BMREQUEST_TO_INTERFACE, BMREQUEST_CLASS, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_CLASS_ENDPOINT",                   TRUE, BMREQUEST_TO_ENDPOINT, BMREQUEST_CLASS, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_RESERVE_0X001D",                   FALSE},
  {"URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL",  FALSE},
  {"URB_FUNCTION_CLASS_OTHER",                      TRUE, BMREQUEST_TO_OTHER, BMREQUEST_CLASS, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  /* 0020 */
  {"URB_FUNCTION_VENDOR_OTHER",                     TRUE, BMREQUEST_TO_OTHER, BMREQUEST_VENDOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_GET_STATUS_FROM_OTHER",            FALSE},
  {"URB_FUNCTION_CLEAR_FEATURE_TO_OTHER",           FALSE},
  {"URB_FUNCTION_SET_FEATURE_TO_OTHER",             FALSE},
  {"URB_FUNCTION_GET_DESCRIPTOR_FROM_ENDPOINT",     TRUE, BMREQUEST_TO_ENDPOINT, BMREQUEST_STANDARD, BMREQUEST_DEVICE_TO_HOST, USB_REQUEST_GET_DESCRIPTOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_SET_DESCRIPTOR_TO_ENDPOINT",       FALSE},
  {"URB_FUNCTION_GET_CONFIGURATION",                FALSE},
  {"URB_FUNCTION_GET_INTERFACE",                    FALSE},
  {"URB_FUNCTION_GET_DESCRIPTOR_FROM_INTERFACE",    TRUE, BMREQUEST_TO_INTERFACE, BMREQUEST_STANDARD, BMREQUEST_DEVICE_TO_HOST, USB_REQUEST_GET_DESCRIPTOR, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_SET_DESCRIPTOR_TO_INTERFACE",      FALSE},
  {"URB_FUNCTION_GET_MS_FEATURE_DESCRIPTOR",        FALSE},
  {"URB_FUNCTION_RESERVE_0X002B",                   FALSE},
  {"URB_FUNCTION_RESERVE_0X002C",                   FALSE},
  {"URB_FUNCTION_RESERVE_0X002D",                   FALSE},
  {"URB_FUNCTION_RESERVE_0X002E",                   FALSE},
  {"URB_FUNCTION_RESERVE_0X002F",                   FALSE},
  /* 0030 */
  {"URB_FUNCTION_SYNC_RESET_PIPE",                  FALSE},
  {"URB_FUNCTION_SYNC_CLEAR_STALL",                 FALSE},
  {"URB_FUNCTION_CONTROL_TRANSFER_EX",              TRUE, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COPY, DECODE_COMPUTE, DECODE_COMPUTE},
  {"URB_FUNCTION_RESERVE_0X0033",                   FALSE},
  {"URB_FUNCTION_RESERVE_0X0034",                   FALSE},
};

/*
decode all the funky URB_Xxx functions into a basic 8 byte SetupPacket
*/
ULONG
XenUsb_DecodeControlUrb(PURB urb, urb_decode_t *decode_data)
{
  ULONG retval;
  decode_t *decode;
  PUSB_DEFAULT_PIPE_SETUP_PACKET setup_packet;

  if (urb->UrbHeader.Function > ARRAY_SIZE(decodes)) {
    FUNCTION_MSG("Unknown URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
    return URB_DECODE_UNKNOWN;
  }
  decode = &decodes[urb->UrbHeader.Function];
  FUNCTION_MSG("decoding %s\n", decode->urb_function_name);
  
  if (decode->is_simple_control) {
    FUNCTION_MSG("is a simple control URB\n");
    
    setup_packet = (PUSB_DEFAULT_PIPE_SETUP_PACKET)urb->UrbControlTransfer.SetupPacket;
    
    if (decode->bmRequestTypeRecipient == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = setup_packet->bmRequestType.Recipient;
    else
      decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = (UCHAR)decode->bmRequestTypeRecipient;
    if (decode->bmRequestTypeType == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = setup_packet->bmRequestType.Type;
    else
      decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = (UCHAR)decode->bmRequestTypeType;
    if (decode->bmRequestTypeDir == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = setup_packet->bmRequestType.Dir;
    else
      decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = (UCHAR)decode->bmRequestTypeDir;

    if (decode->bRequest == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.bRequest = setup_packet->bRequest;
    else
      decode_data->setup_packet.default_pipe_setup_packet.bRequest = (UCHAR)decode->bRequest;
      
    if (decode->wValueLow == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.wValue.LowByte = setup_packet->wValue.LowByte;
    else
      decode_data->setup_packet.default_pipe_setup_packet.wValue.LowByte = (UCHAR)decode->wValueLow;

    if (decode->wValueHigh == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.wValue.HiByte = setup_packet->wValue.HiByte;
    else
      decode_data->setup_packet.default_pipe_setup_packet.wValue.HiByte = (UCHAR)decode->wValueHigh;

    if (decode->wIndexLow == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.wIndex.LowByte = setup_packet->wIndex.LowByte;
    else
      decode_data->setup_packet.default_pipe_setup_packet.wIndex.LowByte = (UCHAR)decode->wIndexLow;

    if (decode->wIndexHigh == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.wIndex.HiByte = setup_packet->wIndex.HiByte;
    else
      decode_data->setup_packet.default_pipe_setup_packet.wIndex.HiByte = (UCHAR)decode->wIndexHigh;

    if (decode->wLength == DECODE_COMPUTE)
      /* use buffer length */
      decode_data->setup_packet.default_pipe_setup_packet.wLength = (USHORT)urb->UrbControlTransfer.TransferBufferLength;
    else if (decode->wLength == DECODE_COPY)
      decode_data->setup_packet.default_pipe_setup_packet.wLength = setup_packet->wLength;
    else
      decode_data->setup_packet.default_pipe_setup_packet.wLength = (UCHAR)decode->wLength;

    if (decode->transfer_flags == DECODE_COMPUTE) {
      /* Fix up transfer_flags based on direction in bmRequest */
      if (decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir == BMREQUEST_DEVICE_TO_HOST)
        decode_data->transfer_flags = USBD_TRANSFER_DIRECTION_IN | USBD_SHORT_TRANSFER_OK;
      else
        decode_data->transfer_flags = 0;
    } else if (decode->transfer_flags == DECODE_COPY) {
      decode_data->transfer_flags = urb->UrbControlTransfer.TransferFlags;
    } else {
      decode_data->transfer_flags = decode->transfer_flags;
    }


    decode_data->buffer = urb->UrbControlTransfer.TransferBuffer;
    decode_data->mdl = urb->UrbControlTransfer.TransferBufferMDL;
    decode_data->length = &urb->UrbControlTransfer.TransferBufferLength;

    return URB_DECODE_COMPLETE;
  }
  
  //FUNCTION_ENTER();
  switch(urb->UrbHeader.Function)
  {
  case URB_FUNCTION_SELECT_CONFIGURATION:
    FUNCTION_MSG("URB_FUNCTION_SELECT_CONFIGURATION\n");
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = BMREQUEST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = BMREQUEST_STANDARD;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bRequest = USB_REQUEST_SET_CONFIGURATION;
    decode_data->setup_packet.default_pipe_setup_packet.wLength = 0;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.W = urb->UrbSelectConfiguration.ConfigurationDescriptor->bConfigurationValue;
    decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = 0;
    decode_data->transfer_flags = 0;
    decode_data->buffer = NULL;
    decode_data->mdl = NULL;
    retval = URB_DECODE_INCOMPLETE;
    break;
  case URB_FUNCTION_SELECT_INTERFACE:
    FUNCTION_MSG("URB_FUNCTION_SELECT_INTERFACE\n");
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Recipient = BMREQUEST_TO_INTERFACE;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Type = BMREQUEST_STANDARD;
    decode_data->setup_packet.default_pipe_setup_packet.bmRequestType.Dir = BMREQUEST_HOST_TO_DEVICE;
    decode_data->setup_packet.default_pipe_setup_packet.bRequest = USB_REQUEST_SET_INTERFACE;
    decode_data->setup_packet.default_pipe_setup_packet.wLength = 0;
    decode_data->setup_packet.default_pipe_setup_packet.wValue.W = urb->UrbSelectInterface.Interface.AlternateSetting;
    decode_data->setup_packet.default_pipe_setup_packet.wIndex.W = urb->UrbSelectInterface.Interface.InterfaceNumber;
    decode_data->transfer_flags = 0;
    decode_data->buffer = NULL;
    decode_data->mdl = NULL;
    retval = URB_DECODE_INCOMPLETE;
    break;
  case URB_FUNCTION_SYNC_RESET_PIPE_AND_CLEAR_STALL:
  case URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER:
  case URB_FUNCTION_ABORT_PIPE:
    FUNCTION_MSG("NOT_CONTROL URB_FUNCTION_%04x\n", urb->UrbHeader.Function);
    retval = URB_DECODE_NOT_CONTROL;
    break;
  default:
    FUNCTION_MSG("NOT IMPLEMENTED\n", urb->UrbHeader.Function);
    retval = URB_DECODE_UNKNOWN;
    break;
  }
  //FUNCTION_EXIT();
  return retval;
}

