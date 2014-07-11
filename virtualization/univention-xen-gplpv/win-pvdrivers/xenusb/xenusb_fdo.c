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

// STATUS_UNSUCCESSFUL -> STATUS_BAD_INITIAL_PC 

#include "xenusb.h"

/* Not really necessary but keeps PREfast happy */
static EVT_WDF_DEVICE_D0_ENTRY XenUsb_EvtDeviceD0Entry;
static EVT_WDF_DEVICE_D0_EXIT XenUsb_EvtDeviceD0Exit;
static EVT_WDFDEVICE_WDM_IRP_PREPROCESS XenUsb_EvtDeviceWdmIrpPreprocessQUERY_INTERFACE;
static EVT_WDF_IO_QUEUE_IO_DEVICE_CONTROL XenUsb_EvtIoDeviceControl;
static EVT_WDF_IO_QUEUE_IO_INTERNAL_DEVICE_CONTROL XenUsb_EvtIoInternalDeviceControl;
static EVT_WDF_IO_QUEUE_IO_INTERNAL_DEVICE_CONTROL XenUsb_EvtIoInternalDeviceControl_PVURB;
static EVT_WDF_IO_QUEUE_IO_DEFAULT XenUsb_EvtIoDefault;
static EVT_WDF_REQUEST_CANCEL XenUsb_EvtRequestCancelPvUrb;
static NTSTATUS XenUsb_Connect(PVOID context, BOOLEAN suspend);
static NTSTATUS XenUsb_Disconnect(PVOID context, BOOLEAN suspend);
#if (VER_PRODUCTBUILD >= 7600)
static KDEFERRED_ROUTINE XenUsb_HandleEventDpc;
#endif

static NTSTATUS
XenUsb_EvtDeviceWdmIrpPreprocessQUERY_INTERFACE(WDFDEVICE device, PIRP irp)
{
  PIO_STACK_LOCATION stack;
 
  FUNCTION_ENTER();
 
  stack = IoGetCurrentIrpStackLocation(irp);

  if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &USB_BUS_INTERFACE_HUB_GUID, sizeof(GUID)) == 0)
    FUNCTION_MSG("USB_BUS_INTERFACE_HUB_GUID\n");
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &USB_BUS_INTERFACE_USBDI_GUID, sizeof(GUID)) == 0)
    FUNCTION_MSG("USB_BUS_INTERFACE_USBDI_GUID\n");
  else if (memcmp(stack->Parameters.QueryInterface.InterfaceType, &GUID_TRANSLATOR_INTERFACE_STANDARD, sizeof(GUID)) == 0)
    FUNCTION_MSG("GUID_TRANSLATOR_INTERFACE_STANDARD\n");
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

/* called with urb ring lock held */
static VOID
PutRequestsOnRing(PXENUSB_DEVICE_DATA xudd) {
  partial_pvurb_t *partial_pvurb;
  uint16_t id;
  int notify;

  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());

  while ((partial_pvurb = (partial_pvurb_t *)RemoveHeadList((PLIST_ENTRY)&xudd->partial_pvurb_queue)) != (partial_pvurb_t *)&xudd->partial_pvurb_queue) {
    FUNCTION_MSG("partial_pvurb = %p\n", partial_pvurb);
    /* if this partial_pvurb is cancelling another we don't need to check if the cancelled partial_pvurb is on the ring - that is taken care of in HandleEvent */
    id = get_id_from_freelist(xudd->req_id_ss);
    if (id == (uint16_t)-1) {
      FUNCTION_MSG("no free ring slots\n");
      InsertHeadList(&xudd->partial_pvurb_queue, &partial_pvurb->entry);
      break;
    }
    InsertTailList(&xudd->partial_pvurb_ring, &partial_pvurb->entry);
    xudd->partial_pvurbs[id] = partial_pvurb;
    partial_pvurb->req.id = id;    
    *RING_GET_REQUEST(&xudd->urb_ring, xudd->urb_ring.req_prod_pvt) = partial_pvurb->req;
    xudd->urb_ring.req_prod_pvt++;
  }
  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xudd->urb_ring, notify);
  if (notify) {
    FUNCTION_MSG("Notifying\n");
    XnNotify(xudd->handle, xudd->event_channel);
  }
  
  FUNCTION_EXIT();
}

