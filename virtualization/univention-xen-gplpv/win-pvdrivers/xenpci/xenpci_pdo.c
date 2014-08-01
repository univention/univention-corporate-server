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

#include "xenpci.h"
#include <stdlib.h>
#include <io/ring.h>

#pragma warning(disable : 4200) // zero-sized array
#pragma warning(disable: 4127) // conditional expression is constant

/* Not really necessary but keeps PREfast happy */
static EVT_WDF_INTERRUPT_SYNCHRONIZE XenPci_EvtChn_Sync_Routine;
static EVT_WDF_DEVICE_D0_ENTRY XenPciPdo_EvtDeviceD0Entry;
static EVT_WDF_DEVICE_D0_EXIT XenPciPdo_EvtDeviceD0Exit;
static EVT_WDF_DEVICE_PREPARE_HARDWARE XenPciPdo_EvtDevicePrepareHardware;
static EVT_WDF_DEVICE_RELEASE_HARDWARE XenPciPdo_EvtDeviceReleaseHardware;
static EVT_WDF_DEVICE_USAGE_NOTIFICATION XenPciPdo_EvtDeviceUsageNotification;
static EVT_WDFDEVICE_WDM_IRP_PREPROCESS XenPciPdo_EvtDeviceWdmIrpPreprocess_START_DEVICE;
static EVT_WDF_DEVICE_RESOURCE_REQUIREMENTS_QUERY XenPciPdo_EvtDeviceResourceRequirementsQuery;
static EVT_WDF_DEVICE_PNP_STATE_CHANGE_NOTIFICATION XenPci_EvtDevicePnpStateChange;

/*
Called at PASSIVE_LEVEL(?)
Called during restore
*/
static ULONG
XenPci_ReadBackendState(PXENPCI_PDO_DEVICE_DATA xppdd)
{
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  char path[128];
  char *value;
  char *err;
  ULONG backend_state;
  
  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
  err = XenBus_Read(xpdd, XBT_NIL, path, &value);
  if (err)
  {
    XenPci_FreeMem(err);
    return XenbusStateUnknown;
  }
  else
  {
    backend_state = atoi(value);
    XenPci_FreeMem(value);
    return backend_state;
  }
}

static NTSTATUS
XenPciPdo_ReconfigureCompletionRoutine(
  PDEVICE_OBJECT device_object,
  PIRP irp,
  PVOID context)
{
  UNREFERENCED_PARAMETER(device_object);
  
  if (irp->PendingReturned)
  {
    KeSetEvent ((PKEVENT)context, IO_NO_INCREMENT, FALSE);
  }
  return STATUS_MORE_PROCESSING_REQUIRED;
}

static VOID
XenPci_UpdateBackendState(PVOID context)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  ULONG new_backend_state;

  FUNCTION_ENTER();

  ExAcquireFastMutex(&xppdd->backend_state_mutex);

  new_backend_state = XenPci_ReadBackendState(xppdd);
  if (new_backend_state == XenbusStateUnknown)
  {
    if (xpdd->suspend_state != SUSPEND_STATE_NONE)
    {
      ExReleaseFastMutex(&xppdd->backend_state_mutex);
      return;
    }
    KdPrint(("Failed to read path, assuming closed\n"));
    new_backend_state = XenbusStateClosed;
  }

  if (xppdd->backend_state == new_backend_state)
  {
    KdPrint((__DRIVER_NAME "     state unchanged\n"));
    ExReleaseFastMutex(&xppdd->backend_state_mutex);
    return;
  }
  
  xppdd->backend_state = new_backend_state;

  switch (xppdd->backend_state)
  {
  case XenbusStateUnknown:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Unknown\n"));
    break;

  case XenbusStateInitialising:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Initialising\n"));
    break;

  case XenbusStateInitWait:
    KdPrint((__DRIVER_NAME "     Backend State Changed to InitWait\n"));
    break;

  case XenbusStateInitialised:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Initialised\n"));
    break;

  case XenbusStateConnected:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Connected\n"));  
    break;

  case XenbusStateClosing:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Closing\n"));
    if (xppdd->frontend_state != XenbusStateClosing)
    {
      xppdd->backend_initiated_remove = TRUE;
      KdPrint((__DRIVER_NAME "     Requesting eject\n"));
      WdfPdoRequestEject(device);
    }
    break;

  case XenbusStateClosed:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Closed\n"));
    break;
  
  default:
    KdPrint((__DRIVER_NAME "     Backend State Changed to Undefined = %d\n", xppdd->backend_state));
    break;
  }

  KeSetEvent(&xppdd->backend_state_event, 1, FALSE);

  ExReleaseFastMutex(&xppdd->backend_state_mutex);
  FUNCTION_EXIT();

  return;
}

static VOID
XenPci_BackendStateHandler(char *path, PVOID context)
{
  UNREFERENCED_PARAMETER(path);

  /* check that path == device/id/state */
  //RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->path);

  XenPci_UpdateBackendState(context);
}

static NTSTATUS
XenPci_GetBackendAndAddWatch(WDFDEVICE device)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  char path[128];
  PCHAR res;
  PCHAR value;

  FUNCTION_ENTER();
  /* Get backend path */
  RtlStringCbPrintfA(path, ARRAY_SIZE(path),
    "%s/backend", xppdd->path);
  res = XenBus_Read(xpdd, XBT_NIL, path, &value);
  if (res)
  {
    KdPrint((__DRIVER_NAME "    Failed to read backend path\n"));
    XenPci_FreeMem(res);
    return STATUS_UNSUCCESSFUL;
  }
  RtlStringCbCopyA(xppdd->backend_path, ARRAY_SIZE(xppdd->backend_path), value);
  XenPci_FreeMem(value);

  /* Get backend id */
  RtlStringCbPrintfA(path, ARRAY_SIZE(path),
    "%s/backend-id", xppdd->path);
  res = XenBus_Read(xpdd, XBT_NIL, path, &value);
  if (res) {
    KdPrint((__DRIVER_NAME "    Failed to read backend id\n"));
    XenPci_FreeMem(res);
    return STATUS_UNSUCCESSFUL;
  }
  xppdd->backend_id = (domid_t)atoi(value);
  XenPci_FreeMem(value);

  /* Add watch on backend state */
  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
  XenBus_AddWatch(xpdd, XBT_NIL, path, XenPci_BackendStateHandler, device);

  FUNCTION_EXIT();  
  return STATUS_SUCCESS;
}

static NTSTATUS
XenConfig_InitConfigPage(WDFDEVICE device)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  //PXENCONFIG_DEVICE_DATA xcdd = (PXENCONFIG_DEVICE_DATA)device_object->DeviceExtension;
  //PXENPCI_PDO_DEVICE_DATA xppdd = (PXENPCI_PDO_DEVICE_DATA)device_object->DeviceExtension;
  //PXENPCI_DEVICE_DATA xpdd = xppdd->bus_fdo->DeviceExtension;
  PUCHAR ptr;
  PDEVICE_OBJECT curr, prev;
  PDRIVER_OBJECT fdo_driver_object;
  PUCHAR fdo_driver_extension;
  
  FUNCTION_ENTER();
  
  ptr = MmGetMdlVirtualAddress(xppdd->config_page_mdl);
  curr = IoGetAttachedDeviceReference(WdfDeviceWdmGetDeviceObject(device));
  //curr = WdfDeviceWdmGetAttachedDevice(device);
  while (curr != NULL)
  {
    fdo_driver_object = curr->DriverObject;
    KdPrint((__DRIVER_NAME "     fdo_driver_object = %p\n", fdo_driver_object));
    if (fdo_driver_object)
    {
      fdo_driver_extension = IoGetDriverObjectExtension(fdo_driver_object, UlongToPtr(XEN_INIT_DRIVER_EXTENSION_MAGIC));
      KdPrint((__DRIVER_NAME "     fdo_driver_extension = %p\n", fdo_driver_extension));
      if (fdo_driver_extension)
      {
        memcpy(ptr, fdo_driver_extension, PAGE_SIZE);
        ObDereferenceObject(curr);
        break;
      }
    }
    prev = curr;
    curr = IoGetLowerDeviceObject(curr);
    ObDereferenceObject(prev);
  }
  
  FUNCTION_EXIT();
  
  return STATUS_SUCCESS;
}

