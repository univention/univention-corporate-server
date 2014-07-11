/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2012 James Harper

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
#include <aux_klib.h>

ULONG
XnGetVersion() {
  return 1;
}

VOID
XenPci_BackendStateCallback(char *path, PVOID context) {
  PXENPCI_PDO_DEVICE_DATA xppdd = context;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  PCHAR err;
  PCHAR value;
  ULONG backend_state;
  ULONG frontend_state;
  
  FUNCTION_ENTER();
  //RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
  FUNCTION_MSG("Read path=%s\n", path);
  err = XenBus_Read(xpdd, XBT_NIL, path, &value);
  if (err) {
    FUNCTION_MSG("Error %s\n", err);
    XenPci_FreeMem(err);
    /* this is pretty catastrophic... */
    /* maybe call the callback with an unknown or something... or just ignore? */
    FUNCTION_EXIT();
    return;
  }
  FUNCTION_MSG("Read value=%s\n", value);
  backend_state = atoi(value);
  XenPci_FreeMem(value);
  if (backend_state == XenbusStateClosing) {
    /* check to see if transition to closing was initiated by backend */
    CHAR frontend_state_path[128];
    FUNCTION_MSG("backend path is closing. checking frontend path\n");
    RtlStringCbCopyA(frontend_state_path, ARRAY_SIZE(frontend_state_path), xppdd->path);
    RtlStringCbCatA(frontend_state_path, ARRAY_SIZE(frontend_state_path), "/state");
    err = XenBus_Read(xpdd, XBT_NIL, frontend_state_path, &value);
    if (err) {
      FUNCTION_MSG("Error %s\n", err);
      XenPci_FreeMem(err);
      FUNCTION_EXIT();
      return;
    }
    FUNCTION_MSG("Read value=%s\n", value);
    frontend_state = atoi(value);
    XenPci_FreeMem(value);
    if (frontend_state == XenbusStateConnected) {
      FUNCTION_MSG("initiated by backend. Requesting eject\n");
      /* frontend is still connected. disconnection was initiated by backend */
      WdfPdoRequestEject(xppdd->wdf_device);
    }
  }
  xppdd->device_callback(xppdd->device_callback_context, XN_DEVICE_CALLBACK_BACKEND_STATE, (PVOID)(ULONG_PTR)backend_state);
  FUNCTION_EXIT();
}

XN_HANDLE
XnOpenDevice(PDEVICE_OBJECT pdo, PXN_DEVICE_CALLBACK callback, PVOID context) {
  WDFDEVICE device;
  PXENPCI_PDO_DEVICE_DATA xppdd;
  PXENPCI_DEVICE_DATA xpdd;
  PCHAR response;
  CHAR path[128];
  
  FUNCTION_ENTER();
  device = WdfWdmDeviceGetWdfDeviceHandle(pdo);
  if (!device) {
    FUNCTION_MSG("Failed to get WDFDEVICE for %p\n", pdo);
    return NULL;
  }
  xppdd = GetXppdd(device);
  xpdd = xppdd->xpdd;
  xppdd->device_callback = callback;
  xppdd->device_callback_context = context;
  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
  response = XenBus_AddWatch(xpdd, XBT_NIL, path, XenPci_BackendStateCallback, xppdd);
  if (response) {
    FUNCTION_MSG("XnAddWatch - %s = %s\n", path, response);
    XenPci_FreeMem(response);
    xppdd->device_callback = NULL;
    xppdd->device_callback_context = NULL;
    FUNCTION_EXIT();
    return NULL;
  }

  FUNCTION_EXIT();
  return xppdd;
}

VOID
XnCloseDevice(XN_HANDLE handle) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  PCHAR response;
  CHAR path[128];

  FUNCTION_ENTER();
  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
  response = XenBus_RemWatch(xpdd, XBT_NIL, path, XenPci_BackendStateCallback, xppdd);
  if (response) {
    FUNCTION_MSG("XnRemWatch - %s = %s\n", path, response);
    XenPci_FreeMem(response);
  }
  xppdd->device_callback = NULL;
  xppdd->device_callback_context = NULL;
  FUNCTION_EXIT();
  return;
}

NTSTATUS
XnBindEvent(XN_HANDLE handle, evtchn_port_t *port, PXN_EVENT_CALLBACK callback, PVOID context) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  *port = EvtChn_AllocUnbound(xpdd, xppdd->backend_id);
  return EvtChn_Bind(xpdd, *port, callback, context, EVT_ACTION_FLAGS_DEFAULT);
}