static VOID
XenUsb_HandleEventDpc(PKDPC dpc, PVOID context, PVOID arg1, PVOID arg2) {
  NTSTATUS status;
  PXENUSB_DEVICE_DATA xudd = context;
  RING_IDX prod, cons;
  usbif_urb_response_t *urb_rsp;
  usbif_conn_response_t *conn_rsp;
  usbif_conn_request_t *conn_req;
  int more_to_do;
  pvurb_t *pvurb, *complete_head = NULL, *complete_tail = NULL;
  partial_pvurb_t *partial_pvurb;
  BOOLEAN port_changed = FALSE;

  UNREFERENCED_PARAMETER(dpc);
  UNREFERENCED_PARAMETER(arg1);
  UNREFERENCED_PARAMETER(arg2);

  FUNCTION_ENTER();

  more_to_do = TRUE;
  KeAcquireSpinLockAtDpcLevel(&xudd->urb_ring_lock);
  while (more_to_do)
  {
    prod = xudd->urb_ring.sring->rsp_prod;
    KeMemoryBarrier();
    for (cons = xudd->urb_ring.rsp_cons; cons != prod; cons++)
    {
      urb_rsp = RING_GET_RESPONSE(&xudd->urb_ring, cons);
//      FUNCTION_MSG("urb_rsp->id = %d\n", urb_rsp->id);
      partial_pvurb = xudd->partial_pvurbs[urb_rsp->id];
      RemoveEntryList(&partial_pvurb->entry);
      partial_pvurb->rsp = *urb_rsp;
//      FUNCTION_MSG("shadow = %p\n", shadow);
//      FUNCTION_MSG("shadow->rsp = %p\n", shadow->rsp);
      if (usbif_pipeunlink(partial_pvurb->req.pipe)) {
        FUNCTION_MSG("is a cancel request for request %p\n", partial_pvurb->pvurb->request);
        FUNCTION_MSG("urb_ring rsp status = %d\n", urb_rsp->status);
        // status should be 115 == EINPROGRESS
      } else {
        partial_pvurb->pvurb->total_length += urb_rsp->actual_length;
        if (!partial_pvurb->pvurb->rsp.status)
          partial_pvurb->pvurb->rsp.status = urb_rsp->status;
        partial_pvurb->pvurb->rsp.error_count += urb_rsp->error_count;;
        if (partial_pvurb->mdl) {
          int i;
          for (i = 0; i < partial_pvurb->req.nr_buffer_segs; i++) {
            XnEndAccess(xudd->handle, partial_pvurb->req.seg[i].gref, FALSE, (ULONG)'XUSB');
          }
        }

        FUNCTION_MSG("urb_ring rsp id = %d\n", partial_pvurb->rsp.id);
        FUNCTION_MSG("urb_ring rsp start_frame = %d\n", partial_pvurb->rsp.start_frame);
        FUNCTION_MSG("urb_ring rsp status = %d\n", partial_pvurb->rsp.status);
        FUNCTION_MSG("urb_ring rsp actual_length = %d\n", partial_pvurb->rsp.actual_length);
        FUNCTION_MSG("urb_ring rsp error_count = %d\n", partial_pvurb->rsp.error_count);
      }
      if (partial_pvurb->other_partial_pvurb) {
        if (!partial_pvurb->other_partial_pvurb->on_ring) {
          /* cancel hasn't been put on the ring yet - remove it */
          RemoveEntryList(&partial_pvurb->other_partial_pvurb->entry);
          ASSERT(usbif_pipeunlink(partial_pvurb->other_partial_pvurb->req.pipe));
          partial_pvurb->pvurb->ref--;
          ExFreePoolWithTag(partial_pvurb->other_partial_pvurb, XENUSB_POOL_TAG);
        }
      }
      partial_pvurb->pvurb->ref--;
      switch (partial_pvurb->rsp.status) {
      case EINPROGRESS: /* unlink request */
      case ECONNRESET:  /* cancelled request */
        ASSERT(partial_pvurb->pvurb->status == STATUS_CANCELLED);
        break;
      default:
        break;
      }
      put_id_on_freelist(xudd->req_id_ss, partial_pvurb->rsp.id);
      partial_pvurb->pvurb->next = NULL;
      if (!partial_pvurb->pvurb->ref) {
        if (complete_tail) {
          complete_tail->next = partial_pvurb->pvurb;
        } else {
          complete_head = partial_pvurb->pvurb;
        }
        complete_tail = partial_pvurb->pvurb;
      }
    }

    xudd->urb_ring.rsp_cons = cons;
    if (cons != xudd->urb_ring.req_prod_pvt) {
      RING_FINAL_CHECK_FOR_RESPONSES(&xudd->urb_ring, more_to_do);
    } else {
      xudd->urb_ring.sring->rsp_event = cons + 1;
      more_to_do = FALSE;
    }
  }
  PutRequestsOnRing(xudd);
  KeReleaseSpinLockFromDpcLevel(&xudd->urb_ring_lock);

  pvurb = complete_head;
  while (pvurb != NULL) {
    complete_head = pvurb->next;
    status = WdfRequestUnmarkCancelable(pvurb->request);
    if (status == STATUS_CANCELLED) {
      FUNCTION_MSG("Cancel was called\n");
    }
    
    WdfRequestCompleteWithInformation(pvurb->request, pvurb->status, pvurb->total_length); /* the WDFREQUEST is always successfull here even if the pvurb->rsp has an error */
    pvurb = complete_head;
  }

  more_to_do = TRUE;
  KeAcquireSpinLockAtDpcLevel(&xudd->conn_ring_lock);
  while (more_to_do)
  {
    prod = xudd->conn_ring.sring->rsp_prod;
    KeMemoryBarrier();
    for (cons = xudd->conn_ring.rsp_cons; cons != prod; cons++)
    {
      USHORT old_port_status;
      conn_rsp = RING_GET_RESPONSE(&xudd->conn_ring, cons);
      FUNCTION_MSG("conn_rsp->portnum = %d\n", conn_rsp->portnum);
      FUNCTION_MSG("conn_rsp->speed = %d\n", conn_rsp->speed);
      
      old_port_status = xudd->ports[conn_rsp->portnum - 1].port_status;
      xudd->ports[conn_rsp->portnum - 1].port_type = conn_rsp->speed;
      xudd->ports[conn_rsp->portnum - 1].port_status &= ~((1 << PORT_LOW_SPEED) | (1 << PORT_HIGH_SPEED) | (1 << PORT_CONNECTION));
      switch (conn_rsp->speed)
      {
      case USB_PORT_TYPE_NOT_CONNECTED:
        xudd->ports[conn_rsp->portnum - 1].port_status &= ~(1 << PORT_ENABLE);
        break;
      case USB_PORT_TYPE_LOW_SPEED:
        xudd->ports[conn_rsp->portnum - 1].port_status |= (1 << PORT_LOW_SPEED) | (1 << PORT_CONNECTION);
        break;
      case USB_PORT_TYPE_FULL_SPEED:
        xudd->ports[conn_rsp->portnum - 1].port_status |= (1 << PORT_CONNECTION);
        break;
      case USB_PORT_TYPE_HIGH_SPEED:
        xudd->ports[conn_rsp->portnum - 1].port_status |= (1 << PORT_HIGH_SPEED) | (1 << PORT_CONNECTION);
        break;
      }      
      xudd->ports[conn_rsp->portnum - 1].port_change |= (xudd->ports[conn_rsp->portnum - 1].port_status ^ old_port_status) & ((1 << PORT_ENABLE) | (1 << PORT_CONNECTION));
      if (xudd->ports[conn_rsp->portnum - 1].port_change)
        port_changed = TRUE;
      conn_req = RING_GET_REQUEST(&xudd->conn_ring, xudd->conn_ring.req_prod_pvt);
      conn_req->id = conn_rsp->id;
      xudd->conn_ring.req_prod_pvt++;
    }

    xudd->conn_ring.rsp_cons = cons;
    if (cons != xudd->conn_ring.req_prod_pvt)
    {
      RING_FINAL_CHECK_FOR_RESPONSES(&xudd->conn_ring, more_to_do);
    }
    else
    {
      xudd->conn_ring.sring->rsp_event = cons + 1;
      more_to_do = FALSE;
    }
  }
  KeReleaseSpinLockFromDpcLevel(&xudd->conn_ring_lock);

  if (port_changed) {
    PXENUSB_PDO_DEVICE_DATA xupdd = GetXupdd(xudd->root_hub_device);
    XenUsbHub_ProcessHubInterruptEvent(xupdd->usb_device->configs[0]->interfaces[0]->endpoints[0]);
  }
      
  FUNCTION_EXIT();

  return;
}

static BOOLEAN
XenUsb_HandleEvent_DIRQL(PVOID context) {
  PXENUSB_DEVICE_DATA xudd = context;
  
  //FUNCTION_ENTER();
  if (xudd->device_state == DEVICE_STATE_ACTIVE || xudd->device_state == DEVICE_STATE_DISCONNECTING) {
    KeInsertQueueDpc(&xudd->event_dpc, NULL, NULL);
  }
  //FUNCTION_EXIT();
  return TRUE;
}

