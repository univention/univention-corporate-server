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

#pragma warning( disable : 4204 ) 
#pragma warning( disable : 4221 ) 

/* Not really necessary but keeps PREfast happy */
static EVT_WDF_WORKITEM XenBus_WatchWorkItemProc;

WDF_DECLARE_CONTEXT_TYPE(xsd_sockmsg_t)

struct write_req {
    void *data;
    unsigned len;
};

// This routine free's the rep structure if there was an error!!!
static char *errmsg(struct xsd_sockmsg *rep)
{
  char *res;

  if (!rep) {
    char msg[] = "No reply";
    size_t len = strlen(msg) + 1;
    return memcpy(ExAllocatePoolWithTag(NonPagedPool, len, XENPCI_POOL_TAG), msg, len);
  }
  if (rep->type != XS_ERROR)
    return NULL;
  res = ExAllocatePoolWithTag(NonPagedPool, rep->len + 1, XENPCI_POOL_TAG);
  memcpy(res, rep + 1, rep->len);
  res[rep->len] = 0;
  ExFreePoolWithTag(rep, XENPCI_POOL_TAG);
  return res;
}

static void memcpy_from_ring(void *Ring,
        void *Dest,
        int off,
        int len)
{
  int c1, c2;
  char *ring = Ring;
  char *dest = Dest;
  c1 = min(len, XENSTORE_RING_SIZE - off);
  c2 = len - c1;
  memcpy(dest, ring + off, c1);
  memcpy(dest + c1, ring, c2);
}

/* called with xenbus_mutex held */
static void xb_write(
  PXENPCI_DEVICE_DATA xpdd,
  PVOID data,
  ULONG len
)
{
  XENSTORE_RING_IDX prod;
  ULONG copy_len;
  PUCHAR ptr;
  ULONG remaining;
  
  //FUNCTION_ENTER();

  ASSERT(len <= XENSTORE_RING_SIZE);
  prod = xpdd->xen_store_interface->req_prod;
  ptr = data;
  remaining = len;
  while (remaining)
  {
    copy_len = min(remaining, XENSTORE_RING_SIZE - MASK_XENSTORE_IDX(prod));
    memcpy((PUCHAR)xpdd->xen_store_interface->req + MASK_XENSTORE_IDX(prod), ptr, copy_len);
    prod += (XENSTORE_RING_IDX)copy_len;
    ptr += copy_len;
    remaining -= copy_len;
  }
  /* Remote must see entire message before updating indexes */
  KeMemoryBarrier();
  xpdd->xen_store_interface->req_prod = prod;
  EvtChn_Notify(xpdd, xpdd->xen_store_evtchn);

  //FUNCTION_EXIT();
}

/* takes and releases xb_request_mutex */
static struct xsd_sockmsg *
xenbus_format_msg_reply(
  PXENPCI_DEVICE_DATA xpdd,
  int type,
  xenbus_transaction_t trans_id,
  struct write_req *req,
  int nr_reqs)
{
  struct xsd_sockmsg msg;
  struct xsd_sockmsg *reply;
  int i;

  //FUNCTION_ENTER();
  
  msg.type = type;
  msg.req_id = 0;
  msg.tx_id = trans_id;
  msg.len = 0;
  for (i = 0; i < nr_reqs; i++)
    msg.len += req[i].len;

  ExAcquireFastMutex(&xpdd->xb_request_mutex);
  xb_write(xpdd, &msg, sizeof(msg));
  for (i = 0; i < nr_reqs; i++)
    xb_write(xpdd, req[i].data, req[i].len);

  KeWaitForSingleObject(&xpdd->xb_request_complete_event, Executive, KernelMode, FALSE, NULL);
  reply = xpdd->xb_reply;
  xpdd->xb_reply = NULL;
  ExReleaseFastMutex(&xpdd->xb_request_mutex);

  //FUNCTION_EXIT();
  
  return reply;
}

/* takes and releases xb_request_mutex */
struct xsd_sockmsg *
XenBus_Raw(
  PXENPCI_DEVICE_DATA xpdd,
  struct xsd_sockmsg *msg)
{
  struct xsd_sockmsg *reply;
  