NTSTATUS
XnUnbindEvent(XN_HANDLE handle, evtchn_port_t port) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  EvtChn_Unbind(xpdd, port);
  EvtChn_Close(xpdd, port);
  return STATUS_SUCCESS;
}

grant_ref_t
XnGrantAccess(XN_HANDLE handle, uint32_t frame, int readonly, grant_ref_t ref, ULONG tag) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;  
  return GntTbl_GrantAccess(xpdd, xppdd->backend_id, frame, readonly, ref, tag);
}

BOOLEAN
XnEndAccess(XN_HANDLE handle, grant_ref_t ref, BOOLEAN keepref, ULONG tag) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  return GntTbl_EndAccess(xpdd, ref, keepref, tag);
}

grant_ref_t
XnAllocateGrant(XN_HANDLE handle, ULONG tag) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  return GntTbl_GetRef(xpdd, tag);
}

VOID
XnFreeGrant(XN_HANDLE handle, grant_ref_t ref, ULONG tag) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  GntTbl_PutRef(xpdd, ref, tag);
}

/* result must be freed with XnFreeMem() */
NTSTATUS
XnReadString(XN_HANDLE handle, ULONG base, PCHAR path, PCHAR *value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  PCHAR response;
  CHAR full_path[1024];
  
  switch(base) {
  case XN_BASE_FRONTEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->path);
    break;
  case XN_BASE_BACKEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->backend_path);
    break;
  case XN_BASE_GLOBAL:
    full_path[0] = 0;
  }
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), "/");
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), path);
  
  response = XenBus_Read(xpdd, XBT_NIL, full_path, value);
  if (response) {
    FUNCTION_MSG("Error reading %s - %s\n", full_path, response);
    XenPci_FreeMem(response);
    return STATUS_UNSUCCESSFUL;
  }
  return STATUS_SUCCESS;
}

NTSTATUS
XnWriteString(XN_HANDLE handle, ULONG base, PCHAR path, PCHAR value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  PCHAR response;
  CHAR full_path[1024];

  switch(base) {
  case XN_BASE_FRONTEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->path);
    break;
  case XN_BASE_BACKEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->backend_path);
    break;
  case XN_BASE_GLOBAL:
    full_path[0] = 0;
  }
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), "/");
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), path);

  //FUNCTION_MSG("XnWriteString(%s, %s)\n", full_path, value);
  response = XenBus_Write(xpdd, XBT_NIL, full_path, value);
  if (response) {
    FUNCTION_MSG("XnWriteString - %s = %s\n", full_path, response);
    XenPci_FreeMem(response);
    FUNCTION_EXIT();
    return STATUS_UNSUCCESSFUL;
  }
  return STATUS_SUCCESS;
}

NTSTATUS
XnReadInt32(XN_HANDLE handle, ULONG base, PCHAR path, ULONG *value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  CHAR full_path[1024];
  PCHAR response;
  PCHAR string_value;

  switch(base) {
  case XN_BASE_FRONTEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->path);
    break;
  case XN_BASE_BACKEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->backend_path);
    break;
  case XN_BASE_GLOBAL:
    full_path[0] = 0;
  }
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), "/");
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), path);

  response = XenBus_Read(xpdd, XBT_NIL, full_path, &string_value);
  if (response) {
    FUNCTION_MSG("XnReadInt - %s = %s\n", full_path, response);
    XenPci_FreeMem(response);
    FUNCTION_EXIT();
    return STATUS_UNSUCCESSFUL;
  }
  *value = atoi(string_value);
  return STATUS_SUCCESS;
}

NTSTATUS
XnWriteInt32(XN_HANDLE handle, ULONG base, PCHAR path, ULONG value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  CHAR full_path[1024];
  PCHAR response;
  
  switch(base) {
  case XN_BASE_FRONTEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->path);
    break;
  case XN_BASE_BACKEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->backend_path);
    break;
  case XN_BASE_GLOBAL:
    full_path[0] = 0;
  }
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), "/");
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), path);
  
  //FUNCTION_MSG("XnWriteInt32(%s, %d)\n", full_path, value);
  response = XenBus_Printf(xpdd, XBT_NIL, full_path, "%d", value);
  if (response) {
    FUNCTION_MSG("XnWriteInt - %s = %s\n", full_path, response);
    XenPci_FreeMem(response);
    FUNCTION_EXIT();
    return STATUS_UNSUCCESSFUL;
  }
  return STATUS_SUCCESS;
}