static NTSTATUS
XenPci_EvtChn_Bind(PVOID context, evtchn_port_t Port, PXEN_EVTCHN_SERVICE_ROUTINE ServiceRoutine, PVOID ServiceContext)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_Bind(xpdd, Port, ServiceRoutine, ServiceContext, EVT_ACTION_FLAGS_DEFAULT);
}

static NTSTATUS
XenPci_EvtChn_BindDpc(PVOID context, evtchn_port_t Port, PXEN_EVTCHN_SERVICE_ROUTINE ServiceRoutine, PVOID ServiceContext)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_BindDpc(xpdd, Port, ServiceRoutine, ServiceContext, EVT_ACTION_FLAGS_DEFAULT);
}

static NTSTATUS
XenPci_EvtChn_Unbind(PVOID context, evtchn_port_t Port)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_Unbind(xpdd, Port);
}

static NTSTATUS
XenPci_EvtChn_Mask(PVOID context, evtchn_port_t Port)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_Mask(xpdd, Port);
}

static NTSTATUS
XenPci_EvtChn_Unmask(PVOID context, evtchn_port_t Port)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_Unmask(xpdd, Port);
}

static NTSTATUS
XenPci_EvtChn_Notify(PVOID context, evtchn_port_t Port)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_Notify(xpdd, Port);
}

static BOOLEAN
XenPci_EvtChn_AckEvent(PVOID context, evtchn_port_t port, BOOLEAN *last_interrupt)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return EvtChn_AckEvent(xpdd, port, last_interrupt);
}

typedef struct {
  PXEN_EVTCHN_SYNC_ROUTINE sync_routine;
  PVOID sync_context;
} sync_context_t;

static BOOLEAN
XenPci_EvtChn_Sync_Routine(WDFINTERRUPT interrupt, WDFCONTEXT context)
{
  sync_context_t *wdf_sync_context = context;
  UNREFERENCED_PARAMETER(interrupt);
  return wdf_sync_context->sync_routine(wdf_sync_context->sync_context);
}

static BOOLEAN
XenPci_EvtChn_Sync(PVOID context, PXEN_EVTCHN_SYNC_ROUTINE sync_routine, PVOID sync_context)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  sync_context_t wdf_sync_context;
  
  wdf_sync_context.sync_routine = sync_routine;
  wdf_sync_context.sync_context = sync_context;
  
  return WdfInterruptSynchronize(xpdd->interrupt, XenPci_EvtChn_Sync_Routine, &wdf_sync_context);
}

static grant_ref_t
XenPci_GntTbl_GrantAccess(PVOID context, uint32_t frame, int readonly, grant_ref_t ref, ULONG tag)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return GntTbl_GrantAccess(xpdd, xppdd->backend_id, frame, readonly, ref, tag);
}

static BOOLEAN
XenPci_GntTbl_EndAccess(PVOID context, grant_ref_t ref, BOOLEAN keepref, ULONG tag)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return GntTbl_EndAccess(xpdd, ref, keepref, tag);
}

static VOID
XenPci_GntTbl_PutRef(PVOID context, grant_ref_t ref, ULONG tag)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  GntTbl_PutRef(xpdd, ref, tag);
}

static grant_ref_t
XenPci_GntTbl_GetRef(PVOID context, ULONG tag)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  
  return GntTbl_GetRef(xpdd, tag);
}

PCHAR
XenPci_XenBus_Read(PVOID context, xenbus_transaction_t xbt, char *path, char **value)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  return XenBus_Read(xpdd, xbt, path, value);
}

PCHAR
XenPci_XenBus_Write(PVOID context, xenbus_transaction_t xbt, char *path, char *value)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  return XenBus_Write(xpdd, xbt, path, value);
}

PCHAR
XenPci_XenBus_Printf(PVOID context, xenbus_transaction_t xbt, char *path, char *fmt, ...)
{
  //PXENPCI_PDO_DEVICE_DATA xppdd = Context;
  //PXENPCI_DEVICE_DATA xpdd = xppdd->bus_fdo->DeviceExtension;
  //return XenBus_Printf(xpdd, xbt, path, value);
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(xbt);
  UNREFERENCED_PARAMETER(path);
  UNREFERENCED_PARAMETER(fmt);
  return NULL;
}

PCHAR
XenPci_XenBus_StartTransaction(PVOID context, xenbus_transaction_t *xbt)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  return XenBus_StartTransaction(xpdd, xbt);
}

PCHAR
XenPci_XenBus_EndTransaction(PVOID context, xenbus_transaction_t xbt, int abort, int *retry)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  return XenBus_EndTransaction(xpdd, xbt, abort, retry);
}

PCHAR
XenPci_XenBus_List(PVOID context, xenbus_transaction_t xbt, char *prefix, char ***contents)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  return XenBus_List(xpdd, xbt, prefix, contents);
}

PCHAR
XenPci_XenBus_AddWatch(PVOID context, xenbus_transaction_t xbt, char *path, PXENBUS_WATCH_CALLBACK ServiceRoutine, PVOID ServiceContext)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  PCHAR retval;
  
  FUNCTION_ENTER();
  retval = XenBus_AddWatch(xpdd, xbt, path, ServiceRoutine, ServiceContext);
  if (retval == NULL)
  {
    KdPrint((__DRIVER_NAME "     XenPci_XenBus_AddWatch - %s = NULL\n", path));
  }
  else
  {
    KdPrint((__DRIVER_NAME "     XenPci_XenBus_AddWatch - %s = %s\n", path, retval));
  }
  FUNCTION_EXIT();
  return retval;
}

PCHAR
XenPci_XenBus_RemWatch(PVOID context, xenbus_transaction_t xbt, char *path, PXENBUS_WATCH_CALLBACK ServiceRoutine, PVOID ServiceContext)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  return XenBus_RemWatch(xpdd, xbt, path, ServiceRoutine, ServiceContext);
}

/*
Called at PASSIVE_LEVEL
Called during restore
*/