#if 0
static NTSTATUS
XenUsb_StartXenbusInit(PXENUSB_DEVICE_DATA xudd)
{
  PUCHAR ptr;
  USHORT type;
  PCHAR setting, value, value2;

  xudd->urb_sring = NULL;
  xudd->event_channel = 0;

  ptr = xudd->config_page;
  while((type = GET_XEN_INIT_RSP(&ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END) {
    switch(type) {
    case XEN_INIT_TYPE_READ_STRING_BACK:
      FUNCTION_MSG("XEN_INIT_TYPE_READ_STRING_BACK - %s = %s\n", setting, value);
      break;
    case XEN_INIT_TYPE_READ_STRING_FRONT:
      FUNCTION_MSG("XEN_INIT_TYPE_READ_STRING_FRONT - %s = %s\n", setting, value);
      break;
    case XEN_INIT_TYPE_VECTORS:
      FUNCTION_MSG("XEN_INIT_TYPE_VECTORS\n");
      if (((PXENPCI_VECTORS)value)->length != sizeof(XENPCI_VECTORS) ||
        ((PXENPCI_VECTORS)value)->magic != XEN_DATA_MAGIC) {
        FUNCTION_MSG("vectors mismatch (magic = %08x, length = %d)\n",
          ((PXENPCI_VECTORS)value)->magic, ((PXENPCI_VECTORS)value)->length);
        FUNCTION_EXIT();
        return STATUS_BAD_INITIAL_PC;
      }
      else
        memcpy(&xudd->vectors, value, sizeof(XENPCI_VECTORS));
      break;
    case XEN_INIT_TYPE_STATE_PTR:
      FUNCTION_MSG("XEN_INIT_TYPE_DEVICE_STATE - %p\n", PtrToUlong(value));
      xudd->device_state = (PXENPCI_DEVICE_STATE)value;
      break;
    default:
      FUNCTION_MSG("XEN_INIT_TYPE_%d\n", type);
      break;
    }
  }
  return STATUS_SUCCESS;
}
#endif

#if 0
static NTSTATUS
XenUsb_CompleteXenbusInit(PXENUSB_DEVICE_DATA xudd) {
  PUCHAR ptr;
  USHORT type;
  PCHAR setting, value, value2;
  ULONG i;

  ptr = xudd->config_page;
  while((type = GET_XEN_INIT_RSP(&ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END) {
    switch(type) {
    case XEN_INIT_TYPE_RING: /* frontend ring */
      FUNCTION_MSG("XEN_INIT_TYPE_RING - %s = %p\n", setting, value);
      if (strcmp(setting, "urb-ring-ref") == 0) {
        xudd->urb_sring = (usbif_urb_sring_t *)value;
        FRONT_RING_INIT(&xudd->urb_ring, xudd->urb_sring, PAGE_SIZE);
      }
      if (strcmp(setting, "conn-ring-ref") == 0) {
        xudd->conn_sring = (usbif_conn_sring_t *)value;
        FRONT_RING_INIT(&xudd->conn_ring, xudd->conn_sring, PAGE_SIZE);
      }
      break;
    case XEN_INIT_TYPE_EVENT_CHANNEL_DPC: /* frontend event channel */
      FUNCTION_MSG("XEN_INIT_TYPE_EVENT_CHANNEL_DPC - %s = %d\n", setting, PtrToUlong(value) & 0x3FFFFFFF);
      if (strcmp(setting, "event-channel") == 0) {
        xudd->event_channel = PtrToUlong(value);
      }
      break;
    case XEN_INIT_TYPE_READ_STRING_BACK:
    case XEN_INIT_TYPE_READ_STRING_FRONT:
      FUNCTION_MSG("XEN_INIT_TYPE_READ_STRING - %s = %s\n", setting, value);
      break;
    default:
      FUNCTION_MSG("XEN_INIT_TYPE_%d\n", type);
      break;
    }
  }
  if (xudd->urb_sring == NULL || xudd->conn_sring == NULL || xudd->event_channel == 0) {
    FUNCTION_MSG("Missing settings\n");
    FUNCTION_EXIT();
    return STATUS_BAD_INITIAL_PC;
  }
  
  stack_new(&xudd->req_id_ss, REQ_ID_COUNT);
  for (i = 0; i < REQ_ID_COUNT; i++)  {
    put_id_on_freelist(xudd->req_id_ss, (uint16_t)i);
  }
  
  return STATUS_SUCCESS;
}
#endif

VOID
XenUsb_DeviceCallback(PVOID context, ULONG callback_type, PVOID value) {
  PXENUSB_DEVICE_DATA xudd = (PXENUSB_DEVICE_DATA)context;
  ULONG state;
  
  FUNCTION_ENTER();
  switch (callback_type) {
  case XN_DEVICE_CALLBACK_BACKEND_STATE:
    state = (ULONG)(ULONG_PTR)value;
    if (state == xudd->backend_state) {
      FUNCTION_MSG("same state %d\n", state);
      FUNCTION_EXIT();
    }
    FUNCTION_MSG("XenBusState = %d -> %d\n", xudd->backend_state, state);
    xudd->backend_state = state;
    KeSetEvent(&xudd->backend_event, 0, FALSE);
    break;
  case XN_DEVICE_CALLBACK_SUSPEND:
    FUNCTION_MSG("XN_DEVICE_CALLBACK_SUSPEND");
    XenUsb_Disconnect(xudd, TRUE);
    break;
  case XN_DEVICE_CALLBACK_RESUME:
    FUNCTION_MSG("XN_DEVICE_CALLBACK_RESUME");
    xudd->device_state = DEVICE_STATE_INITIALISING;
    XenUsb_Connect(xudd, TRUE);
    // some sort of notify to kick things off?
    break;
  }
  FUNCTION_EXIT();
}

NTSTATUS
XenUsb_Connect(PVOID context, BOOLEAN suspend) {
  NTSTATUS status;
  PXENUSB_DEVICE_DATA xudd = context;
  PFN_NUMBER pfn;
  ULONG i;

  if (!suspend) {
    xudd->handle = XnOpenDevice(xudd->pdo, XenUsb_DeviceCallback, xudd);
  }
  if (!xudd->handle) {
    FUNCTION_MSG("Cannot open Xen device\n");
    return STATUS_UNSUCCESSFUL;
  }

  if (xudd->device_state != DEVICE_STATE_INACTIVE) {
    for (i = 0; i <= 5 && xudd->backend_state != XenbusStateInitialising && xudd->backend_state != XenbusStateInitWait && xudd->backend_state != XenbusStateInitialised; i++) {
      FUNCTION_MSG("Waiting for XenbusStateInitXxx\n");
      if (xudd->backend_state == XenbusStateClosed) {
        status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "state", XenbusStateInitialising);
      }
      KeWaitForSingleObject(&xudd->backend_event, Executive, KernelMode, FALSE, NULL);
    }
    if (xudd->backend_state != XenbusStateInitialising && xudd->backend_state != XenbusStateInitWait && xudd->backend_state != XenbusStateInitialised) {
      FUNCTION_MSG("Backend state timeout\n");
      return STATUS_UNSUCCESSFUL;
    }
    if (!NT_SUCCESS(status = XnBindEvent(xudd->handle, &xudd->event_channel, XenUsb_HandleEvent_DIRQL, xudd))) {
      FUNCTION_MSG("Cannot allocate event channel\n");
      return STATUS_UNSUCCESSFUL;
    }
    FUNCTION_MSG("event_channel = %d\n", xudd->event_channel);
    status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "event-channel", xudd->event_channel);
    xudd->urb_sring = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENUSB_POOL_TAG);
    if (!xudd->urb_sring) {
      FUNCTION_MSG("Cannot allocate urb_sring\n");
      return STATUS_UNSUCCESSFUL;
    }
    SHARED_RING_INIT(xudd->urb_sring);
    FRONT_RING_INIT(&xudd->urb_ring, xudd->urb_sring, PAGE_SIZE);
    pfn = (PFN_NUMBER)(MmGetPhysicalAddress(xudd->urb_sring).QuadPart >> PAGE_SHIFT);
    FUNCTION_MSG("usb sring pfn = %d\n", (ULONG)pfn);
    xudd->urb_sring_gref = XnGrantAccess(xudd->handle, (ULONG)pfn, FALSE, INVALID_GRANT_REF, XENUSB_POOL_TAG);
    FUNCTION_MSG("usb sring_gref = %d\n", xudd->urb_sring_gref);
    status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "urb-ring-ref", xudd->urb_sring_gref);  
    xudd->conn_sring = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENUSB_POOL_TAG);
    if (!xudd->conn_sring) {
      FUNCTION_MSG("Cannot allocate conn_sring\n");
      return STATUS_UNSUCCESSFUL;
    }
    SHARED_RING_INIT(xudd->conn_sring);
    FRONT_RING_INIT(&xudd->conn_ring, xudd->conn_sring, PAGE_SIZE);
    pfn = (PFN_NUMBER)(MmGetPhysicalAddress(xudd->conn_sring).QuadPart >> PAGE_SHIFT);
    FUNCTION_MSG("conn sring pfn = %d\n", (ULONG)pfn);
    xudd->conn_sring_gref = XnGrantAccess(xudd->handle, (ULONG)pfn, FALSE, INVALID_GRANT_REF, XENUSB_POOL_TAG);
    FUNCTION_MSG("conn sring_gref = %d\n", xudd->conn_sring_gref);
    status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "conn-ring-ref", xudd->conn_sring_gref);  

    /* fill conn ring with requests */
    for (i = 0; i < USB_CONN_RING_SIZE; i++) {
      usbif_conn_request_t *req = RING_GET_REQUEST(&xudd->conn_ring, i);
      req->id = (uint16_t)i;
    }
    xudd->conn_ring.req_prod_pvt = i;

    status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "state", XenbusStateConnected);
    for (i = 0; i <= 5 && xudd->backend_state != XenbusStateConnected; i++) {
      FUNCTION_MSG("Waiting for XenbusStateConnected\n");
      KeWaitForSingleObject(&xudd->backend_event, Executive, KernelMode, FALSE, NULL);
    }
    if (xudd->backend_state != XenbusStateConnected) {
      FUNCTION_MSG("Backend state timeout\n");
      return STATUS_UNSUCCESSFUL;
    }
    xudd->device_state = DEVICE_STATE_ACTIVE;
  }

  return STATUS_SUCCESS;
}