NTSTATUS
XnReadInt64(XN_HANDLE handle, ULONG base, PCHAR path, ULONGLONG *value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  CHAR full_path[1024];
  PCHAR response;
  PCHAR string_value;
  PCHAR ptr;

  switch(base) {
  case XN_BASE_FRONTEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->path);
    break;
  case XN_BASE_BACKEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->backend_path);
    break;
  case XN_BASE_GLOBAL:
    full_path[0] = 0;
  }
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), "/");
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), path);

  response = XenBus_Read(xpdd, XBT_NIL, full_path, &string_value);
  if (response) {
    FUNCTION_MSG("XnReadInt - %s = %s\n", full_path, response);
    XenPci_FreeMem(response);
    FUNCTION_EXIT();
    return STATUS_UNSUCCESSFUL;
  }
  *value = 0;
  for (ptr = string_value; *ptr && *ptr >= '0' && *ptr <= '9'; ptr++) {
    *value *= 10;
    *value += (*ptr) - '0';
  }
  return STATUS_SUCCESS;
}

NTSTATUS
XnWriteInt64(XN_HANDLE handle, ULONG base, PCHAR path, ULONGLONG value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  CHAR full_path[1024];
  PCHAR response;
  
  switch(base) {
  case XN_BASE_FRONTEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->path);
    break;
  case XN_BASE_BACKEND:
    RtlStringCbCopyA(full_path, ARRAY_SIZE(full_path), xppdd->backend_path);
    break;
  case XN_BASE_GLOBAL:
    full_path[0] = 0;
  }
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), "/");
  RtlStringCbCatA(full_path, ARRAY_SIZE(full_path), path);
  
  response = XenBus_Printf(xpdd, XBT_NIL, full_path, "%I64d", value);
  if (response) {
    FUNCTION_MSG("XnWriteInt - %s = %s\n", full_path, response);
    XenPci_FreeMem(response);
    FUNCTION_EXIT();
    return STATUS_UNSUCCESSFUL;
  }
  return STATUS_SUCCESS;
}

NTSTATUS
XnNotify(XN_HANDLE handle, evtchn_port_t port) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;  
  return EvtChn_Notify(xpdd, port);
}

/* called at PASSIVE_LEVEL */
VOID
XnGetValue(XN_HANDLE handle, ULONG value_type, PVOID value) {
  PXENPCI_PDO_DEVICE_DATA xppdd = handle;
  //PXENPCI_DEVICE_DATA xpdd = xppdd->xpdd;
  DECLARE_UNICODE_STRING_SIZE(my_device_name, 128);
  ULONG i;

  switch (value_type) {
  case XN_VALUE_TYPE_QEMU_HIDE_FLAGS:
    *(PULONG)value = (ULONG)qemu_hide_flags_value;
    break;
  case XN_VALUE_TYPE_QEMU_FILTER:
    *(PULONG)value = FALSE;
    RtlUnicodeStringPrintf(&my_device_name, L"#%S#", xppdd->device);
    for (i = 0; i < WdfCollectionGetCount(qemu_hide_devices); i++) {
      WDFSTRING wdf_string = WdfCollectionGetItem(qemu_hide_devices, i);
      UNICODE_STRING hide_device_name;
      WdfStringGetUnicodeString(wdf_string, &hide_device_name);
      if (RtlCompareUnicodeString(&hide_device_name, &my_device_name, TRUE) != 0) {
        *(PULONG)value = TRUE;
        break;
      }
    }
    break;
  default:
    FUNCTION_MSG("GetValue unknown type %d\n", value_type);
    break;
  }
}

//externPVOID hypercall_stubs = NULL;

PVOID
XnGetHypercallStubs() {
  return hypercall_stubs;
}

VOID
XnSetHypercallStubs(PVOID _hypercall_stubs) {
  hypercall_stubs = _hypercall_stubs;
}

NTSTATUS
XnDebugPrint(PCHAR format, ...) {
  NTSTATUS status;
  va_list args;
  
  va_start(args, format);
  status = XenPci_DebugPrintV(format, args);
  va_end(args);

  return status;
}

VOID
XnPrintDump() {
  KBUGCHECK_DATA bugcheck_data;
  
  bugcheck_data.BugCheckDataSize  = sizeof(bugcheck_data);
  AuxKlibGetBugCheckData(&bugcheck_data);
  if (bugcheck_data.BugCheckCode != 0) {
    /* use XnDebugPrint so this gets printed even not in debug mode */
    XnDebugPrint("Bug check 0x%08x (0x%p, 0x%p, 0x%p, 0x%p)\n", bugcheck_data.BugCheckCode, bugcheck_data.Parameter1, bugcheck_data.Parameter2, bugcheck_data.Parameter3, bugcheck_data.Parameter4);
  }
}

ULONG
XnTmemOp(struct tmem_op *tmem_op) {
  return HYPERVISOR_tmem_op(tmem_op);
}