static NTSTATUS
XenPci_ChangeFrontendState(WDFDEVICE device, ULONG frontend_state_set, ULONG backend_state_response, ULONG maximum_wait_ms)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  LARGE_INTEGER timeout;
  ULONG remaining;
  ULONG thiswait;
  char path[128];
  
  FUNCTION_ENTER();
  
  xppdd->frontend_state = frontend_state_set;

  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->path);
  XenBus_Printf(xpdd, XBT_NIL, path, "%d", frontend_state_set);

  remaining = maximum_wait_ms;

  while (xppdd->backend_state != backend_state_response)
  {
    thiswait = min((LONG)remaining, 1000); // 1 second or remaining time, whichever is less
    timeout.QuadPart = (LONGLONG)-1 * thiswait * 1000 * 10;
    if (KeWaitForSingleObject(&xppdd->backend_state_event, Executive, KernelMode, FALSE, &timeout) == STATUS_TIMEOUT)
    {
      /* it's possible that the workitems are blocked because the pagefile isn't available. Lets just re-read the backend value for now */
      XenPci_UpdateBackendState(device);
      remaining -= thiswait;
      if (remaining == 0)
      {
        KdPrint((__DRIVER_NAME "     Timed out waiting for %d!\n", backend_state_response));
        return STATUS_UNSUCCESSFUL;
      }
      KdPrint((__DRIVER_NAME "     Still waiting for %d (currently %d)...\n", backend_state_response, xppdd->backend_state));
    }
  }
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenPci_ChangeFrontendStateMap(WDFDEVICE device, PXENPCI_STATE_MAP_ELEMENT map)
{
  NTSTATUS status;
  
  FUNCTION_ENTER();
  while(map->front_target)
  {
    //KdPrint((__DRIVER_NAME "     Changing state to %d expecting %d\n", (ULONG)map->front_target, (ULONG)map->back_expected));
    if (!NT_SUCCESS(status = XenPci_ChangeFrontendState(device, (ULONG)map->front_target, (ULONG)map->back_expected, (ULONG)map->wait * 100)))
    {
      FUNCTION_EXIT();
      return status;
    }
    map++;
  }
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenPci_XenConfigDevice(WDFDEVICE device);

static NTSTATUS
XenPci_XenShutdownDevice(PVOID context)
{
  WDFDEVICE device = context;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  PUCHAR in_ptr;
  ULONG i;
  UCHAR type;
  PVOID setting;
  PVOID value;
  PVOID value2;

  FUNCTION_ENTER();

  if (xppdd->backend_state == XenbusStateConnected)
  {
    XenPci_ChangeFrontendStateMap(device, xppdd->xb_shutdown_map);
  }
  else if (xppdd->backend_state == XenbusStateClosing)
  {
      XenPci_ChangeFrontendState(device, XenbusStateClosed, XenbusStateClosed, 30000);
  }

  if (xppdd->assigned_resources_start != NULL)
  {
    ADD_XEN_INIT_RSP(&xppdd->assigned_resources_ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);
    in_ptr = xppdd->assigned_resources_start;
    while((type = GET_XEN_INIT_RSP(&in_ptr, &setting, &value, &value2)) != XEN_INIT_TYPE_END)
    {
      switch (type)
      {
      case XEN_INIT_TYPE_RING: /* frontend ring */
        FreePages(value);
        break;
      case XEN_INIT_TYPE_EVENT_CHANNEL: /* frontend event channel */
      case XEN_INIT_TYPE_EVENT_CHANNEL_DPC: /* frontend event channel bound to dpc */
      case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ: /* frontend event channel bound to irq */
        EvtChn_Unbind(xpdd, PtrToUlong(value));
        EvtChn_Close(xpdd, PtrToUlong(value));
        break;
      case XEN_INIT_TYPE_GRANT_ENTRIES:
        for (i = 0; i < PtrToUlong(value); i++)
          GntTbl_EndAccess(xpdd, ((grant_ref_t *)value2)[i], FALSE, PtrToUlong(setting));
        break;
      }
    }
    ExFreePoolWithTag(xppdd->assigned_resources_start, XENPCI_POOL_TAG);
    xppdd->assigned_resources_start = NULL;
  }

  FUNCTION_EXIT();

  return STATUS_SUCCESS;
}

struct dummy_sring {
    RING_IDX req_prod, req_event;
    RING_IDX rsp_prod, rsp_event;
    uint8_t  pad[48];
};

static NTSTATUS
XenPci_XenConfigDeviceSpecifyBuffers(WDFDEVICE device, PUCHAR src, PUCHAR dst)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  NTSTATUS status = STATUS_SUCCESS;
  ULONG i;
  char path[128];
  PCHAR setting, value;
  PCHAR res;
  PVOID address;
  UCHAR type;
  PUCHAR in_ptr;
  PUCHAR out_ptr;
  XENPCI_VECTORS vectors;
  ULONG event_channel;
  PMDL ring;
  grant_ref_t gref;
  PVOID value2;
  int map_no;
 
  FUNCTION_ENTER();

  xppdd->xb_pre_connect_map[0].front_target = 0;
  xppdd->xb_post_connect_map[0].front_target = 0;
  xppdd->xb_shutdown_map[0].front_target = 0;
  
  in_ptr = src;
  out_ptr = dst;
  
  // always add vectors
  vectors.magic = XEN_DATA_MAGIC;
  vectors.length = sizeof(XENPCI_VECTORS);
  vectors.context = device;
  vectors.EvtChn_Bind = XenPci_EvtChn_Bind;
  vectors.EvtChn_BindDpc = XenPci_EvtChn_BindDpc;
  vectors.EvtChn_Unbind = XenPci_EvtChn_Unbind;
  vectors.EvtChn_Mask = XenPci_EvtChn_Mask;
  vectors.EvtChn_Unmask = XenPci_EvtChn_Unmask;
  vectors.EvtChn_Notify = XenPci_EvtChn_Notify;
  vectors.EvtChn_AckEvent = XenPci_EvtChn_AckEvent;
  vectors.EvtChn_Sync = XenPci_EvtChn_Sync;
  vectors.GntTbl_GetRef = XenPci_GntTbl_GetRef;
  vectors.GntTbl_PutRef = XenPci_GntTbl_PutRef;
  vectors.GntTbl_GrantAccess = XenPci_GntTbl_GrantAccess;
  vectors.GntTbl_EndAccess = XenPci_GntTbl_EndAccess;
  vectors.XenPci_XenConfigDevice = XenPci_XenConfigDevice;
  vectors.XenPci_XenShutdownDevice = XenPci_XenShutdownDevice;
  RtlStringCbCopyA(vectors.path, 128, xppdd->path);
  RtlStringCbCopyA(vectors.backend_path, 128, xppdd->backend_path);
  //vectors.pdo_event_channel = xpdd->pdo_event_channel;
  vectors.XenBus_Read = XenPci_XenBus_Read;
  vectors.XenBus_Write = XenPci_XenBus_Write;
  vectors.XenBus_Printf = XenPci_XenBus_Printf;
  vectors.XenBus_StartTransaction = XenPci_XenBus_StartTransaction;
  vectors.XenBus_EndTransaction = XenPci_XenBus_EndTransaction;
  vectors.XenBus_List = XenPci_XenBus_List;
  vectors.XenBus_AddWatch = XenPci_XenBus_AddWatch;
  vectors.XenBus_RemWatch = XenPci_XenBus_RemWatch;

  ADD_XEN_INIT_RSP(&out_ptr, XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION, NULL, UlongToPtr(qemu_protocol_version), NULL);
  
  ADD_XEN_INIT_RSP(&out_ptr, XEN_INIT_TYPE_VECTORS, NULL, &vectors, NULL);
  ADD_XEN_INIT_RSP(&out_ptr, XEN_INIT_TYPE_STATE_PTR, NULL, &xppdd->device_state, NULL);
  
  // need to make sure we never get here while backend state is connected or closing...
  // first pass, possibly before state == Connected
  in_ptr = src;
  while((type = GET_XEN_INIT_REQ(&in_ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END)
  {
    ADD_XEN_INIT_REQ(&xppdd->requested_resources_ptr, type, setting, value, value2);

    switch (type)
    {
    case XEN_INIT_TYPE_WRITE_STRING: /* frontend setting = value */
      //KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_WRITE_STRING - %s = %s\n", setting, value));
      RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/%s", xppdd->path, setting);
      XenBus_Printf(xpdd, XBT_NIL, path, "%s", value);
      break;
    case XEN_INIT_TYPE_RING: /* frontend ring */
      /* we only allocate and do the SHARED_RING_INIT here */
      if ((ring = AllocatePage()) != 0)
      {
        address = MmGetMdlVirtualAddress(ring);
        KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_RING - %s = %p\n", setting, address));
        SHARED_RING_INIT((struct dummy_sring *)address);
        if ((gref = GntTbl_GrantAccess(
          xpdd, xppdd->backend_id, (ULONG)*MmGetMdlPfnArray(ring), FALSE, INVALID_GRANT_REF, (ULONG)'XPDO')) != INVALID_GRANT_REF)
        {
          RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/%s", xppdd->path, setting);
          KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_RING - %s = %d\n", setting, gref));
          XenBus_Printf(xpdd, XBT_NIL, path, "%d", gref);
          ADD_XEN_INIT_RSP(&out_ptr, type, setting, address, NULL);
          ADD_XEN_INIT_RSP(&xppdd->assigned_resources_ptr, type, setting, ring, NULL);
          // add the grant entry too so it gets freed automatically
          __ADD_XEN_INIT_UCHAR(&xppdd->assigned_resources_ptr, XEN_INIT_TYPE_GRANT_ENTRIES);
          __ADD_XEN_INIT_ULONG(&xppdd->assigned_resources_ptr, (ULONG)'XPDO');
          __ADD_XEN_INIT_ULONG(&xppdd->assigned_resources_ptr, 1);
          __ADD_XEN_INIT_ULONG(&xppdd->assigned_resources_ptr, gref);
        }
        else
        {
          FreePages(ring);
          status = STATUS_UNSUCCESSFUL;
          goto error;
        }
      }
      else
      {
        status = STATUS_UNSUCCESSFUL;
        goto error;
      }
      break;
    case XEN_INIT_TYPE_EVENT_CHANNEL: /* frontend event channel */
    case XEN_INIT_TYPE_EVENT_CHANNEL_DPC: /* frontend event channel bound to dpc */
    case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ: /* frontend event channel bound to irq */
      if ((event_channel = EvtChn_AllocUnbound(xpdd, xppdd->backend_id)) != 0)
      {
        KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_EVENT_CHANNEL - %s = %d\n", setting, event_channel));
        RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/%s", xppdd->path, setting);
        XenBus_Printf(xpdd, XBT_NIL, path, "%d", event_channel);
        ADD_XEN_INIT_RSP(&out_ptr, type, setting, UlongToPtr(event_channel), NULL);
        ADD_XEN_INIT_RSP(&xppdd->assigned_resources_ptr, type, setting, UlongToPtr(event_channel), NULL);
        if (type == XEN_INIT_TYPE_EVENT_CHANNEL_IRQ)
        {
          EvtChn_BindIrq(xpdd, event_channel, xppdd->irq_vector, path, EVT_ACTION_FLAGS_DEFAULT);
        }
        else if (type == XEN_INIT_TYPE_EVENT_CHANNEL_DPC)
        {
          #pragma warning(suppress:4055)
          EvtChn_BindDpc(xpdd, event_channel, (PXEN_EVTCHN_SERVICE_ROUTINE)value, value2, EVT_ACTION_FLAGS_DEFAULT);
        }
        else
        {
          #pragma warning(suppress:4055)
          EvtChn_Bind(xpdd, event_channel, (PXEN_EVTCHN_SERVICE_ROUTINE)value, value2, EVT_ACTION_FLAGS_DEFAULT);
        }
      }
      else
      {
        status = STATUS_UNSUCCESSFUL;
        goto error;
      }
      break;
    case XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT:
      map_no = 0;
      while ((xppdd->xb_pre_connect_map[map_no].front_target = __GET_XEN_INIT_UCHAR(&in_ptr)) != 0)
      {
         xppdd->xb_pre_connect_map[map_no].back_expected = __GET_XEN_INIT_UCHAR(&in_ptr);
         xppdd->xb_pre_connect_map[map_no].wait = __GET_XEN_INIT_UCHAR(&in_ptr);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_pre_connect_map[map_no].front_target);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_pre_connect_map[map_no].back_expected);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_pre_connect_map[map_no].wait);
         map_no++;
      }
      __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, 0);
      break;
    case XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT:
      map_no = 0;
      while ((xppdd->xb_post_connect_map[map_no].front_target = __GET_XEN_INIT_UCHAR(&in_ptr)) != 0)
      {
         xppdd->xb_post_connect_map[map_no].back_expected = __GET_XEN_INIT_UCHAR(&in_ptr);
         xppdd->xb_post_connect_map[map_no].wait = __GET_XEN_INIT_UCHAR(&in_ptr);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_post_connect_map[map_no].front_target);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_post_connect_map[map_no].back_expected);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_post_connect_map[map_no].wait);
         map_no++;
      }
      __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, 0);
      break;
    case XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN:
      map_no = 0;
      while ((xppdd->xb_shutdown_map[map_no].front_target = __GET_XEN_INIT_UCHAR(&in_ptr)) != 0)
      {
         xppdd->xb_shutdown_map[map_no].back_expected = __GET_XEN_INIT_UCHAR(&in_ptr);
         xppdd->xb_shutdown_map[map_no].wait = __GET_XEN_INIT_UCHAR(&in_ptr);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_shutdown_map[map_no].front_target);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_shutdown_map[map_no].back_expected);
         __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, xppdd->xb_shutdown_map[map_no].wait);
         map_no++;
      }
      __ADD_XEN_INIT_UCHAR(&xppdd->requested_resources_ptr, 0);
      break;
    }
  }
  if (!NT_SUCCESS(status))
  {
    goto error;
  }

  if (XenPci_ChangeFrontendStateMap(device, xppdd->xb_pre_connect_map) != STATUS_SUCCESS)
  {
    status = STATUS_UNSUCCESSFUL;
    goto error;
  }

  // second pass, possibly after state == Connected
  in_ptr = src;
  while((type = GET_XEN_INIT_REQ(&in_ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END)
  {
    switch(type)
    {
    case XEN_INIT_TYPE_READ_STRING_BACK:
    case XEN_INIT_TYPE_READ_STRING_FRONT:
      if (type == XEN_INIT_TYPE_READ_STRING_FRONT)
        RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/%s", xppdd->path, setting);
      else
        RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/%s", xppdd->backend_path, setting);
      res = XenBus_Read(xpdd, XBT_NIL, path, &value);
      if (res)
      {
        KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_READ_STRING - %s = <failed>\n", setting));
        XenPci_FreeMem(res);
        ADD_XEN_INIT_RSP(&out_ptr, type, setting, "", "");
      }
      else
      {
        //KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_READ_STRING - %s = %s\n", setting, value));
        ADD_XEN_INIT_RSP(&out_ptr, type, setting, value, value2);
        XenPci_FreeMem(value);
      }
      break;
    case XEN_INIT_TYPE_VECTORS:
      // this is always done so ignore the request
      break;
    case XEN_INIT_TYPE_GRANT_ENTRIES:
      //KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_GRANT_ENTRIES - %d\n", PtrToUlong(value)));
      __ADD_XEN_INIT_UCHAR(&out_ptr, type);
      __ADD_XEN_INIT_UCHAR(&xppdd->assigned_resources_ptr, type);
      __ADD_XEN_INIT_ULONG(&out_ptr, PtrToUlong(setting));
      __ADD_XEN_INIT_ULONG(&xppdd->assigned_resources_ptr, PtrToUlong(setting));
      __ADD_XEN_INIT_ULONG(&out_ptr, PtrToUlong(value));
      __ADD_XEN_INIT_ULONG(&xppdd->assigned_resources_ptr, PtrToUlong(value));
      for (i = 0; i < PtrToUlong(value); i++)
      {
        gref = GntTbl_GetRef(xpdd, PtrToUlong(setting));
        __ADD_XEN_INIT_ULONG(&out_ptr, gref);
        __ADD_XEN_INIT_ULONG(&xppdd->assigned_resources_ptr, gref);
      }
      break;
    /* just need to eat these */
    case XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT:
    case XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT:
    case XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN:
      while ((__GET_XEN_INIT_UCHAR(&in_ptr)) != 0)
      {
         __GET_XEN_INIT_UCHAR(&in_ptr);
         __GET_XEN_INIT_UCHAR(&in_ptr);
      }
      break;
    }
  }
  if (qemu_hide_flags_value)
  {
    ADD_XEN_INIT_RSP(&out_ptr, XEN_INIT_TYPE_QEMU_HIDE_FLAGS, NULL, UlongToPtr(qemu_hide_flags_value), NULL);
  }
  else
  {
    DECLARE_UNICODE_STRING_SIZE(my_device_name, 128);
    
    RtlUnicodeStringPrintf(&my_device_name, L"#%S#", xppdd->device);
    
    for (i = 0; i < WdfCollectionGetCount(qemu_hide_devices); i++)
    {
      WDFSTRING wdf_string = WdfCollectionGetItem(qemu_hide_devices, i);
      UNICODE_STRING hide_device_name;
      
      WdfStringGetUnicodeString(wdf_string, &hide_device_name);
      
      if (RtlCompareUnicodeString(&hide_device_name, &my_device_name, TRUE) != 0)
      {
        ADD_XEN_INIT_RSP(&out_ptr, XEN_INIT_TYPE_QEMU_HIDE_FILTER, NULL, NULL, NULL);
        break;
      }
    }
  }
  
  ADD_XEN_INIT_RSP(&out_ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);

  if (XenPci_ChangeFrontendStateMap(device, xppdd->xb_post_connect_map) != STATUS_SUCCESS)
  {
    status = STATUS_UNSUCCESSFUL;
    goto error;
  }
  FUNCTION_EXIT();
  return status;

error:
  KdPrint((__DRIVER_NAME "     Error\n"));
  XenPci_ChangeFrontendState(device, XenbusStateInitialising, XenbusStateInitWait, 2000);
  FUNCTION_EXIT_STATUS(status);
  return status;
}

static NTSTATUS
XenPci_XenConfigDevice(WDFDEVICE device)
{
  NTSTATUS status;
  PUCHAR src, dst;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);

  src = ExAllocatePoolWithTag(NonPagedPool, xppdd->config_page_length, XENPCI_POOL_TAG);
  dst = MmMapIoSpace(xppdd->config_page_phys, xppdd->config_page_length, MmNonCached);
  memcpy(src, dst, xppdd->config_page_length);
  
  status = XenPci_XenConfigDeviceSpecifyBuffers(device, src, dst);

  MmUnmapIoSpace(dst, xppdd->config_page_length);
  ExFreePoolWithTag(src, XENPCI_POOL_TAG);
  
  return status;
}