NTSTATUS
XenUsb_Disconnect(PVOID context, BOOLEAN suspend) {
  PXENUSB_DEVICE_DATA xudd = (PXENUSB_DEVICE_DATA)context;
  //PFN_NUMBER pfn;
  NTSTATUS status;

  if (xudd->device_state != DEVICE_STATE_ACTIVE && xudd->device_state != DEVICE_STATE_INACTIVE) {
    FUNCTION_MSG("state not DEVICE_STATE_(IN)ACTIVE, is %d instead\n", xudd->device_state);
    FUNCTION_EXIT();
    return STATUS_SUCCESS;
  }
  if (xudd->device_state != DEVICE_STATE_INACTIVE) {
    xudd->device_state = DEVICE_STATE_DISCONNECTING;
    status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "state", XenbusStateClosing);
    while (xudd->backend_state != XenbusStateClosing && xudd->backend_state != XenbusStateClosed) {
      FUNCTION_MSG("Waiting for XenbusStateClosing/Closed\n");
      KeWaitForSingleObject(&xudd->backend_event, Executive, KernelMode, FALSE, NULL);
    }
    status = XnWriteInt32(xudd->handle, XN_BASE_FRONTEND, "state", XenbusStateClosed);
    while (xudd->backend_state != XenbusStateClosed) {
      FUNCTION_MSG("Waiting for XenbusStateClosed\n");
      KeWaitForSingleObject(&xudd->backend_event, Executive, KernelMode, FALSE, NULL);
    }
    XnUnbindEvent(xudd->handle, xudd->event_channel);
    
  #if NTDDI_VERSION < WINXP
    KeFlushQueuedDpcs();
  #endif
    XnEndAccess(xudd->handle, xudd->conn_sring_gref, FALSE, XENUSB_POOL_TAG);
    ExFreePoolWithTag(xudd->conn_sring, XENUSB_POOL_TAG);
    XnEndAccess(xudd->handle, xudd->urb_sring_gref, FALSE, XENUSB_POOL_TAG);
    ExFreePoolWithTag(xudd->urb_sring, XENUSB_POOL_TAG);
  }
  if (!suspend) {
    XnCloseDevice(xudd->handle);
  }
  xudd->device_state = DEVICE_STATE_DISCONNECTED;
  return STATUS_SUCCESS;
}