  //FUNCTION_ENTER();

  ExAcquireFastMutex(&xpdd->xb_request_mutex);
  xb_write(xpdd, msg, sizeof(struct xsd_sockmsg) + msg->len);
  KeWaitForSingleObject(&xpdd->xb_request_complete_event, Executive, KernelMode, FALSE, NULL);
  reply = xpdd->xb_reply;
  xpdd->xb_reply = NULL;
  ExReleaseFastMutex(&xpdd->xb_request_mutex);  

  //FUNCTION_EXIT();
    
  return reply;
}

/* Called at PASSIVE_LEVEL */
char *
XenBus_Read(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *path,
  char **value)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  struct write_req req[] = { {path, (ULONG)strlen(path) + 1} };
  struct xsd_sockmsg *rep;
  char *res;
  char *msg;

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  rep = xenbus_format_msg_reply(xpdd, XS_READ, xbt, req, ARRAY_SIZE(req));
  msg = errmsg(rep);
  if (msg) {
    *value = NULL;
    return msg;
  }
  res = ExAllocatePoolWithTag(NonPagedPool, rep->len + 1, XENPCI_POOL_TAG);
  memcpy(res, rep + 1, rep->len);
  res[rep->len] = 0;
  ExFreePoolWithTag(rep, XENPCI_POOL_TAG);
  *value = res;

  //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));

  return NULL;
}

/* Called at PASSIVE_LEVEL */
char *
XenBus_Write(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *path,
  char *value)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  struct write_req req[] = {
    {path, (ULONG)strlen(path) + 1},
    {value, (ULONG)strlen(value)},
  };
  struct xsd_sockmsg *rep;
  char *msg;

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  rep = xenbus_format_msg_reply(xpdd, XS_WRITE, xbt, req, ARRAY_SIZE(req));
  msg = errmsg(rep);
  if (msg)
    return msg;
  ExFreePoolWithTag(rep, XENPCI_POOL_TAG);

  return NULL;
}

/* Called at PASSIVE_LEVEL */
static VOID
XenBus_WatchWorkItemProc(WDFWORKITEM workitem)
{
  WDFDEVICE device = WdfWorkItemGetParentObject(workitem);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  xsd_sockmsg_t *msg;
  PCHAR path;
  int index;
  PXENBUS_WATCH_ENTRY entry;
  PXENBUS_WATCH_CALLBACK service_routine;
  PVOID service_context;  

  //FUNCTION_ENTER();
  msg = WdfObjectGetTypedContext(workitem, xsd_sockmsg_t);
  path = (PCHAR)msg + sizeof(xsd_sockmsg_t);
  index = atoi(path + strlen(path) + 1);
  if (index < 0 || index >= MAX_WATCH_ENTRIES)
  {
    KdPrint((__DRIVER_NAME "     Watch index %d out of range\n", index));
    WdfObjectDelete(workitem);
    //FUNCTION_ENTER();
    return;
  }
  ExAcquireFastMutex(&xpdd->xb_watch_mutex);
  entry = &xpdd->XenBus_WatchEntries[index];
  if (!entry->Active || !entry->ServiceRoutine)
  {
    KdPrint((__DRIVER_NAME "     No watch for index %d\n", index));
    ExReleaseFastMutex(&xpdd->xb_watch_mutex);
    WdfObjectDelete(workitem);
    //FUNCTION_ENTER();
    return;
  }
  entry->Count++;
  service_routine = entry->ServiceRoutine;
  service_context = entry->ServiceContext;
  service_routine(path, service_context);
  ExReleaseFastMutex(&xpdd->xb_watch_mutex);
  WdfObjectDelete(workitem);
  //FUNCTION_EXIT();
}    

