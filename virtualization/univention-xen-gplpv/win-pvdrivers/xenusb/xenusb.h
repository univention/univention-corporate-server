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

#pragma warning(disable: 4127)

#pragma warning(disable : 4200) // zero-sized array

#if !defined(_XENUSB_H_)
#define _XENUSB_H_

#define __attribute__(arg) /* empty */
#define EISCONN 127

#include <ntifs.h>
#include <ntddk.h>

#define DDKAPI
//#include <wdm.h>
#include <wdf.h>
#include <initguid.h>
#include <wdmguid.h>
#include <errno.h>
#define NTSTRSAFE_LIB
#include <ntstrsafe.h>

#define __DRIVER_NAME "XenUSB"

#include <xen_windows.h>
#include <io/ring.h>
#include <io/usbif.h>
#include <io/xenbus.h>
#include <usb.h>
#include <usbioctl.h>
#include <usbdlib.h>
#include <hubbusif.h>
#include <usbbusif.h>

#define C_HUB_LOCAL_POWER   0
#define C_HUB_OVER_CURRENT  1
#define PORT_CONNECTION     0
#define PORT_ENABLE         1
#define PORT_SUSPEND        2
#define PORT_OVER_CURRENT   3
#define PORT_RESET          4
#define PORT_POWER          8
#define PORT_LOW_SPEED      9
#define PORT_HIGH_SPEED     10
#define C_PORT_CONNECTION   16
#define C_PORT_ENABLE       17
#define C_PORT_SUSPEND      18
#define C_PORT_OVER_CURRENT 19
#define C_PORT_RESET        20
#define PORT_TEST           21
#define PORT_INDICATOR      22

#define XENUSB_POOL_TAG (ULONG)'XenU'

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

#define CHILD_STATE_EMPTY 0
#define CHILD_STATE_DELETED 1
#define CHILD_STATE_ADDED 2

#define LINUX_PIPE_DIRECTION_OUT 0x00000000
#define LINUX_PIPE_DIRECTION_IN  0x00000080

/* these are linux definitions - different to usb standard */
#define LINUX_PIPE_TYPE_ISOC     0x00000000
#define LINUX_PIPE_TYPE_INTR     0x40000000
#define LINUX_PIPE_TYPE_CTRL     0x80000000
#define LINUX_PIPE_TYPE_BULK     0xC0000000

/*
 * urb->transfer_flags:
 */
#define LINUX_URB_SHORT_NOT_OK        0x0001  /* report short reads as errors */
#define LINUX_URB_ISO_ASAP            0x0002  /* iso-only, urb->start_frame ignored */
#define LINUX_URB_NO_TRANSFER_DMA_MAP 0x0004  /* urb->transfer_dma valid on submit */
#define LINUX_URB_NO_SETUP_DMA_MAP    0x0008  /* urb->setup_dma valid on submit */
#define LINUX_URB_NO_FSBR             0x0020  /* UHCI-specific */
#define LINUX_URB_ZERO_PACKET         0x0040  /* Finish bulk OUT with short packet */
#define LINUX_URB_NO_INTERRUPT        0x0080  /* HINT: no non-error interrupt needed */

#define PRE_DECLARE_TYPE_TYPEDEF(x) struct _##x; typedef struct _##x x##_t

#if 0
struct _usbif_shadow;
typedef struct _usbif_shadow usbif_shadow_t;
#endif

PRE_DECLARE_TYPE_TYPEDEF(usbif_shadow);

struct _usbif_shadow {
  uint16_t id;
  union
  {
    struct {
      WDFREQUEST request;
      PURB urb;
    };
    KEVENT event;
  };
  //WDFDMATRANSACTION dma_transaction;
  PMDL mdl;
  ULONG total_length;
  /* called at DISPATCH_LEVEL */
  VOID (*callback)(usbif_shadow_t *);
  usbif_urb_request_t req;
  usbif_urb_response_t rsp;
  usbif_shadow_t *next; /* for gathering shadows from the ring for callback */
};

#define MAX_SHADOW_ENTRIES 64
#define SHADOW_ENTRIES min(MAX_SHADOW_ENTRIES, USB_URB_RING_SIZE)