NTSTATUS
XenUsb_EvtDeviceD0Entry(WDFDEVICE device, WDF_POWER_DEVICE_STATE previous_state) {
  NTSTATUS status = STATUS_SUCCESS;
  PXENUSB_DEVICE_DATA xudd = GetXudd(device);

  UNREFERENCED_PARAMETER(device);

  FUNCTION_ENTER();

  switch (previous_state) {
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
  
  XenUsb_Connect(xudd, FALSE);

  FUNCTION_EXIT();

  return status;
}

NTSTATUS
XenUsb_EvtDeviceD0Exit(WDFDEVICE device, WDF_POWER_DEVICE_STATE target_state) {
  NTSTATUS status = STATUS_SUCCESS;
  PXENUSB_DEVICE_DATA xudd = GetXudd(device);
  
  FUNCTION_ENTER();

  UNREFERENCED_PARAMETER(device);

  switch (target_state) {
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

  XenUsb_Disconnect(xudd, FALSE);
  
  FUNCTION_EXIT();
  
  return status;
}

VOID
XenUsb_EvtChildListScanForChildren(WDFCHILDLIST child_list) {
  NTSTATUS status;
  PXENUSB_DEVICE_DATA xudd = GetXudd(WdfChildListGetDevice(child_list));
  XENUSB_PDO_IDENTIFICATION_DESCRIPTION child_description;
  CHAR path[128];
  PCHAR value;
  ULONG i;

  FUNCTION_ENTER();

  WdfChildListBeginScan(child_list);

  // hold the queue on each device and set each device to a pending state
  // read backend/num_ports
  //RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/num-ports", xudd->vectors.backend_path);
  status = XnReadString(xudd->handle, XBT_NIL, path, &value);
  if (status != STATUS_SUCCESS) {
    WdfChildListEndScan(child_list);
    FUNCTION_MSG("Failed to read num-ports\n");
    return;
  }
  xudd->num_ports = (ULONG)parse_numeric_string(value);  
  XnFreeMem(xudd->handle, value);
  FUNCTION_MSG("num-ports = %d\n", xudd->num_ports);

  for (i = 0; i < 8; i++) {
    xudd->ports[i].port_number = i + 1;
    xudd->ports[i].port_type = USB_PORT_TYPE_NOT_CONNECTED;
    xudd->ports[i].port_status = 0; //1 << PORT_ENABLE;
    xudd->ports[i].port_change = 0x0000;
  }  

  /* only a single root hub is enumerated */
  WDF_CHILD_IDENTIFICATION_DESCRIPTION_HEADER_INIT(&child_description.header, sizeof(child_description));

  child_description.device_number = 0; //TODO: get the proper index from parent

  status = WdfChildListAddOrUpdateChildDescriptionAsPresent(child_list, &child_description.header, NULL);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfChildListAddOrUpdateChildDescriptionAsPresent failed with status 0x%08x\n", status);
  }

  WdfChildListEndScan(child_list);
  
  FUNCTION_EXIT();
}

static VOID
XenUsb_EvtIoDeviceControl(
  WDFQUEUE queue,
  WDFREQUEST request,
  size_t output_buffer_length,
  size_t input_buffer_length,
  ULONG io_control_code)
{
  NTSTATUS status;
  WDFDEVICE device = WdfIoQueueGetDevice(queue);
  PXENUSB_DEVICE_DATA xudd = GetXudd(device);

  UNREFERENCED_PARAMETER(queue);
  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);

  FUNCTION_ENTER();

  status = STATUS_BAD_INITIAL_PC;

  // these are in api\usbioctl.h
  switch(io_control_code)
  {
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
  case IOCTL_USB_GET_ROOT_HUB_NAME:
  {
    PUSB_HCD_DRIVERKEY_NAME uhdn;
    size_t length;
    ULONG required_length = sizeof(USB_HCD_DRIVERKEY_NAME);
    
    FUNCTION_MSG("IOCTL_USB_GET_ROOT_HUB_NAME\n");
    FUNCTION_MSG(" output_buffer_length = %d\n", output_buffer_length);
      
    if (output_buffer_length < sizeof(USB_HCD_DRIVERKEY_NAME)) {
      status = STATUS_BUFFER_TOO_SMALL;
    } else {
      status = WdfRequestRetrieveOutputBuffer(request, output_buffer_length, (PVOID *)&uhdn, &length);
      if (NT_SUCCESS(status)) {
        WDFSTRING symbolic_link_wdfstring;
        UNICODE_STRING symbolic_link;
        
        uhdn->DriverKeyName[0] = 0;
        status = WdfStringCreate(NULL, WDF_NO_OBJECT_ATTRIBUTES, &symbolic_link_wdfstring);
        if (NT_SUCCESS(status)) {
          status = WdfDeviceRetrieveDeviceInterfaceString(xudd->root_hub_device, &GUID_DEVINTERFACE_USB_HUB, NULL, symbolic_link_wdfstring);
          if (NT_SUCCESS(status)) {
            WdfStringGetUnicodeString(symbolic_link_wdfstring, &symbolic_link);
            /* remove leading \??\ from name */
            symbolic_link.Buffer += 4;
            symbolic_link.Length -= 4 * sizeof(WCHAR);
            required_length = FIELD_OFFSET(USB_HCD_DRIVERKEY_NAME, DriverKeyName) + symbolic_link.Length + sizeof(WCHAR);
            FUNCTION_MSG("output_buffer_length = %d\n", output_buffer_length);
            FUNCTION_MSG("required_length = %d\n", required_length);
            if (output_buffer_length >= required_length) {
              uhdn->ActualLength = required_length;
              memcpy(uhdn->DriverKeyName, symbolic_link.Buffer, symbolic_link.Length);
              uhdn->DriverKeyName[symbolic_link.Length / 2] = 0;
              WdfRequestSetInformation(request, required_length);
            } else {
              uhdn->ActualLength = required_length;
              uhdn->DriverKeyName[0] = 0;
              status = STATUS_SUCCESS;
              WdfRequestSetInformation(request, output_buffer_length);
            }
          } else {
            FUNCTION_MSG("WdfStringCreate = %08x\n", status);
          }
        } else {
          FUNCTION_MSG("WdfDeviceRetrieveDeviceInterfaceString = %08x\n", status);
          status = STATUS_INVALID_PARAMETER;
        }
      } else {
        FUNCTION_MSG("WdfRequestRetrieveOutputBuffer = %08x\n", status);
      }
      FUNCTION_MSG(" uhdn->ActualLength = %d\n", uhdn->ActualLength);
      FUNCTION_MSG(" uhdn->DriverKeyName = %S\n", uhdn->DriverKeyName);
    }
    break;
  }
  case IOCTL_GET_HCD_DRIVERKEY_NAME:
  {
    PUSB_HCD_DRIVERKEY_NAME uhdn;
    size_t length;
    ULONG required_length = sizeof(USB_HCD_DRIVERKEY_NAME);
    ULONG key_length;
    
    FUNCTION_MSG("IOCTL_GET_HCD_DRIVERKEY_NAME\n");
    FUNCTION_MSG(" output_buffer_length = %d\n", output_buffer_length);
      
    if (output_buffer_length < sizeof(USB_HCD_DRIVERKEY_NAME)) {
      FUNCTION_MSG("Buffer too small (%d < %d)\n", output_buffer_length, sizeof(USB_HCD_DRIVERKEY_NAME));
      status = STATUS_BUFFER_TOO_SMALL;
      break;
    }
    status = WdfRequestRetrieveOutputBuffer(request, output_buffer_length, (PVOID *)&uhdn, &length);
    if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("WdfRequestRetrieveOutputBuffer = %08x\n", status);
      break;
    }
    status = WdfDeviceQueryProperty(device, DevicePropertyDriverKeyName, 0, NULL, &key_length);
    if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("WdfDeviceQueryProperty = %08x\n", status);
      break;
    }    
    FUNCTION_MSG(" key_length = %d\n", key_length);
    required_length = FIELD_OFFSET(USB_HCD_DRIVERKEY_NAME, DriverKeyName) + key_length + 2;
    uhdn->ActualLength = required_length;
    FUNCTION_MSG("output_buffer_length = %d\n", output_buffer_length);
    FUNCTION_MSG("required_length = %d\n", required_length);
    if (output_buffer_length >= required_length)
    {
      status = WdfDeviceQueryProperty(device, DevicePropertyDriverKeyName, 
        required_length - FIELD_OFFSET(USB_HCD_DRIVERKEY_NAME, DriverKeyName), uhdn->DriverKeyName,
        &key_length);
      WdfRequestSetInformation(request, required_length);
    }
    else
    {
      uhdn->DriverKeyName[0] = 0;
      status = STATUS_SUCCESS;
      WdfRequestSetInformation(request, output_buffer_length);
    }
    FUNCTION_MSG(" uhdn->ActualLength = %d\n", uhdn->ActualLength);
    FUNCTION_MSG(" uhdn->DriverKeyName = %S\n", uhdn->DriverKeyName);
    break;
  }