/* Called at DISPATCH_LEVEL */
static VOID
XenBus_Dpc(PVOID ServiceContext)
{
  NTSTATUS status;
  PXENPCI_DEVICE_DATA xpdd = ServiceContext;
  xsd_sockmsg_t msg;
  ULONG msg_len;
  WDF_WORKITEM_CONFIG workitem_config;
  WDF_OBJECT_ATTRIBUTES workitem_attributes;
  WDFWORKITEM workitem;
  ULONG rsp_prod;

  //FUNCTION_ENTER();
  
  KeAcquireSpinLockAtDpcLevel(&xpdd->xb_ring_spinlock);

  /* snapshot rsp_prod so it doesn't change while we are looking at it */
  while ((rsp_prod = xpdd->xen_store_interface->rsp_prod) != xpdd->xen_store_interface->rsp_cons)
  {
    KeMemoryBarrier(); /* make sure the data in the ring is valid */
    if (!xpdd->xb_msg)
    {
      if (rsp_prod - xpdd->xen_store_interface->rsp_cons < sizeof(xsd_sockmsg_t))
      {
        //KdPrint((__DRIVER_NAME " +++ Message incomplete (not even a full header)\n"));
        break;
      }
      memcpy_from_ring(xpdd->xen_store_interface->rsp, &msg,
        MASK_XENSTORE_IDX(xpdd->xen_store_interface->rsp_cons), sizeof(xsd_sockmsg_t));
      xpdd->xb_msg = ExAllocatePoolWithTag(NonPagedPool, sizeof(xsd_sockmsg_t) + msg.len, XENPCI_POOL_TAG);
      memcpy(xpdd->xb_msg, &msg, sizeof(xsd_sockmsg_t));
      xpdd->xb_msg_offset = sizeof(xsd_sockmsg_t);
      xpdd->xen_store_interface->rsp_cons += sizeof(xsd_sockmsg_t);
    }

    msg_len = min(rsp_prod - xpdd->xen_store_interface->rsp_cons, sizeof(xsd_sockmsg_t) + xpdd->xb_msg->len - xpdd->xb_msg_offset);
    ASSERT(xpdd->xb_msg_offset + msg_len <= sizeof(xsd_sockmsg_t) + xpdd->xb_msg->len);
    memcpy_from_ring(xpdd->xen_store_interface->rsp,
      (PUCHAR)xpdd->xb_msg + xpdd->xb_msg_offset,
      MASK_XENSTORE_IDX(xpdd->xen_store_interface->rsp_cons),
      msg_len);
    xpdd->xen_store_interface->rsp_cons += msg_len;
    xpdd->xb_msg_offset += msg_len;

    if (xpdd->xb_msg_offset < sizeof(xsd_sockmsg_t) + xpdd->xb_msg->len)
    {
      //KdPrint((__DRIVER_NAME " +++ Message incomplete (header but not full body)\n"));
      EvtChn_Notify(xpdd, xpdd->xen_store_evtchn); /* there is room on the ring now */
      break;
    }

    if (xpdd->xb_msg->type != XS_WATCH_EVENT)
    {
      /* process reply - only ever one outstanding */
      ASSERT(xpdd->xb_reply == NULL);
      xpdd->xb_reply = xpdd->xb_msg;
      xpdd->xb_msg = NULL;
      KeSetEvent(&xpdd->xb_request_complete_event, IO_NO_INCREMENT, FALSE);
    }
    else
    {
      /* process watch */
      WDF_WORKITEM_CONFIG_INIT(&workitem_config, XenBus_WatchWorkItemProc);
      WDF_OBJECT_ATTRIBUTES_INIT_CONTEXT_TYPE(&workitem_attributes, xsd_sockmsg_t);
      workitem_attributes.ParentObject = xpdd->wdf_device;
      workitem_attributes.ContextSizeOverride = xpdd->xb_msg_offset;
      status = WdfWorkItemCreate(&workitem_config, &workitem_attributes, &workitem);
      if (!NT_SUCCESS(status))
      {
        KdPrint((__DRIVER_NAME "     Failed to create work item for watch\n"));
        continue;
      }
      memcpy(WdfObjectGetTypedContext(workitem, xsd_sockmsg_t), xpdd->xb_msg, xpdd->xb_msg_offset);
      xpdd->xb_msg = NULL;
      WdfWorkItemEnqueue(workitem);
    }
    EvtChn_Notify(xpdd, xpdd->xen_store_evtchn); /* there is room on the ring now */
  }
  KeReleaseSpinLockFromDpcLevel(&xpdd->xb_ring_spinlock);
  
  //FUNCTION_EXIT();
}