static NTSTATUS
XenPciPdo_EvtDeviceWdmIrpPreprocess_START_DEVICE(WDFDEVICE device, PIRP irp)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  PIO_STACK_LOCATION stack;
  PCM_PARTIAL_RESOURCE_LIST prl;
  PCM_PARTIAL_RESOURCE_DESCRIPTOR prd;
  ULONG i;
  //char path[128];
  //PMDL mdl;
 
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     %s\n", xppdd->path));

  stack = IoGetCurrentIrpStackLocation(irp);

  prl = &stack->Parameters.StartDevice.AllocatedResources->List[0].PartialResourceList;
  for (i = 0; i < prl->Count; i++)
  {
    prd = & prl->PartialDescriptors[i];
    switch (prd->Type)
    {
    case CmResourceTypeMemory:
      if (prd->u.Memory.Start.QuadPart == xpdd->platform_mmio_addr.QuadPart && prd->u.Memory.Length == 0)
      {
        prd->u.Memory.Start.QuadPart = MmGetMdlPfnArray(xppdd->config_page_mdl)[0] << PAGE_SHIFT;
        prd->u.Memory.Length = MmGetMdlByteCount(xppdd->config_page_mdl);
      }
      else if (prd->u.Memory.Start.QuadPart == xpdd->platform_mmio_addr.QuadPart + 1 && prd->u.Memory.Length == 0)
      {
        RtlZeroMemory(prd, sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR));
        prd->Type = CmResourceTypeInterrupt;
        prd->ShareDisposition = CmResourceShareShared;
        prd->Flags = (xpdd->irq_mode == Latched)?CM_RESOURCE_INTERRUPT_LATCHED:CM_RESOURCE_INTERRUPT_LEVEL_SENSITIVE;
        prd->u.Interrupt.Level = 0;       // Set group and level to zero (group = upper word)
        prd->u.Interrupt.Level = xpdd->irq_number & 0xffff; // Only set the lower word
        prd->u.Interrupt.Vector = xpdd->irq_number;
        prd->u.Interrupt.Affinity = xpdd->irq_affinity; //KeQueryActiveProcessors();
        xppdd->irq_number = xpdd->irq_number;
      }
      break;
    }
  }

  prl = &stack->Parameters.StartDevice.AllocatedResourcesTranslated->List[0].PartialResourceList;
  for (i = 0; i < prl->Count; i++)
  {
    prd = & prl->PartialDescriptors[i];
    switch (prd->Type)
    {
    case CmResourceTypeMemory:
      KdPrint((__DRIVER_NAME "     CmResourceTypeMemory (%d)\n", i));
      KdPrint((__DRIVER_NAME "     Start = %08x, Length = %d\n", prd->u.Memory.Start.LowPart, prd->u.Memory.Length));
      if (prd->u.Memory.Start.QuadPart == xpdd->platform_mmio_addr.QuadPart)
      {
        if (prd->u.Memory.Length == 0)
        {
          KdPrint((__DRIVER_NAME "     pfn[0] = %08x\n", (ULONG)MmGetMdlPfnArray(xppdd->config_page_mdl)[0]));
          prd->u.Memory.Start.QuadPart = (ULONGLONG)MmGetMdlPfnArray(xppdd->config_page_mdl)[0] << PAGE_SHIFT;
          prd->u.Memory.Length = MmGetMdlByteCount(xppdd->config_page_mdl);
          KdPrint((__DRIVER_NAME "     New Start = %08x%08x, Length = %d\n", prd->u.Memory.Start.HighPart, prd->u.Memory.Start.LowPart, prd->u.Memory.Length));
        }
        xppdd->config_page_phys = prd->u.Memory.Start;
        xppdd->config_page_length = prd->u.Memory.Length;
        xppdd->requested_resources_start = xppdd->requested_resources_ptr = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);
        //xppdd->assigned_resources_start = xppdd->assigned_resources_ptr = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);
        
#if 0
        status = XenPci_XenConfigDevice(device);
        if (!NT_SUCCESS(status))
        {
          RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
          XenBus_RemWatch(xpdd, XBT_NIL, path, XenPci_BackendStateHandler, device);
          FUNCTION_EXIT_STATUS(status);
          return status;
        }
#endif
      }
      else if (prd->u.Memory.Start.QuadPart == xpdd->platform_mmio_addr.QuadPart + 1 && prd->u.Memory.Length == 0)
      {
        RtlZeroMemory(prd, sizeof(CM_PARTIAL_RESOURCE_DESCRIPTOR));
        prd->Type = CmResourceTypeInterrupt;
        prd->ShareDisposition = CmResourceShareShared;
        prd->Flags = (xpdd->irq_mode == Latched)?CM_RESOURCE_INTERRUPT_LATCHED:CM_RESOURCE_INTERRUPT_LEVEL_SENSITIVE;
        prd->u.Interrupt.Level = 0;       // Set group and level to zero (group = upper word)
        prd->u.Interrupt.Level = xpdd->irq_level & 0xffff; // Only set the lower word
        prd->u.Interrupt.Vector = xpdd->irq_vector;
        prd->u.Interrupt.Affinity = xpdd->irq_affinity; //KeQueryActiveProcessors();
        xppdd->irq_vector = xpdd->irq_vector;
        xppdd->irq_level = xpdd->irq_level;
      }
      break;
    }
  }

  IoSkipCurrentIrpStackLocation(irp);
  
  FUNCTION_EXIT();

  return WdfDeviceWdmDispatchPreprocessedIrp(device, irp);
}