#if 0
  case IOCTL_USB_RESET_HUB:
    FUNCTION_MSG("IOCTL_USB_RESET_HUB\n");
    break;
#endif
  default:
    FUNCTION_MSG("Unknown IOCTL %08x\n", io_control_code);
    break;
  }
  FUNCTION_MSG("Calling WdfRequestComplete with status = %08x\n", status);
  WdfRequestComplete(request, status);

  FUNCTION_EXIT();
}

VOID
XenUsb_EvtRequestCancelPvUrb(WDFREQUEST request) {
  WDFDEVICE device = WdfIoQueueGetDevice(WdfRequestGetIoQueue(request));
  PXENUSB_DEVICE_DATA xudd = GetXudd(device);
  WDF_REQUEST_PARAMETERS wrp;
  partial_pvurb_t *partial_pvurb;
  pvurb_t *pvurb;
  KIRQL old_irql;

  FUNCTION_ENTER();
  FUNCTION_MSG("cancelling request %p\n", request);

  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  KeAcquireSpinLock(&xudd->urb_ring_lock, &old_irql);

  WdfRequestGetParameters(request, &wrp);
  pvurb = (pvurb_t *)wrp.Parameters.Others.Arg1;
  FUNCTION_MSG("pvurb = %p\n", pvurb);
  ASSERT(pvurb);

  partial_pvurb = (partial_pvurb_t *)xudd->partial_pvurb_queue.Flink;
  while (partial_pvurb != (partial_pvurb_t *)&xudd->partial_pvurb_queue) {
    partial_pvurb_t *next_partial_pvurb = (partial_pvurb_t *)partial_pvurb->entry.Flink;
    ASSERT(!partial_pvurb->on_ring);
    FUNCTION_MSG("partial_pvurb = %p is not yet on ring\n", partial_pvurb);
    RemoveEntryList(&partial_pvurb->entry);
    ExFreePoolWithTag(partial_pvurb, XENUSB_POOL_TAG);
    pvurb->ref--;
    partial_pvurb = next_partial_pvurb;
  }
  partial_pvurb = (partial_pvurb_t *)xudd->partial_pvurb_ring.Flink;
  while (partial_pvurb != (partial_pvurb_t *)&xudd->partial_pvurb_ring) {
    partial_pvurb_t *next_partial_pvurb = (partial_pvurb_t *)partial_pvurb->entry.Flink;
    partial_pvurb_t *partial_pvurb_cancel;
    FUNCTION_MSG("partial_pvurb = %p is on ring\n", partial_pvurb);
    ASSERT(partial_pvurb->on_ring);
    partial_pvurb_cancel = ExAllocatePoolWithTag(NonPagedPool, sizeof(*partial_pvurb_cancel), XENUSB_POOL_TAG); /* todo - use lookaside */
    ASSERT(partial_pvurb_cancel); /* what would we do if this failed? */
    partial_pvurb_cancel->req = partial_pvurb->req;
    partial_pvurb_cancel->req.pipe = usbif_setunlink_pipe(partial_pvurb_cancel->req.pipe);
    partial_pvurb_cancel->req.u.unlink.unlink_id = partial_pvurb->req.id;
    partial_pvurb_cancel->pvurb = pvurb;
    partial_pvurb_cancel->mdl = NULL;
    partial_pvurb_cancel->other_partial_pvurb = partial_pvurb;
    partial_pvurb->other_partial_pvurb = partial_pvurb_cancel;
    partial_pvurb_cancel->on_ring = FALSE;
    pvurb->ref++;
    InsertHeadList(&xudd->partial_pvurb_queue, &partial_pvurb_cancel->entry);
    partial_pvurb = next_partial_pvurb;
  }
  if (pvurb->ref) {
    PutRequestsOnRing(xudd);
    KeReleaseSpinLock(&xudd->urb_ring_lock, old_irql);
  } else {
    KeReleaseSpinLock(&xudd->urb_ring_lock, old_irql);
    WdfRequestComplete(request, STATUS_CANCELLED);
  }
  FUNCTION_EXIT();
}