static NTSTATUS
XenBus_Connect(PXENPCI_DEVICE_DATA xpdd)
{
  PHYSICAL_ADDRESS pa_xen_store_interface;
  xen_ulong_t xen_store_mfn;

  xpdd->xen_store_evtchn = (evtchn_port_t)hvm_get_parameter(xpdd, HVM_PARAM_STORE_EVTCHN);
  xen_store_mfn = (xen_ulong_t)hvm_get_parameter(xpdd, HVM_PARAM_STORE_PFN);
  pa_xen_store_interface.QuadPart = (ULONGLONG)xen_store_mfn << PAGE_SHIFT;
  xpdd->xen_store_interface = MmMapIoSpace(pa_xen_store_interface, PAGE_SIZE, MmNonCached);

  EvtChn_BindDpc(xpdd, xpdd->xen_store_evtchn, XenBus_Dpc, xpdd, EVT_ACTION_FLAGS_NO_SUSPEND);
  
  return STATUS_SUCCESS;
}

static NTSTATUS
XenBus_Disconnect(PXENPCI_DEVICE_DATA xpdd)
{
  EvtChn_Unbind(xpdd, xpdd->xen_store_evtchn);

  MmUnmapIoSpace(xpdd->xen_store_interface, PAGE_SIZE);
  
  return STATUS_SUCCESS;
}

NTSTATUS
XenBus_Init(PXENPCI_DEVICE_DATA xpdd)
{
  NTSTATUS status;
  int i;
    
  FUNCTION_ENTER();

  ASSERT(KeGetCurrentIrql() == PASSIVE_LEVEL);

  KeInitializeSpinLock(&xpdd->xb_ring_spinlock);
  ExInitializeFastMutex(&xpdd->xb_request_mutex);
  ExInitializeFastMutex(&xpdd->xb_watch_mutex);

  for (i = 0; i < MAX_WATCH_ENTRIES; i++)
  {
    xpdd->XenBus_WatchEntries[i].Active = 0;
  }

  KeInitializeEvent(&xpdd->xb_request_complete_event, SynchronizationEvent, FALSE);

  status = XenBus_Connect(xpdd);
  if (!NT_SUCCESS(status))
  {
    FUNCTION_EXIT();
    return status;
  }
  
  FUNCTION_EXIT();

  return STATUS_SUCCESS;
}

char *
XenBus_SendRemWatch(
  PVOID context,
  xenbus_transaction_t xbt,
  char *path,
  int index)
{
  struct xsd_sockmsg *rep;
  char *msg;
  char Token[20];
  struct write_req req[2];

  req[0].data = path;
  req[0].len = (ULONG)strlen(path) + 1;

  RtlStringCbPrintfA(Token, ARRAY_SIZE(Token), "%d", index);
  req[1].data = Token;
  req[1].len = (ULONG)strlen(Token) + 1;

  rep = xenbus_format_msg_reply(context, XS_UNWATCH, xbt, req, ARRAY_SIZE(req));

  msg = errmsg(rep);
  if (msg)
    return msg;

  ExFreePoolWithTag(rep, XENPCI_POOL_TAG);

  return NULL;
}

NTSTATUS
XenBus_Halt(PXENPCI_DEVICE_DATA xpdd)
{
  int i;

  FUNCTION_ENTER();
  
  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  /* we need to remove the watches as a watch firing could lead to a XenBus_Read/Write/Printf */
  for (i = 0; i < MAX_WATCH_ENTRIES; i++)
  {
    if (xpdd->XenBus_WatchEntries[i].Active)
    {
      xpdd->XenBus_WatchEntries[i].Active = 0;
      XenBus_SendRemWatch(xpdd, XBT_NIL, xpdd->XenBus_WatchEntries[i].Path, i);
    }
  }

  XenBus_Disconnect(xpdd);

  FUNCTION_EXIT();

  return STATUS_SUCCESS;
}