#if 0
static NTSTATUS
XenPciPdo_EvtDeviceResourcesQuery(WDFDEVICE device, WDFCMRESLIST resources)
{
}
#endif

static NTSTATUS
XenPciPdo_EvtDeviceResourceRequirementsQuery(WDFDEVICE device, WDFIORESREQLIST requirements_list)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  WDFIORESLIST res_list;
  IO_RESOURCE_DESCRIPTOR ird;

  //FUNCTION_ENTER();
  
  WdfIoResourceRequirementsListSetInterfaceType(requirements_list, PNPBus);
  
  WdfIoResourceListCreate(requirements_list, WDF_NO_OBJECT_ATTRIBUTES, &res_list);
  ird.Option = 0;
  ird.Type = CmResourceTypeMemory;
  ird.ShareDisposition = CmResourceShareShared;
  ird.Flags = CM_RESOURCE_MEMORY_READ_WRITE | CM_RESOURCE_MEMORY_CACHEABLE;
  ird.u.Memory.MinimumAddress.QuadPart = xpdd->platform_mmio_addr.QuadPart;
  ird.u.Memory.MaximumAddress.QuadPart = xpdd->platform_mmio_addr.QuadPart;
  ird.u.Memory.Length = 0;
  ird.u.Memory.Alignment = 1; //PAGE_SIZE;
  WdfIoResourceListAppendDescriptor(res_list, &ird);
  
  ird.Option = 0;
  ird.Type = CmResourceTypeMemory;
  ird.ShareDisposition = CmResourceShareShared;
  ird.Flags = CM_RESOURCE_MEMORY_READ_WRITE | CM_RESOURCE_MEMORY_CACHEABLE;
  ird.u.Memory.MinimumAddress.QuadPart = xpdd->platform_mmio_addr.QuadPart + 1;
  ird.u.Memory.MaximumAddress.QuadPart = xpdd->platform_mmio_addr.QuadPart + 1;
  ird.u.Memory.Length = 0;
  ird.u.Memory.Alignment = 1; //PAGE_SIZE;
  WdfIoResourceListAppendDescriptor(res_list, &ird);
  
  WdfIoResourceRequirementsListAppendIoResList(requirements_list, res_list);

  //FUNCTION_EXIT();
  
  return STATUS_SUCCESS;
}