static VOID
XenUsb_EvtIoInternalDeviceControl_PVURB(
  WDFQUEUE queue,
  WDFREQUEST request,
  size_t output_buffer_length,
  size_t input_buffer_length,
  ULONG io_control_code)
{
  NTSTATUS status;
  WDFDEVICE device = WdfIoQueueGetDevice(queue);
  PXENUSB_DEVICE_DATA xudd = GetXudd(device);
  WDF_REQUEST_PARAMETERS wrp;
  pvurb_t *pvurb;
  partial_pvurb_t *partial_pvurb;
  KIRQL old_irql;
  
  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);
  UNREFERENCED_PARAMETER(io_control_code);

  FUNCTION_ENTER();

  ASSERT(io_control_code == IOCTL_INTERNAL_PVUSB_SUBMIT_URB);

  WDF_REQUEST_PARAMETERS_INIT(&wrp);
  WdfRequestGetParameters(request, &wrp);
  pvurb = (pvurb_t *)wrp.Parameters.Others.Arg1;
  ASSERT(pvurb);
  RtlZeroMemory(&pvurb->rsp, sizeof(pvurb->rsp));
  pvurb->status = STATUS_SUCCESS;
  pvurb->request = request;
  pvurb->ref = 1;
  pvurb->total_length = 0;
  partial_pvurb = ExAllocatePoolWithTag(NonPagedPool, sizeof(*partial_pvurb), XENUSB_POOL_TAG); /* todo - use lookaside */
  if (!partial_pvurb) {
    WdfRequestComplete(request, STATUS_INSUFFICIENT_RESOURCES);
    FUNCTION_EXIT();
    return;
  }
  KeAcquireSpinLock(&xudd->urb_ring_lock, &old_irql);
  status = WdfRequestMarkCancelableEx(request, XenUsb_EvtRequestCancelPvUrb);
  if (!NT_SUCCESS(status)) {
    KeReleaseSpinLock(&xudd->urb_ring_lock, old_irql);  
    FUNCTION_MSG("WdfRequestMarkCancelableEx returned %08x\n", status);
    WdfRequestComplete(request, STATUS_INSUFFICIENT_RESOURCES);
    FUNCTION_EXIT();
    return;
  }  
  
  partial_pvurb->req = pvurb->req;
  partial_pvurb->mdl = pvurb->mdl; /* 1:1 right now, but may need to split up large pvurb into smaller partial_pvurb's */
  partial_pvurb->pvurb = pvurb;
  partial_pvurb->other_partial_pvurb = NULL;
  partial_pvurb->on_ring = FALSE;
  if (!partial_pvurb->mdl) {
    partial_pvurb->req.nr_buffer_segs = 0;
    partial_pvurb->req.buffer_length = 0;
  } else {
    ULONG remaining = MmGetMdlByteCount(partial_pvurb->mdl);
    USHORT offset = (USHORT)MmGetMdlByteOffset(partial_pvurb->mdl);
    int i;
    partial_pvurb->req.buffer_length = (USHORT)MmGetMdlByteCount(partial_pvurb->mdl);
    partial_pvurb->req.nr_buffer_segs = (USHORT)ADDRESS_AND_SIZE_TO_SPAN_PAGES(MmGetMdlVirtualAddress(partial_pvurb->mdl), MmGetMdlByteCount(partial_pvurb->mdl));
    for (i = 0; i < partial_pvurb->req.nr_buffer_segs; i++) {
      partial_pvurb->req.seg[i].gref = XnGrantAccess(xudd->handle, (ULONG)MmGetMdlPfnArray(partial_pvurb->mdl)[i], FALSE, INVALID_GRANT_REF, (ULONG)'XUSB');
      partial_pvurb->req.seg[i].offset = (USHORT)offset;
      partial_pvurb->req.seg[i].length = (USHORT)min((USHORT)remaining, (USHORT)PAGE_SIZE - offset);
      offset = 0;
      remaining -= partial_pvurb->req.seg[i].length;
      FUNCTION_MSG("seg = %d\n", i);
      FUNCTION_MSG(" gref = %d\n", partial_pvurb->req.seg[i].gref);
      FUNCTION_MSG(" offset = %d\n", partial_pvurb->req.seg[i].offset);
      FUNCTION_MSG(" length = %d\n", partial_pvurb->req.seg[i].length);
    }
    FUNCTION_MSG("buffer_length = %d\n", partial_pvurb->req.buffer_length);
    FUNCTION_MSG("nr_buffer_segs = %d\n", partial_pvurb->req.nr_buffer_segs);
  }
  InsertTailList(&xudd->partial_pvurb_queue, &partial_pvurb->entry);
  PutRequestsOnRing(xudd);
  KeReleaseSpinLock(&xudd->urb_ring_lock, old_irql);  
  
  FUNCTION_EXIT();
}

static VOID
XenUsb_EvtIoInternalDeviceControl(
  WDFQUEUE queue,
  WDFREQUEST request,
  size_t output_buffer_length,
  size_t input_buffer_length,
  ULONG io_control_code)
{
  WDFDEVICE device = WdfIoQueueGetDevice(queue);
  PXENUSB_DEVICE_DATA xudd = GetXudd(device);
  //WDF_REQUEST_PARAMETERS wrp;
  //pvusb_urb_t *urb;

  UNREFERENCED_PARAMETER(input_buffer_length);
  UNREFERENCED_PARAMETER(output_buffer_length);

  FUNCTION_ENTER();

  //WDF_REQUEST_PARAMETERS_INIT(&wrp);
  //WdfRequestGetParameters(request, &wrp);

  switch(io_control_code)
  {
  case IOCTL_INTERNAL_PVUSB_SUBMIT_URB:
    FUNCTION_MSG("IOCTL_INTERNAL_PVUSB_SUBMIT_URB\n");
    //urb = (pvusb_urb_t *)wrp.Parameters.Others.Arg1;
    //FUNCTION_MSG("urb = %p\n", urb);
    WdfRequestForwardToIoQueue(request, xudd->pvurb_queue);
    break;
  default:
    FUNCTION_MSG("Unknown IOCTL %08x\n", io_control_code);
    WdfRequestComplete(request, WdfRequestGetStatus(request));
    break;
  }
  FUNCTION_EXIT();
}

static VOID
XenUsb_EvtIoDefault(
  WDFQUEUE queue,
  WDFREQUEST request)
{
  NTSTATUS status;
  WDF_REQUEST_PARAMETERS parameters;

  FUNCTION_ENTER();

  UNREFERENCED_PARAMETER(queue);

  status = STATUS_BAD_INITIAL_PC;

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
  WdfRequestComplete(request, status);  

  FUNCTION_EXIT();
}