char *
XenBus_List(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *pre,
  char ***contents)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  struct xsd_sockmsg *reply, *repmsg;
  struct write_req req[] = { { pre, (ULONG)strlen(pre)+1 } };
  ULONG nr_elems, x, i;
  char **res;
  char *msg;

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  repmsg = xenbus_format_msg_reply(xpdd, XS_DIRECTORY, xbt, req, ARRAY_SIZE(req));
  msg = errmsg(repmsg);
  if (msg)
  {
    *contents = NULL;
    return msg;
  }
  reply = repmsg + 1;
  for (x = nr_elems = 0; x < repmsg->len; x++)
  {
    nr_elems += (((char *)reply)[x] == 0);
  }
  res = ExAllocatePoolWithTag(NonPagedPool, sizeof(res[0]) * (nr_elems + 1),
    XENPCI_POOL_TAG);
  for (x = i = 0; i < nr_elems; i++)
  {
    int l = (int)strlen((char *)reply + x);
    res[i] = ExAllocatePoolWithTag(NonPagedPool, l + 1, XENPCI_POOL_TAG);
    memcpy(res[i], (char *)reply + x, l + 1);
    x += l + 1;
  }
  res[i] = NULL;
  ExFreePoolWithTag(repmsg, XENPCI_POOL_TAG);
  *contents = res;
  
  return NULL;
}

/* Called at PASSIVE_LEVEL */
static char *
XenBus_SendAddWatch(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *Path,
  int slot)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  struct xsd_sockmsg *rep;
  char *msg;
  char Token[20];
  struct write_req req[2];

  req[0].data = Path;
  req[0].len = (ULONG)strlen(Path) + 1;

  RtlStringCbPrintfA(Token, ARRAY_SIZE(Token), "%d", slot);
  req[1].data = Token;
  req[1].len = (ULONG)strlen(Token) + 1;

  rep = xenbus_format_msg_reply(xpdd, XS_WATCH, xbt, req, ARRAY_SIZE(req));

  msg = errmsg(rep);
  if (!msg)
    ExFreePoolWithTag(rep, XENPCI_POOL_TAG);

  return msg;
}

/* called at PASSIVE_LEVEL */
NTSTATUS
XenBus_Suspend(PXENPCI_DEVICE_DATA xpdd)
{
  int i;
  
  /* we need to remove the watches as a watch firing could lead to a XenBus_Read/Write/Printf */
  for (i = 0; i < MAX_WATCH_ENTRIES; i++) {
    if (xpdd->XenBus_WatchEntries[i].Active)
      XenBus_SendRemWatch(xpdd, XBT_NIL, xpdd->XenBus_WatchEntries[i].Path, i);
  }
  XenBus_Disconnect(xpdd);
  
  return STATUS_SUCCESS;
}

/* called at PASSIVE_LEVEL */
NTSTATUS
XenBus_Resume(PXENPCI_DEVICE_DATA xpdd)
{
  NTSTATUS status;
  int i;

  FUNCTION_ENTER();

  status = XenBus_Connect(xpdd);
  if (!NT_SUCCESS(status))
  {
    return status;
  }
  
  for (i = 0; i < MAX_WATCH_ENTRIES; i++)
  {
    if (xpdd->XenBus_WatchEntries[i].Active)
    {
      KdPrint((__DRIVER_NAME "     Adding watch for path = %s\n", xpdd->XenBus_WatchEntries[i].Path));
      XenBus_SendAddWatch(xpdd, XBT_NIL, xpdd->XenBus_WatchEntries[i].Path, i);
    }
  }

  FUNCTION_EXIT();
  
  return STATUS_SUCCESS;
}