NTSTATUS
XenPciPdo_EvtDeviceD0Entry(WDFDEVICE device, WDF_POWER_DEVICE_STATE previous_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  CHAR path[128];
  
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     path = %s\n", xppdd->path));

  switch (previous_state)
  {
  case WdfPowerDeviceD0:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD1:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD2:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD2\n"));
    break;
  case WdfPowerDeviceD3:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3\n"));
    if (xppdd->hiber_usage_kludge)
    {
      KdPrint((__DRIVER_NAME "     (but really WdfPowerDevicePrepareForHibernation)\n"));
      previous_state = WdfPowerDevicePrepareForHibernation;
    }
    break;
  case WdfPowerDeviceD3Final:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3Final\n"));
    break;
  case WdfPowerDevicePrepareForHibernation:
    KdPrint((__DRIVER_NAME "     WdfPowerDevicePrepareForHibernation\n"));
    break;  
  default:
    KdPrint((__DRIVER_NAME "     Unknown WdfPowerDevice state %d\n", previous_state));
    break;  
  }

  status = XenPci_GetBackendAndAddWatch(device);
  if (!NT_SUCCESS(status))
  {
    WdfDeviceSetFailed(device, WdfDeviceFailedNoRestart);
    FUNCTION_EXIT_STATUS(status);
    return status;
  }

  if (previous_state == WdfPowerDeviceD3 || previous_state == WdfPowerDeviceD3Final)
  {
    xppdd->requested_resources_ptr = xppdd->requested_resources_start;
    xppdd->assigned_resources_start = xppdd->assigned_resources_ptr = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);
    XenConfig_InitConfigPage(device);
    status = XenPci_XenConfigDevice(device);
  }
  else if (previous_state == WdfPowerDevicePrepareForHibernation)
  {
    PVOID src, dst;
    
    ADD_XEN_INIT_REQ(&xppdd->requested_resources_ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);
    src = xppdd->requested_resources_start;
    xppdd->requested_resources_ptr = xppdd->requested_resources_start = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);
    xppdd->assigned_resources_ptr = xppdd->assigned_resources_start;

    dst = MmMapIoSpace(xppdd->config_page_phys, xppdd->config_page_length, MmNonCached);

    status = XenPci_XenConfigDeviceSpecifyBuffers(device, src, dst);

    MmUnmapIoSpace(dst, xppdd->config_page_length);
    ExFreePoolWithTag(src, XENPCI_POOL_TAG);
  }

  if (!NT_SUCCESS(status))
  {
    RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
    XenBus_RemWatch(xpdd, XBT_NIL, path, XenPci_BackendStateHandler, device);
    WdfDeviceSetFailed(device, WdfDeviceFailedNoRestart);
    FUNCTION_EXIT_STATUS(status);
    return status;
  }

  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPciPdo_EvtDeviceD0Exit(WDFDEVICE device, WDF_POWER_DEVICE_STATE target_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  char path[128];
  
  UNREFERENCED_PARAMETER(device);
  UNREFERENCED_PARAMETER(target_state);
  
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     path = %s\n", xppdd->path));
  
  switch (target_state)
  {
  case WdfPowerDeviceD0:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD1:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD2:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD2\n"));
    break;
  case WdfPowerDeviceD3:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3\n"));
    if (xppdd->hiber_usage_kludge)
    {
      KdPrint((__DRIVER_NAME "     (but really WdfPowerDevicePrepareForHibernation)\n"));
      target_state = WdfPowerDevicePrepareForHibernation;
    }
    break;
  case WdfPowerDeviceD3Final:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3Final\n"));
    break;
  case WdfPowerDevicePrepareForHibernation:
    KdPrint((__DRIVER_NAME "     WdfPowerDevicePrepareForHibernation\n"));
    break;  
  default:
    KdPrint((__DRIVER_NAME "     Unknown WdfPowerDevice state %d\n", target_state));
    break;  
  }
  
  if (target_state == WdfPowerDevicePrepareForHibernation)
  {
    KdPrint((__DRIVER_NAME "     not powering down as we are hibernating\n"));
    // should we set the backend state here so it's correct on resume???
  }
  else
  {
    status = XenPci_XenShutdownDevice(device);
  }
  
  /* Remove watch on backend state */
  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
  XenBus_RemWatch(xpdd, XBT_NIL, path, XenPci_BackendStateHandler, device);
  
  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPciPdo_EvtDevicePrepareHardware(WDFDEVICE device, WDFCMRESLIST resources_raw, WDFCMRESLIST resources_translated)
{
  NTSTATUS status = STATUS_SUCCESS;

  UNREFERENCED_PARAMETER(device);
  UNREFERENCED_PARAMETER(resources_raw);
  UNREFERENCED_PARAMETER(resources_translated);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPciPdo_EvtDeviceReleaseHardware(WDFDEVICE device, WDFCMRESLIST resources_translated)
{
  NTSTATUS status = STATUS_SUCCESS;
  
  UNREFERENCED_PARAMETER(device);
  UNREFERENCED_PARAMETER(resources_translated);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  
  return status;
}

static VOID
XenPciPdo_EvtDeviceUsageNotification(WDFDEVICE device, WDF_SPECIAL_FILE_TYPE notification_type, BOOLEAN is_in_notification_path)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);

  FUNCTION_ENTER();
  
  KdPrint((__DRIVER_NAME "     path = %s\n", xppdd->path));
  switch (notification_type)
  {
  case WdfSpecialFilePaging:
    KdPrint((__DRIVER_NAME "     notification_type = Paging, flag = %d\n", is_in_notification_path));
    break;
  case WdfSpecialFileHibernation:
    xppdd->hiber_usage_kludge = is_in_notification_path;
    KdPrint((__DRIVER_NAME "     notification_type = Hibernation, flag = %d\n", is_in_notification_path));
    break;
  case WdfSpecialFileDump:
    KdPrint((__DRIVER_NAME "     notification_type = Dump, flag = %d\n", is_in_notification_path));
    break;
  default:
    KdPrint((__DRIVER_NAME "     notification_type = %d, flag = %d\n", notification_type, is_in_notification_path));
    break;
  }

  FUNCTION_EXIT();
}