struct _xenusb_endpoint_t;
struct _xenusb_interface_t;
struct _xenusb_config_t;
struct _xenusb_device_t;
typedef struct _xenusb_endpoint_t xenusb_endpoint_t, *pxenusb_endpoint_t;
typedef struct _xenusb_interface_t xenusb_interface_t;
typedef struct _xenusb_config_t xenusb_config_t;
typedef struct _xenusb_device_t xenusb_device_t;

typedef struct _xenusb_endpoint_t {
  xenusb_interface_t *interface;
  ULONG pipe_value;
  //WDFTIMER interrupt_timer;
  WDFQUEUE queue;
  WDFSPINLOCK lock;
  USB_ENDPOINT_DESCRIPTOR endpoint_descriptor;
};
//WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(pxenusb_endpoint_t, GetEndpoint)

typedef struct _xenusb_interface_t {
  //ULONG pipe_value;
  xenusb_config_t *config;
  USB_INTERFACE_DESCRIPTOR interface_descriptor;
  xenusb_endpoint_t *endpoints[0];
} xenusb_interface_t;

typedef struct _xenusb_config_t {
  xenusb_device_t *device;
  USB_CONFIGURATION_DESCRIPTOR config_descriptor;
  xenusb_interface_t *interfaces[0];
} xenusb_config_t;

typedef struct _xenusb_device_t {
  WDFDEVICE pdo_device;
  UCHAR address;
  USB_DEVICE_DESCRIPTOR device_descriptor;
  ULONG port_number;
  WDFQUEUE urb_queue;
  USB_DEVICE_SPEED device_speed;
  USB_DEVICE_TYPE device_type;
  xenusb_config_t *active_config;
  xenusb_interface_t *active_interface;
  xenusb_config_t **configs; /* pointer to an array of configs */
} xenusb_device_t;

#define USB_PORT_TYPE_NOT_CONNECTED 0
#define USB_PORT_TYPE_LOW_SPEED     1
#define USB_PORT_TYPE_FULL_SPEED    2
#define USB_PORT_TYPE_HIGH_SPEED    3

typedef struct
{
  ULONG port_number;
  ULONG port_type;
  USHORT port_status;
  USHORT port_change;
  ULONG reset_counter;
} xenusb_port_t;

typedef struct {  
  BOOLEAN XenBus_ShuttingDown;
  WDFQUEUE io_queue;
  //WDFDMAENABLER dma_enabler;
  
  WDFCHILDLIST child_list;
  
  WDFDEVICE root_hub_device;

  usbif_shadow_t shadows[MAX_SHADOW_ENTRIES];
  USHORT shadow_free_list[MAX_SHADOW_ENTRIES];
  USHORT shadow_free;

  PUCHAR config_page;

  /* protected by conn_ring_lock */  
  ULONG num_ports;
  xenusb_port_t ports[32];

  KSPIN_LOCK urb_ring_lock;
  usbif_urb_sring_t *urb_sring;
  usbif_urb_front_ring_t urb_ring;

  KSPIN_LOCK conn_ring_lock;
  usbif_conn_sring_t *conn_sring;
  usbif_conn_front_ring_t conn_ring;

  evtchn_port_t event_channel;

  XENPCI_VECTORS vectors;
  PXENPCI_DEVICE_STATE device_state;

} XENUSB_DEVICE_DATA, *PXENUSB_DEVICE_DATA;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(XENUSB_DEVICE_DATA, GetXudd)

typedef struct {  
  WDFDEVICE wdf_device;
  WDFDEVICE wdf_device_bus_fdo;
  WDFQUEUE io_queue;
  WDFQUEUE urb_queue;
  ULONG device_number;
  //ULONG port_number;
  //ULONG port_type;
  xenusb_device_t *usb_device;
  PVOID BusCallbackContext;
  PRH_INIT_CALLBACK BusCallbackFunction;

} XENUSB_PDO_DEVICE_DATA, *PXENUSB_PDO_DEVICE_DATA;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(XENUSB_PDO_DEVICE_DATA, GetXupdd)

#if 0
typedef struct {
  UCHAR usb_class;
  UCHAR usb_subclass;
  UCHAR usb_protocol;
} xenusb_compatible_id_details_t;
#endif

typedef struct {
  WDF_CHILD_IDENTIFICATION_DESCRIPTION_HEADER header;
  ULONG device_number;
  //ULONG port_number;
  //ULONG port_type;
  //USHORT vendor_id;
  //USHORT product_id;
  //xenusb_compatible_id_details_t xucid[1];
} XENUSB_PDO_IDENTIFICATION_DESCRIPTION, *PXENUSB_PDO_IDENTIFICATION_DESCRIPTION;