char *
XenBus_AddWatch(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *Path,
  PXENBUS_WATCH_CALLBACK ServiceRoutine,
  PVOID ServiceContext)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  char *msg;
  int i;
  PXENBUS_WATCH_ENTRY w_entry;

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  ASSERT(strlen(Path) < ARRAY_SIZE(w_entry->Path));

  ExAcquireFastMutex(&xpdd->xb_watch_mutex);

  for (i = 0; i < MAX_WATCH_ENTRIES; i++)
    if (xpdd->XenBus_WatchEntries[i].Active == 0)
      break;
  
  if (i == MAX_WATCH_ENTRIES)
  {
    KdPrint((__DRIVER_NAME " +++ No more watch slots left\n"));
    ExReleaseFastMutex(&xpdd->xb_watch_mutex);
    return NULL;
  }

  /* must init watchentry before starting watch */
  
  w_entry = &xpdd->XenBus_WatchEntries[i];
  RtlStringCbCopyA(w_entry->Path, ARRAY_SIZE(w_entry->Path), Path);
  w_entry->ServiceRoutine = ServiceRoutine;
  w_entry->ServiceContext = ServiceContext;
  w_entry->Count = 0;
  w_entry->Active = 1;

  ExReleaseFastMutex(&xpdd->xb_watch_mutex);

  msg = XenBus_SendAddWatch(xpdd, xbt, Path, i);

  if (msg)
  {
    xpdd->XenBus_WatchEntries[i].Active = 0;
    return msg;
  }

  return NULL;
}

char *
XenBus_RemWatch(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *Path,
  PXENBUS_WATCH_CALLBACK ServiceRoutine,
  PVOID ServiceContext)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  char *msg;
  int i;

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  ExAcquireFastMutex(&xpdd->xb_watch_mutex);

  // check that Path < 128 chars

  for (i = 0; i < MAX_WATCH_ENTRIES; i++)
  {
    if (xpdd->XenBus_WatchEntries[i].Active
      && !strcmp(xpdd->XenBus_WatchEntries[i].Path, Path)
      && xpdd->XenBus_WatchEntries[i].ServiceRoutine == ServiceRoutine
      && xpdd->XenBus_WatchEntries[i].ServiceContext == ServiceContext)
    {
      KdPrint((__DRIVER_NAME "     Match\n"));
      break;
    }
  }

  if (i == MAX_WATCH_ENTRIES)
  {
    ExReleaseFastMutex(&xpdd->xb_watch_mutex);
    KdPrint((__DRIVER_NAME "     Watch not set for %s - can't remove\n", Path));
    return NULL;
  }

  xpdd->XenBus_WatchEntries[i].Active = 0;
  xpdd->XenBus_WatchEntries[i].Path[0] = 0;

  ExReleaseFastMutex(&xpdd->xb_watch_mutex);

  msg = XenBus_SendRemWatch(Context, xbt, Path, i);
  
  return msg;
}

char *
XenBus_StartTransaction(PVOID Context, xenbus_transaction_t *xbt)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  /* xenstored becomes angry if you send a length 0 message, so just
     shove a nul terminator on the end */
  struct write_req req = { "", 1};
  struct xsd_sockmsg *rep;
  char *err;

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  rep = xenbus_format_msg_reply(xpdd, XS_TRANSACTION_START, 0, &req, 1);
  err = errmsg(rep);
  if (err)
    return err;
  *xbt = atoi((char *)(rep + 1));
  ExFreePoolWithTag(rep, XENPCI_POOL_TAG);

  return NULL;
}

char *
XenBus_EndTransaction(
  PVOID Context,
  xenbus_transaction_t t,
  int abort,
  int *retry)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  struct xsd_sockmsg *rep;
  struct write_req req;
  char *err;

  *retry = 0;

  req.data = abort ? "F" : "T";
  req.len = 2;
  rep = xenbus_format_msg_reply(xpdd, XS_TRANSACTION_END, t, &req, 1);
  err = errmsg(rep);
  if (err) {
    if (!strcmp(err, "EAGAIN")) {
      *retry = 1;
      ExFreePoolWithTag(err, XENPCI_POOL_TAG);
      return NULL;
    } else {
      return err;
    }
  }
  ExFreePoolWithTag(rep, XENPCI_POOL_TAG);

  return NULL;
}

char *
XenBus_Printf(
  PVOID Context,
  xenbus_transaction_t xbt,
  char *path,
  char *fmt,
  ...)
{
  PXENPCI_DEVICE_DATA xpdd = Context;
  va_list ap;
  char buf[512];
  char *retval;

  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  va_start(ap, fmt);
  RtlStringCbVPrintfA(buf, ARRAY_SIZE(buf), fmt, ap);
  va_end(ap);
  retval = XenBus_Write(xpdd, xbt, path, buf);

  return retval;
}