static VOID
XenPci_EvtDevicePnpStateChange(WDFDEVICE device, PCWDF_DEVICE_PNP_NOTIFICATION_DATA notification_data)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  
  //FUNCTION_ENTER();
  
  if (xppdd->backend_initiated_remove
    && notification_data->Type == StateNotificationEnterState
    && notification_data->Data.EnterState.CurrentState == WdfDevStatePnpQueryRemovePending 
    && notification_data->Data.EnterState.NewState == WdfDevStatePnpQueryCanceled)
  {
    PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
    
    KdPrint((__DRIVER_NAME "     Eject failed, doing surprise removal\n"));
    xppdd->do_not_enumerate = TRUE;
    XenPci_EvtChildListScanForChildren(xpdd->child_list);
  }
  
  //FUNCTION_EXIT();
  
  //return STATUS_SUCCESS;
}

NTSTATUS
XenPci_EvtChildListCreateDevice(WDFCHILDLIST child_list,
  PWDF_CHILD_IDENTIFICATION_DESCRIPTION_HEADER identification_header,
  PWDFDEVICE_INIT child_init)
{
  NTSTATUS status = STATUS_SUCCESS;
  WDF_OBJECT_ATTRIBUTES child_attributes;
  WDFDEVICE child_device;
  PXENPCI_PDO_IDENTIFICATION_DESCRIPTION identification = (PXENPCI_PDO_IDENTIFICATION_DESCRIPTION)identification_header;
  WDF_DEVICE_PNP_CAPABILITIES child_pnp_capabilities;
  DECLARE_UNICODE_STRING_SIZE(buffer, 512);
  DECLARE_CONST_UNICODE_STRING(location, L"Xen Bus");
  PXENPCI_PDO_DEVICE_DATA xppdd;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(WdfChildListGetDevice(child_list));
  WDF_PDO_EVENT_CALLBACKS pdo_callbacks;
  WDF_PNPPOWER_EVENT_CALLBACKS child_pnp_power_callbacks;
  UCHAR pnp_minor_functions[] = { IRP_MN_START_DEVICE };
  WDF_DEVICE_POWER_CAPABILITIES child_power_capabilities;
  
  FUNCTION_ENTER();

  WdfDeviceInitSetDeviceType(child_init, FILE_DEVICE_UNKNOWN);
  
  WDF_PNPPOWER_EVENT_CALLBACKS_INIT(&child_pnp_power_callbacks);
  child_pnp_power_callbacks.EvtDeviceD0Entry = XenPciPdo_EvtDeviceD0Entry;
  //child_pnp_power_callbacks.EvtDeviceD0EntryPostInterruptsEnabled = XenPciPdo_EvtDeviceD0EntryPostInterruptsEnabled;
  child_pnp_power_callbacks.EvtDeviceD0Exit = XenPciPdo_EvtDeviceD0Exit;
  //child_pnp_power_callbacks.EvtDeviceD0ExitPreInterruptsDisabled = XenPciPdo_EvtDeviceD0ExitPreInterruptsDisabled;
  child_pnp_power_callbacks.EvtDevicePrepareHardware = XenPciPdo_EvtDevicePrepareHardware;
  child_pnp_power_callbacks.EvtDeviceReleaseHardware = XenPciPdo_EvtDeviceReleaseHardware;
  child_pnp_power_callbacks.EvtDeviceUsageNotification = XenPciPdo_EvtDeviceUsageNotification;
  WdfDeviceInitSetPnpPowerEventCallbacks(child_init, &child_pnp_power_callbacks);

  KdPrint((__DRIVER_NAME "     device = '%s', index = '%d', path = '%s'\n",
    identification->device, identification->index, identification->path));
  
  status = WdfDeviceInitAssignWdmIrpPreprocessCallback(child_init, XenPciPdo_EvtDeviceWdmIrpPreprocess_START_DEVICE,
    IRP_MJ_PNP, pnp_minor_functions, ARRAY_SIZE(pnp_minor_functions));
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  
  WDF_PDO_EVENT_CALLBACKS_INIT(&pdo_callbacks);
  //pdo_callbacks.EvtDeviceResourcesQuery = XenPciPdo_EvtDeviceResourcesQuery;
  pdo_callbacks.EvtDeviceResourceRequirementsQuery = XenPciPdo_EvtDeviceResourceRequirementsQuery;
  //pdo_callbacks.EvtDeviceEject = XenPciPdo_EvtDeviceEject;
  //pdo_callbacks.EvtDeviceSetLock  = XenPciPdo_EvtDeviceSetLock;
  WdfPdoInitSetEventCallbacks(child_init, &pdo_callbacks);

  RtlUnicodeStringPrintf(&buffer, L"xen\\%S", identification->device);
  status = WdfPdoInitAssignDeviceID(child_init, &buffer);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  status = WdfPdoInitAddHardwareID(child_init, &buffer);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  status = WdfPdoInitAddCompatibleID(child_init, &buffer);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  
  RtlUnicodeStringPrintf(&buffer, L"%02d", identification->index);
  status = WdfPdoInitAssignInstanceID(child_init, &buffer);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  
  RtlUnicodeStringPrintf(&buffer, L"Xen %S device #%d", identification->device, identification->index);
  status = WdfPdoInitAddDeviceText(child_init, &buffer, &location, 0x0409);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  WdfPdoInitSetDefaultLocale(child_init, 0x0409);

  WdfDeviceInitSetPowerNotPageable(child_init);

  WdfDeviceInitRegisterPnpStateChangeCallback(child_init, WdfDevStatePnpQueryCanceled, XenPci_EvtDevicePnpStateChange, StateNotificationEnterState);
  
  WDF_OBJECT_ATTRIBUTES_INIT_CONTEXT_TYPE(&child_attributes, XENPCI_PDO_DEVICE_DATA);
  status = WdfDeviceCreate(&child_init, &child_attributes, &child_device);
  if (!NT_SUCCESS(status))
  {
    return status;
  }

  xppdd = GetXppdd(child_device);
  
  xppdd->wdf_device = child_device;
  xppdd->wdf_device_bus_fdo = WdfChildListGetDevice(child_list);

  xppdd->config_page_mdl = AllocateUncachedPage();

  xppdd->device_state.magic = XEN_DEVICE_STATE_MAGIC;
  xppdd->device_state.length = sizeof(XENPCI_DEVICE_STATE);
  xppdd->device_state.suspend_resume_state_pdo = SR_STATE_RUNNING;
  xppdd->device_state.suspend_resume_state_fdo = SR_STATE_RUNNING;
  xppdd->device_state.pdo_event_channel = xpdd->pdo_event_channel;
  WdfDeviceSetSpecialFileSupport(child_device, WdfSpecialFilePaging, TRUE);
  WdfDeviceSetSpecialFileSupport(child_device, WdfSpecialFileHibernation, TRUE);
  WdfDeviceSetSpecialFileSupport(child_device, WdfSpecialFileDump, TRUE);

  WDF_DEVICE_PNP_CAPABILITIES_INIT(&child_pnp_capabilities);
  child_pnp_capabilities.LockSupported = WdfFalse;
  child_pnp_capabilities.EjectSupported  = WdfTrue;
  child_pnp_capabilities.Removable  = WdfTrue;
  child_pnp_capabilities.DockDevice  = WdfFalse;
  child_pnp_capabilities.UniqueID  = WdfFalse;
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

  RtlStringCbCopyA(xppdd->path, ARRAY_SIZE(xppdd->path), identification->path);
  RtlStringCbCopyA(xppdd->device, ARRAY_SIZE(xppdd->device), identification->device);
  xppdd->index = identification->index;
  KeInitializeEvent(&xppdd->backend_state_event, SynchronizationEvent, FALSE);
  ExInitializeFastMutex(&xppdd->backend_state_mutex);
  xppdd->backend_state = XenbusStateUnknown;
  xppdd->frontend_state = XenbusStateUnknown;
  xppdd->backend_path[0] = '\0';
  xppdd->backend_id = 0;
    
  FUNCTION_EXIT();
  
  return status;
}