NTSTATUS
XenUsb_EvtDriverDeviceAdd(WDFDRIVER driver, PWDFDEVICE_INIT device_init)
{
  NTSTATUS status;
  WDF_CHILD_LIST_CONFIG child_list_config;
  WDFDEVICE device;
  PXENUSB_DEVICE_DATA xudd;
  //UNICODE_STRING reference;
  WDF_OBJECT_ATTRIBUTES device_attributes;
  PNP_BUS_INFORMATION pbi;
  WDF_PNPPOWER_EVENT_CALLBACKS pnp_power_callbacks;
  WDF_DEVICE_POWER_CAPABILITIES power_capabilities;
  WDF_IO_QUEUE_CONFIG queue_config;
  UCHAR pnp_minor_functions[] = { IRP_MN_QUERY_INTERFACE };
  DECLARE_CONST_UNICODE_STRING(symbolicname_name, L"SymbolicName");
  WDFSTRING symbolicname_value_wdfstring;
  WDFKEY device_key;
  UNICODE_STRING symbolicname_value;

  UNREFERENCED_PARAMETER(driver);

  FUNCTION_ENTER();

  WDF_PNPPOWER_EVENT_CALLBACKS_INIT(&pnp_power_callbacks);
  pnp_power_callbacks.EvtDeviceD0Entry = XenUsb_EvtDeviceD0Entry;
  pnp_power_callbacks.EvtDeviceD0Exit = XenUsb_EvtDeviceD0Exit;

  WdfDeviceInitSetPnpPowerEventCallbacks(device_init, &pnp_power_callbacks);

  status = WdfDeviceInitAssignWdmIrpPreprocessCallback(device_init, XenUsb_EvtDeviceWdmIrpPreprocessQUERY_INTERFACE,
    IRP_MJ_PNP, pnp_minor_functions, ARRAY_SIZE(pnp_minor_functions));
  if (!NT_SUCCESS(status))
  {
    return status;
  }

  WdfDeviceInitSetDeviceType(device_init, FILE_DEVICE_BUS_EXTENDER);
  WdfDeviceInitSetExclusive(device_init, FALSE);

  WDF_CHILD_LIST_CONFIG_INIT(&child_list_config, sizeof(XENUSB_PDO_IDENTIFICATION_DESCRIPTION), XenUsb_EvtChildListCreateDevice);
  child_list_config.EvtChildListScanForChildren = XenUsb_EvtChildListScanForChildren;
  WdfFdoInitSetDefaultChildListConfig(device_init, &child_list_config, WDF_NO_OBJECT_ATTRIBUTES);

  WdfDeviceInitSetIoType(device_init, WdfDeviceIoBuffered);

  WdfDeviceInitSetPowerNotPageable(device_init);
  
  WDF_OBJECT_ATTRIBUTES_INIT_CONTEXT_TYPE(&device_attributes, XENUSB_DEVICE_DATA);
  status = WdfDeviceCreate(&device_init, &device_attributes, &device);
  if (!NT_SUCCESS(status))
  {
    FUNCTION_MSG("Error creating device %08x\n", status);
    return status;
  }

  xudd = GetXudd(device);
  xudd->pdo = WdfDeviceWdmGetPhysicalDevice(device);
  xudd->child_list = WdfFdoGetDefaultChildList(device);
  KeInitializeEvent(&xudd->backend_event, SynchronizationEvent, FALSE);
  InitializeListHead(&xudd->partial_pvurb_queue);
  InitializeListHead(&xudd->partial_pvurb_ring);
  KeInitializeDpc(&xudd->event_dpc, XenUsb_HandleEventDpc, xudd);

  KeInitializeSpinLock(&xudd->urb_ring_lock);
  
  WDF_IO_QUEUE_CONFIG_INIT_DEFAULT_QUEUE(&queue_config, WdfIoQueueDispatchParallel);
  queue_config.PowerManaged = FALSE; /* ? */
  queue_config.EvtIoDeviceControl = XenUsb_EvtIoDeviceControl;
  queue_config.EvtIoInternalDeviceControl = XenUsb_EvtIoInternalDeviceControl;
  queue_config.EvtIoDefault = XenUsb_EvtIoDefault;
  status = WdfIoQueueCreate(device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, &xudd->io_queue);
  if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("Error creating io_queue 0x%x\n", status);
      return status;
  }

  WDF_IO_QUEUE_CONFIG_INIT(&queue_config, WdfIoQueueDispatchParallel);
  queue_config.PowerManaged = FALSE; /* ? */
  //queue_config.EvtIoDeviceControl = XenUsb_EvtIoDeviceControl;
  queue_config.EvtIoInternalDeviceControl = XenUsb_EvtIoInternalDeviceControl_PVURB;
  //queue_config.EvtIoDefault = XenUsb_EvtIoDefault;
  queue_config.Settings.Parallel.NumberOfPresentedRequests = USB_URB_RING_SIZE; /* the queue controls if the ring is full */
  status = WdfIoQueueCreate(device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, &xudd->pvurb_queue);
  if (!NT_SUCCESS(status)) {
      FUNCTION_MSG("Error creating urb_queue 0x%x\n", status);
      return status;
  }

  WDF_DEVICE_POWER_CAPABILITIES_INIT(&power_capabilities);
  power_capabilities.DeviceD1 = WdfTrue;
  power_capabilities.WakeFromD1 = WdfTrue;
  power_capabilities.DeviceWake = PowerDeviceD1;
  power_capabilities.DeviceState[PowerSystemWorking]   = PowerDeviceD0;
  power_capabilities.DeviceState[PowerSystemSleeping1] = PowerDeviceD1;
  power_capabilities.DeviceState[PowerSystemSleeping2] = PowerDeviceD2;
  power_capabilities.DeviceState[PowerSystemSleeping3] = PowerDeviceD2;
  power_capabilities.DeviceState[PowerSystemHibernate] = PowerDeviceD3;
  power_capabilities.DeviceState[PowerSystemShutdown]  = PowerDeviceD3;
  WdfDeviceSetPowerCapabilities(device, &power_capabilities);  

  WdfDeviceSetSpecialFileSupport(device, WdfSpecialFilePaging, TRUE);
  WdfDeviceSetSpecialFileSupport(device, WdfSpecialFileHibernation, TRUE);
  WdfDeviceSetSpecialFileSupport(device, WdfSpecialFileDump, TRUE);
  
  pbi.BusTypeGuid = GUID_BUS_TYPE_XEN;
  pbi.LegacyBusType = PNPBus;
  pbi.BusNumber = 0;
  WdfDeviceSetBusInformationForChildren(device, &pbi);

  status = WdfDeviceCreateDeviceInterface(device, &GUID_DEVINTERFACE_USB_HOST_CONTROLLER, NULL);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDeviceCreateDeviceInterface returned %08x\n");
    return status;
  }

  /* USB likes to have a registry key with the symbolic link name in it */
  status = WdfStringCreate(NULL, WDF_NO_OBJECT_ATTRIBUTES, &symbolicname_value_wdfstring);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfStringCreate returned %08x\n");
    return status;
  }
  status = WdfDeviceRetrieveDeviceInterfaceString(device, &GUID_DEVINTERFACE_USB_HOST_CONTROLLER, NULL, symbolicname_value_wdfstring);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDeviceRetrieveDeviceInterfaceString returned %08x\n");
    return status;
  }
  WdfStringGetUnicodeString(symbolicname_value_wdfstring, &symbolicname_value);
  status = WdfDeviceOpenRegistryKey(device, PLUGPLAY_REGKEY_DEVICE, KEY_SET_VALUE, WDF_NO_OBJECT_ATTRIBUTES, &device_key);
  if (!NT_SUCCESS(status)) {
    FUNCTION_MSG("WdfDeviceOpenRegistryKey returned %08x\n");
    return status;
  }
  WdfRegistryAssignUnicodeString(device_key, &symbolicname_name, &symbolicname_value);

  FUNCTION_EXIT();
  return status;
}