static usbif_shadow_t *
get_shadow_from_freelist(PXENUSB_DEVICE_DATA xudd)
{
  if (xudd->shadow_free == 0)
  {
    KdPrint((__DRIVER_NAME "     No more shadow entries\n"));
    return NULL;
  }
  xudd->shadow_free--;
  return &xudd->shadows[xudd->shadow_free_list[xudd->shadow_free]];
}

static VOID
put_shadow_on_freelist(PXENUSB_DEVICE_DATA xudd, usbif_shadow_t *shadow)
{
  xudd->shadow_free_list[xudd->shadow_free] = (USHORT)shadow->id;
  shadow->request = NULL;
  xudd->shadow_free++;
}

static
ULONGLONG parse_numeric_string(PCHAR string)
{
  ULONGLONG val = 0;
  while (*string != 0)
  {
    val = val * 10 + (*string - '0');
    string++;
  }
  return val;
}

#if 0
static VOID
XenUsb_PutRequest(PXENVBD_DEVICE_DATA xudd, usbif_request_t *req)
{
  *RING_GET_REQUEST(&xudd->ring, xudd->ring.req_prod_pvt) = *req;
  xudd->ring.req_prod_pvt++;
}

static usbif_request_t *
XenUsb_GetResponse(PXENVBD_DEVICE_DATA xudd, ULONG i)
{
  return RING_GET_RESPONSE(&xvdd->ring, i);
}
#endif


/*
EVT_WDF_DEVICE_PREPARE_HARDWARE XenUsb_EvtDevicePrepareHardware;
EVT_WDF_DEVICE_RELEASE_HARDWARE XenUsb_EvtDeviceReleaseHardware;
EVT_WDF_DEVICE_D0_ENTRY XenUsb_EvtDeviceD0Entry;
EVT_WDF_DEVICE_D0_ENTRY_POST_INTERRUPTS_ENABLED XenUsb_EvtDeviceD0EntryPostInterruptsEnabled;
EVT_WDF_DEVICE_D0_EXIT XenUsb_EvtDeviceD0Exit;
EVT_WDF_DEVICE_D0_EXIT_PRE_INTERRUPTS_DISABLED XenUsb_EvtDeviceD0ExitPreInterruptsDisabled;
EVT_WDF_DEVICE_QUERY_REMOVE XenUsb_EvtDeviceQueryRemove;
*/

EVT_WDF_DRIVER_DEVICE_ADD XenUsb_EvtDriverDeviceAdd;

EVT_WDF_CHILD_LIST_CREATE_DEVICE XenUsb_EvtChildListCreateDevice;
EVT_WDF_CHILD_LIST_SCAN_FOR_CHILDREN XenUsb_EvtChildListScanForChildren;

VOID
XenUsb_EnumeratePorts(WDFDEVICE device);

EVT_WDF_IO_QUEUE_IO_INTERNAL_DEVICE_CONTROL XenUsb_EvtIoInternalDeviceControl_DEVICE_SUBMIT_URB;
EVT_WDF_IO_QUEUE_IO_INTERNAL_DEVICE_CONTROL XenUsb_EvtIoInternalDeviceControl_ROOTHUB_SUBMIT_URB;

NTSTATUS
XenUsb_ExecuteRequest(
  PXENUSB_DEVICE_DATA xudd,
  usbif_shadow_t *shadow,
  PVOID transfer_buffer,
  PMDL transfer_buffer_mdl,
  ULONG transfer_buffer_length);

#define URB_DECODE_UNKNOWN     0 /* URB is unknown */
#define URB_DECODE_COMPLETE    1 /* URB is decoded and no further work should be required */
#define URB_DECODE_INCOMPLETE  2 /* URB is decoded but further work is required */
#define URB_DECODE_NOT_CONTROL 3 /* URB is known but not a control packet */

typedef struct {
  PULONG length;
  PVOID buffer;
  union {
    USB_DEFAULT_PIPE_SETUP_PACKET default_pipe_setup_packet;
    UCHAR raw[8];
  } setup_packet;
} urb_decode_t;

ULONG
XenUsb_DecodeControlUrb(PURB urb, urb_decode_t *decode_data);

VOID
XenUsbHub_ProcessHubInterruptEvent(xenusb_endpoint_t *endpoint);
  
#endif