static __forceinline VOID
XenPci_Pdo_ChangeSuspendState(WDFDEVICE device, ULONG new_state)
{
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);

  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     setting pdo state to %d\n", new_state));
  xppdd->device_state.suspend_resume_state_pdo = new_state;
  KeMemoryBarrier();
  KdPrint((__DRIVER_NAME "     Notifying event channel %d\n", xpdd->pdo_event_channel));
  EvtChn_Notify(xpdd, xpdd->pdo_event_channel);    
  while(xppdd->device_state.suspend_resume_state_fdo != xppdd->device_state.suspend_resume_state_pdo)
  {
    KdPrint((__DRIVER_NAME "     waiting...\n"));
    KeWaitForSingleObject(&xpdd->pdo_suspend_event, Executive, KernelMode, FALSE, NULL);
  }
  KdPrint((__DRIVER_NAME "     fdo state set to %d\n", new_state));
  FUNCTION_EXIT();
}

/* called at PASSIVE_LEVEL */
NTSTATUS
XenPci_Pdo_Suspend(WDFDEVICE device)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  char path[128];
  PUCHAR in_ptr;
  UCHAR type;
  PVOID setting;
  PVOID value;
  PVOID value2;
  int i;

  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ " (%s)\n", xppdd->path));

  if (xppdd->backend_state == XenbusStateConnected)
  {
    xppdd->restart_on_resume = TRUE;
    XenPci_Pdo_ChangeSuspendState(device, SR_STATE_SUSPENDING);

    XenPci_ChangeFrontendState(device, XenbusStateClosing, XenbusStateClosing, 30000);
    XenPci_ChangeFrontendState(device, XenbusStateClosed, XenbusStateClosed, 30000);
    XenPci_ChangeFrontendState(device, XenbusStateInitialising, XenbusStateInitWait, 30000);

    if (xppdd->assigned_resources_start != NULL)
    {
      in_ptr = xppdd->assigned_resources_ptr;
      ADD_XEN_INIT_RSP(&in_ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);
      in_ptr = xppdd->assigned_resources_start;
      while((type = GET_XEN_INIT_RSP(&in_ptr, &setting, &value, &value2)) != XEN_INIT_TYPE_END)
      {
        switch (type)
        {
        case XEN_INIT_TYPE_RING: /* frontend ring */
          FreePages(value);
          break;
        case XEN_INIT_TYPE_EVENT_CHANNEL: /* frontend event channel */
        case XEN_INIT_TYPE_EVENT_CHANNEL_DPC: /* frontend event channel bound to dpc */
        case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ: /* frontend event channel bound to irq */
          EvtChn_Unbind(xpdd, PtrToUlong(value));
          EvtChn_Close(xpdd, PtrToUlong(value));
          break;
        case XEN_INIT_TYPE_GRANT_ENTRIES:
          for (i = 0; i < (int)PtrToUlong(value); i++)
            GntTbl_EndAccess(xpdd, ((grant_ref_t *)value2)[i], FALSE, PtrToUlong(setting));
          break;
        }
      }
    }

    RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
    XenBus_RemWatch(xpdd, XBT_NIL, path, XenPci_BackendStateHandler, device);  
  }
  else
  {
    xppdd->restart_on_resume = FALSE;
  }

  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPci_Pdo_Resume(WDFDEVICE device)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(device);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xppdd->wdf_device_bus_fdo);
  ULONG old_backend_state;
  PUCHAR src, dst;

  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     path = %s\n", xppdd->path));

  xppdd->device_state.pdo_event_channel = xpdd->pdo_event_channel;
  old_backend_state = xppdd->backend_state;

  if (xppdd->restart_on_resume)
  {  
    status = XenPci_GetBackendAndAddWatch(device);
  
    if (XenPci_ChangeFrontendState(device, XenbusStateInitialising, XenbusStateInitWait, 30000) != STATUS_SUCCESS)
    {
      KdPrint((__DRIVER_NAME "     Failed to change frontend state to Initialising\n"));
      // this is probably an unrecoverable situation...
      FUNCTION_EXIT();
      return STATUS_UNSUCCESSFUL;
    }
    if (xppdd->assigned_resources_ptr)
    {
      // reset things - feed the 'requested resources' back in
      ADD_XEN_INIT_REQ(&xppdd->requested_resources_ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);
      src = xppdd->requested_resources_start;
      xppdd->requested_resources_ptr = xppdd->requested_resources_start = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);;
      xppdd->assigned_resources_ptr = xppdd->assigned_resources_start;

      dst = MmMapIoSpace(xppdd->config_page_phys, xppdd->config_page_length, MmNonCached);

      status = XenPci_XenConfigDeviceSpecifyBuffers(device, src, dst);

      MmUnmapIoSpace(dst, xppdd->config_page_length);
      ExFreePoolWithTag(src, XENPCI_POOL_TAG);
    }
    if (XenPci_ChangeFrontendState(device, XenbusStateConnected, XenbusStateConnected, 30000) != STATUS_SUCCESS)
    {
      // this is definitely an unrecoverable situation...
      KdPrint((__DRIVER_NAME "     Failed to change frontend state to connected\n"));
      FUNCTION_EXIT();
      return STATUS_UNSUCCESSFUL;
    }
    XenPci_Pdo_ChangeSuspendState(device, SR_STATE_RESUMING);
    XenPci_Pdo_ChangeSuspendState(device, SR_STATE_RUNNING);
  }

  FUNCTION_EXIT();

  return STATUS_SUCCESS;
}
